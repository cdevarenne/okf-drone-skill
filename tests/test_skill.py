"""Check the skill manifest: its frontmatter, and that each make target it names exists."""

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / ".claude" / "skills" / "drone-mission-compliance"


def _text() -> str:
    return (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")


def test_frontmatter_names_the_skill() -> None:
    _, front, _ = _text().split("---", 2)
    meta = yaml.safe_load(front)
    assert meta["name"] == SKILL_DIR.name
    assert meta["description"].strip()


def test_each_make_target_exists() -> None:
    targets = set(re.findall(r"^([a-z][a-z0-9-]*):", (ROOT / "Makefile").read_text(), re.MULTILINE))
    named = set(re.findall(r"`make ([a-z][a-z0-9-]*)", _text()))
    assert named and named <= targets
