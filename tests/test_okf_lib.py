"""Check the bundle loader against a fixture bundle and against broken files."""

from pathlib import Path

import pytest
from okf_lib import BundleError, load_bundle

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "bundle"


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_loads_concepts_and_skips_reserved_files() -> None:
    assert set(load_bundle(FIXTURE).concepts) == {"risk/sail", "failsafes/lost-link"}


def test_concept_fields() -> None:
    sail = load_bundle(FIXTURE).concepts["risk/sail"]
    assert sail.type == "Risk Table"
    assert sail.path == "risk/sail.md"
    assert sail.tags == ("fixture",)
    assert sail.checks == ("sora.sail",)
    assert sail.table == {"rows": {"2": {"a": "I"}}}


def test_links_resolve_and_keep_broken_links() -> None:
    bundle = load_bundle(FIXTURE)
    assert bundle.concepts["risk/sail"].links == ("failsafes/lost-link", "risk/missing")
    assert bundle.concepts["failsafes/lost-link"].links == ()


def test_governing_concept_or_gap() -> None:
    bundle = load_bundle(FIXTURE)
    assert bundle.governing("failsafe.lost_link").id == "failsafes/lost-link"
    assert bundle.governing("alt.max_agl") is None


def test_of_type_and_section() -> None:
    bundle = load_bundle(FIXTURE)
    assert [c.id for c in bundle.of_type("Failsafe", "Risk Table")] == [
        "failsafes/lost-link",
        "risk/sail",
    ]
    sail = bundle.concepts["risk/sail"]
    assert bundle.section(sail, "Source") == "Fixture."
    assert bundle.section(sail, "Nope") is None


def test_table_defaults_to_empty() -> None:
    assert load_bundle(FIXTURE).concepts["failsafes/lost-link"].table == {}


@pytest.mark.parametrize(
    ("rel", "text", "match"),
    [
        ("a.md", "just markdown\n", "missing YAML frontmatter"),
        ("a.md", "---\ntitle: no type\n---\n", "no non-empty 'type'"),
        ("a.md", "---\ntype: X\ntags: one\n---\n", "'tags' must be a YAML list"),
        ("a.md", "---\ntype: X\nchecks: [Alt]\n---\n", "is not '<group>.<name>'"),
        ("a.md", "---\ntype: X\ntable: [1, 2]\n---\n", "'table' must be a YAML mapping"),
        ("a.md", "---\ntype: X\ntitle: [unclosed\n---\n", "unparseable frontmatter"),
    ],
)
def test_broken_file_is_rejected(tmp_path: Path, rel: str, text: str, match: str) -> None:
    _write(tmp_path, rel, text)
    with pytest.raises(BundleError, match=match):
        load_bundle(tmp_path)


def test_duplicate_check_id_is_rejected(tmp_path: Path) -> None:
    _write(tmp_path, "a.md", "---\ntype: X\nchecks: [alt.max_agl]\n---\n")
    _write(tmp_path, "b.md", "---\ntype: Y\nchecks: [alt.max_agl]\n---\n")
    with pytest.raises(BundleError, match="already declared by a"):
        load_bundle(tmp_path)
