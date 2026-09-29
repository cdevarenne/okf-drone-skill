"""Check the shape and internal consistency of the SORA risk tables in knowledge/risk/.

These tests do not repeat the values. The owner checks the values against S2 and S4.
"""

from pathlib import Path

from okf_lib import load_bundle

BUNDLE = load_bundle(Path(__file__).resolve().parents[1] / "knowledge")
SAILS = ["I", "II", "III", "IV", "V", "VI"]
ARCS = ["a", "b", "c", "d"]
ROBUSTNESS = {"low", "medium", "high", "out-of-scope"}


def table(concept_id: str) -> dict:
    return BUNDLE.concepts[concept_id].table


def test_igrc_columns_grow() -> None:
    cols = table("risk/igrc")["columns"]
    assert len(cols) == 5
    for key in ("max_dimension_m", "max_speed_ms"):
        values = [c[key] for c in cols]
        assert values == sorted(set(values)), key


def test_igrc_rows_are_monotonic() -> None:
    rows = table("risk/igrc")["rows"]
    assert len({r["band"] for r in rows}) == len(rows) == 7
    for row in rows:
        assert len(row["igrc"]) == 5, row["band"]
        cells = [v for v in row["igrc"] if v is not None]
        assert cells == sorted(cells), row["band"]
    for col in range(5):
        cells = [r["igrc"][col] for r in rows if r["igrc"][col] is not None]
        assert cells == sorted(cells), col


def test_igrc_floor_names_a_band() -> None:
    igrc = table("risk/igrc")
    assert igrc["final_grc_floor"] in {r["band"] for r in igrc["rows"]}


def test_sail_rows_are_monotonic() -> None:
    sail = table("risk/sail")
    assert sail["arc_columns"] == ARCS
    grcs = [r["final_grc_max"] for r in sail["rows"]]
    assert grcs == sorted(set(grcs))
    rank = [[SAILS.index(s) for s in r["sail"]] for r in sail["rows"]]
    for row in rank:
        assert row == sorted(row)
    for col in range(len(ARCS)):
        assert [r[col] for r in rank] == sorted(r[col] for r in rank)


def test_arc_rules_end_with_a_default() -> None:
    arc = table("risk/arc")
    rules = arc["initial_arc"]
    assert all(r["arc"] in ARCS for r in rules)
    assert rules[-1]["when"] == {}
    assert all(r["when"] for r in rules[:-1])
    assert set(arc["tmpr"]) == set(ARCS)
    assert arc["residual_arc"]["lowest_by_vlos"] in ARCS


def test_containment_tables_cover_every_sail_once() -> None:
    tables = table("risk/containment")["tables"]
    assert [t["id"] for t in tables] == ["8", "9", "10", "11", "12", "13"]
    for t in tables:
        sails = [s for row in t["rows"] for s in row["sail"]]
        assert sails == SAILS, t["id"]
        for row in t["rows"]:
            assert len(row["robustness"]) == len(t["columns"]), t["id"]
            assert set(row["robustness"]) <= ROBUSTNESS, t["id"]
