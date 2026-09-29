"""Load an OKF v0.2 bundle into an in-memory concept graph.

Adapted from okf-grc-skill. This version adds two extension keys: `checks` (the check ids a
concept governs) and `table` (the structured values of a concept). Code reads regulatory values
only from `table`.
"""

from __future__ import annotations

import posixpath
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

RESERVED = frozenset({"index.md", "log.md"})
_FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n?(.*)\Z", re.DOTALL)
_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
_H1 = re.compile(r"^# (.+?)\s*$", re.MULTILINE)
_CHECK_ID = re.compile(r"[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+")


class BundleError(ValueError):
    """A bundle file violates OKF v0.2 conformance or a convention of this repo."""


@dataclass(frozen=True)
class Concept:
    """One OKF concept document."""

    id: str
    path: str
    type: str
    title: str
    description: str
    tags: tuple[str, ...]
    checks: tuple[str, ...]
    table: Mapping[str, Any]
    frontmatter: Mapping[str, Any]
    body: str
    links: tuple[str, ...]


@dataclass(frozen=True)
class Bundle:
    """All concepts in a bundle, keyed by concept id."""

    concepts: Mapping[str, Concept]

    def of_type(self, *types: str) -> list[Concept]:
        """Return the concepts of the given types, sorted by id."""
        return sorted((c for c in self.concepts.values() if c.type in types), key=lambda c: c.id)

    def governing(self, check_id: str) -> Concept | None:
        """Return the one concept that declares `check_id` in `checks`, or None (a coverage gap)."""
        return next((c for c in self.concepts.values() if check_id in c.checks), None)

    def section(self, concept: Concept, heading: str) -> str | None:
        """Return the body text under `# heading`, up to the next level-1 heading."""
        matches = list(_H1.finditer(concept.body))
        for i, m in enumerate(matches):
            if m.group(1) == heading:
                end = matches[i + 1].start() if i + 1 < len(matches) else len(concept.body)
                return concept.body[m.end() : end].strip()
        return None


def _resolve_link(target: str, concept_path: str) -> str | None:
    """Return the concept id that a markdown link points to, or None for a non-concept link."""
    target = target.split("#", 1)[0]
    if "://" in target or target.startswith("mailto:") or not target.endswith(".md"):
        return None
    if target.startswith("/"):
        resolved = posixpath.normpath(target.lstrip("/"))
    else:
        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(concept_path), target))
    if resolved.startswith("..") or posixpath.basename(resolved) in RESERVED:
        return None
    return resolved.removesuffix(".md")


def _string_list(rel_path: str, fm: Mapping[str, Any], key: str) -> tuple[str, ...]:
    value = fm.get(key, [])
    if not isinstance(value, list):
        raise BundleError(f"{rel_path}: '{key}' must be a YAML list")
    return tuple(str(v) for v in value)


def _parse(rel_path: str, text: str) -> Concept:
    m = _FRONTMATTER.match(text)
    if not m:
        raise BundleError(f"{rel_path}: missing YAML frontmatter")
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        raise BundleError(f"{rel_path}: unparseable frontmatter: {e}") from e
    if not isinstance(fm, dict) or not str(fm.get("type") or "").strip():
        raise BundleError(f"{rel_path}: frontmatter has no non-empty 'type'")
    checks = _string_list(rel_path, fm, "checks")
    for check in checks:
        if not _CHECK_ID.fullmatch(check):
            raise BundleError(f"{rel_path}: check id {check!r} is not '<group>.<name>'")
    table = fm.get("table", {})
    if not isinstance(table, dict):
        raise BundleError(f"{rel_path}: 'table' must be a YAML mapping")
    body = m.group(2)
    stem = rel_path.removesuffix(".md")
    return Concept(
        id=stem,
        path=rel_path,
        type=str(fm["type"]).strip(),
        title=str(fm.get("title") or posixpath.basename(stem)),
        description=str(fm.get("description") or ""),
        tags=_string_list(rel_path, fm, "tags"),
        checks=checks,
        table=table,
        frontmatter=fm,
        body=body,
        links=tuple(
            dict.fromkeys(
                link
                for t in _LINK.findall(body)
                if (link := _resolve_link(t, rel_path)) is not None
            )
        ),
    )


def load_bundle(root: Path) -> Bundle:
    """Parse every non-reserved .md under `root` into a Bundle.

    Raise BundleError if a file does not conform, or if two concepts declare the same check id.
    """
    concepts: dict[str, Concept] = {}
    owner: dict[str, str] = {}
    for path in sorted(root.rglob("*.md")):
        if path.name in RESERVED:
            continue
        rel = path.relative_to(root).as_posix()
        concept = _parse(rel, path.read_text(encoding="utf-8"))
        for check in concept.checks:
            if check in owner:
                raise BundleError(
                    f"{rel}: check id {check!r} is already declared by {owner[check]}"
                )
            owner[check] = concept.id
        concepts[concept.id] = concept
    return Bundle(concepts=concepts)
