"""Check the LLM eval offline: the intake score, the labels and a full run on recorded answers."""

import json
from pathlib import Path

import intake
import pytest
from eval_llm import label_for, main, score_intake
from mission import load_mission

ROOT = Path(__file__).resolve().parents[1]
LABEL = load_mission(ROOT / "missions" / "m01-survey-open.yaml")


def test_labels_follow_the_text_names() -> None:
    missions = ROOT / "missions"
    assert label_for(Path("m03.txt"), missions).name == "m03-outside-geofence.yaml"
    assert label_for(Path("x01-injection.txt"), missions).name == "m01-survey-open.yaml"
    assert label_for(Path("x02-no-failsafes.txt"), missions).name == "m01-survey-open.yaml"


def test_score_counts_correct_wrong_and_missing() -> None:
    accepted = [
        {"path": "speed_ms", "value": 8, "quote": "8 m/s"},
        {"path": "max_altitude_agl_m", "value": 120, "quote": "120 m"},
        {"path": "failsafes.lost_link", "value": "RTL", "quote": "return to launch"},
    ]
    score = score_intake(accepted, LABEL)
    assert score["correct"] == 2 and score["wrong"] == ["max_altitude_agl_m"]
    assert "home.lat" in score["missing"] and "speed_ms" not in score["missing"]
    assert "id" not in score["missing"]
    assert score["failsafes_filled"] == ["failsafes.lost_link"]


def test_lists_and_numbers_compare_as_values() -> None:
    accepted = [{"path": "home.lat", "value": 44.799, "quote": "44.7990"}]
    assert score_intake(accepted, LABEL)["correct"] == 1


def _record(fixtures: Path, request, output: dict, model: str = "claude-opus-5-5") -> None:
    usage = {"input_tokens": 1000, "output_tokens": 500}
    doc = {"task": request.task, "model": model, "output": output, "usage": usage}
    fixtures.mkdir(parents=True, exist_ok=True)
    (fixtures / f"{request.key(model)}.json").write_text(json.dumps(doc))


@pytest.fixture
def small_set(tmp_path: Path, monkeypatch) -> list[str]:
    """One text (m01) and one seeded mission (m01), with recorded answers."""
    monkeypatch.delenv("LLM_MODE", raising=False)
    monkeypatch.delenv("LLM_EVAL_MODELS", raising=False)
    texts, fixtures = tmp_path / "text", tmp_path / "fx"
    texts.mkdir()
    text = "The drone flies at 8 m/s. On lost link it does a return to launch."
    (texts / "m01.txt").write_text(text)
    fields = [
        {"path": "speed_ms", "value": 8, "quote": "8 m/s"},
        {"path": "failsafes.lost_link", "value": "RTL", "quote": "return to launch"},
    ]
    _record(fixtures, intake.request(text), {"fields": fields})
    seeded = tmp_path / "SEEDED.yaml"
    seeded.write_text("- mission: m01-survey-open\n  expected: GO\n")
    return [
        "--texts", str(texts), "--seeded", str(seeded), "--missions", str(ROOT / "missions"),
        "--knowledge", str(ROOT / "knowledge"), "--lock", str(ROOT / "tools.lock"),
        "--fixtures", str(fixtures), "--data", str(tmp_path / "eval.json"),
    ]  # fmt: skip


def test_full_run_on_recorded_answers(small_set: list[str], tmp_path: Path) -> None:
    assert main(small_set) == 0
    result = json.loads((tmp_path / "eval.json").read_text())["models"]["claude-opus-5-5"]
    assert result["intake"]["m01"]["correct"] == 2 and result["intake"]["m01"]["wrong"] == []
    assert result["narrate"]["m01-survey-open"] == {"skipped": "no fail and no gap"}
    # One answer (intake; m01 is GO, so no narrate call): 1000 tokens in (4 USD/M), 500 out (20 USD/M).
    assert result["cost_usd"] == pytest.approx(0.014)


def test_missing_answer_names_the_text(small_set: list[str], tmp_path: Path, capsys) -> None:
    (tmp_path / "text" / "m02.txt").write_text("Another mission.")
    assert main(small_set) == 2
    assert "m02.txt" in capsys.readouterr().err
    assert not (tmp_path / "eval.json").exists()


def test_no_texts_exits_2_with_a_message(small_set: list[str], tmp_path: Path, capsys) -> None:
    (tmp_path / "text" / "m01.txt").unlink()
    assert main(small_set) == 2
    err = capsys.readouterr().err
    assert "no .txt" in err
