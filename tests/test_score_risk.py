"""Check score_risk: the hazard matrix, each SORA step against its table, the gaps, and the CLI."""

import copy
import json
from pathlib import Path

from bundle_helpers import BUNDLE, unverified
from mission import load_mission
from score_risk import hazard_matrix, main, score

ROOT = Path(__file__).resolve().parents[1]
MISSIONS = ROOT / "tests" / "fixtures" / "missions"


def specific(**changes) -> dict:
    mission = copy.deepcopy(load_mission(MISSIONS / "specific.yaml"))
    for path, value in changes.items():
        *parents, key = path.split("__")
        node = mission
        for p in parents:
            node = node[p]
        node[key] = value
    return mission


def sora(mission: dict, bundle=BUNDLE) -> tuple[dict, dict]:
    doc = score(mission, bundle)
    return doc["sora"], {c["check_id"]: c for c in doc["checks"]}


def value(summary: dict, key: str):
    return summary[key]["value"]


def test_hazard_matrix_rows() -> None:
    rows, gaps = hazard_matrix(BUNDLE)
    assert gaps == []
    assert {r["hazard_id"] for r in rows} == {c.id for c in BUNDLE.of_type("Hazard")}
    for r in rows:
        assert r["score"] == r["likelihood"] * r["severity"]
        assert r["mitigations"] and not any("](" in m for m in r["mitigations"])


def test_hazard_matrix_skips_unverified_hazards() -> None:
    rows, _ = hazard_matrix(unverified("hazards/loss-of-c2"))
    assert "hazards/loss-of-c2" not in {r["hazard_id"] for r in rows}


def test_open_category_is_not_scored() -> None:
    summary, checks = sora(load_mission(MISSIONS / "survey.yaml"))
    assert summary == {"status": "not_applicable"}
    assert list(checks) == ["sora.applicable"]
    assert checks["sora.applicable"]["concept_id"] == "regulations/easa-specific-sora"


def test_specific_fixture_summary() -> None:
    summary, checks = sora(specific())
    assert [value(summary, k) for k in ("igrc", "final_grc", "initial_arc", "residual_arc")] == [
        4,
        3,
        "b",
        "b",
    ]
    assert [value(summary, k) for k in ("tmpr", "sail", "containment")] == ["low", "II", "low"]
    assert summary["mitigations_applied"] == [
        {"concept_id": "risk/m1a", "level": "low", "credit": -1}
    ]
    assert checks["sora.oso"] == {
        "check_id": "sora.oso",
        "status": "gap",
        "concept_id": None,
        "evidence": "",
        "message": "no verified concept in the bundle governs sora.oso",
    }
    assert {c["status"] for k, c in checks.items() if k != "sora.oso"} == {"pass"}


def test_small_ua_rule() -> None:
    summary, _ = sora(specific(ua__mtom_kg=0.2, ua__max_speed_ms=20))
    assert value(summary, "igrc") == 1


def test_unknown_band_is_a_gap() -> None:
    _, checks = sora(specific(ground__population_density="crowded"))
    assert (checks["sora.igrc"]["status"], checks["sora.igrc"]["concept_id"]) == (
        "gap",
        "risk/igrc",
    )
    assert checks["sora.final_grc"]["status"] == "gap"


def test_ua_outside_the_table_fails() -> None:
    _, checks = sora(specific(ua__char_dimension_m=50))
    assert checks["sora.igrc"]["status"] == "fail"


def test_m1_floor() -> None:
    summary, _ = sora(specific(sora__mitigations={"m1a": "medium", "m1b": "high"}))
    assert value(summary, "final_grc") == 1


def test_mitigation_level_without_credit_fails() -> None:
    _, checks = sora(specific(sora__mitigations={"m1b": "low"}))
    assert checks["sora.final_grc"]["status"] == "fail"


def test_unknown_mitigation_is_a_gap() -> None:
    _, checks = sora(specific(sora__mitigations={"m3": "low"}))
    assert (checks["sora.final_grc"]["status"], checks["sora.final_grc"]["concept_id"]) == (
        "gap",
        "risk/igrc",
    )


def test_vlos_reduces_the_arc() -> None:
    summary, _ = sora(specific(operation="VLOS", airspace__over_urban_area=True))
    assert value(summary, "initial_arc") == "c"
    assert value(summary, "residual_arc") == "b"
    assert value(summary, "tmpr") == "none (VLOS)"


def test_missing_airspace_fact_is_a_gap_downstream_too() -> None:
    mission = specific()
    del mission["airspace"]["atypical_airspace"]
    summary, checks = sora(mission)
    assert (checks["sora.initial_arc"]["status"], checks["sora.initial_arc"]["concept_id"]) == (
        "gap",
        "risk/arc",
    )
    for key in ("residual_arc", "sail", "containment"):
        assert value(summary, key) == "not_assessed"
        assert checks[f"sora.{key}"]["status"] == "gap"


def test_final_grc_above_the_table_fails() -> None:
    mission = specific(
        ua__char_dimension_m=5,
        ua__max_speed_ms=60,
        ground__population_density="high-density-metropolitan",
        sora__mitigations={},
    )
    summary, checks = sora(mission)
    assert value(summary, "final_grc") == 8
    assert checks["sora.sail"]["status"] == "fail"


def test_containment_needs_the_adjacent_area() -> None:
    mission = specific()
    del mission["sora"]["adjacent_area"]
    _, checks = sora(mission)
    assert (checks["sora.containment"]["status"], checks["sora.containment"]["concept_id"]) == (
        "gap",
        "risk/containment",
    )


def test_containment_out_of_scope_fails() -> None:
    adjacent = {"below_people_km2": None, "assemblies": "over-400k", "shelter": True}
    mission = specific(ua__char_dimension_m=2, ua__max_speed_ms=30, sora__adjacent_area=adjacent)
    _, checks = sora(mission)
    assert checks["sora.containment"]["status"] == "fail"


def test_cli_writes_risk_json(tmp_path: Path) -> None:
    args = ["--mission", str(MISSIONS / "specific.yaml"), "--knowledge", str(ROOT / "knowledge")]
    assert main([*args, "--out", str(tmp_path)]) == 0
    doc = json.loads((tmp_path / "specific" / "risk.json").read_text())
    assert doc == score(load_mission(MISSIONS / "specific.yaml"), BUNDLE)
