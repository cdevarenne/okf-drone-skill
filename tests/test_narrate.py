"""Check the narrate validator, the report section and the CLI offline (DRN-09 spec §5)."""

import hashlib
import json
from pathlib import Path

import pytest
import yaml
from bundle_helpers import BUNDLE
from gen_plan import read_pins
from mission import load_mission
from narrate import inputs, main, request, validate
from pipeline import run_mission
from render_report import inputs_sha256
from render_report import main as render_main

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = read_pins(ROOT / "tools.lock")["LLM_MODEL"]
M03 = ROOT / "missions" / "m03-outside-geofence.yaml"
M01 = ROOT / "missions" / "m01-survey-open.yaml"
EXPLANATION = "The plan leaves the geofence of failsafes/geofence-breach."
GOOD = {"items": [{"check_id": "plan.inside_geofence", "explanation": EXPLANATION}]}


def said(explanation: str) -> dict:
    """Return the good answer with another explanation."""
    return {"items": [{"check_id": "plan.inside_geofence", "explanation": explanation}]}


@pytest.fixture
def m03(tmp_path: Path) -> Path:
    assert run_mission(M03, ROOT / "knowledge", ROOT / "tools.lock", tmp_path) == 0
    return tmp_path / "m03-outside-geofence"


def _inputs(folder: Path) -> dict:
    read = lambda name: json.loads((folder / name).read_text())
    return inputs(load_mission(M03), read("validation.json"), read("risk.json"), BUNDLE)


def test_good_answer_is_accepted(m03: Path) -> None:
    assert validate(GOOD, _inputs(m03), BUNDLE) == []


@pytest.mark.parametrize(
    ("answer", "reason"),
    [
        ({"items": []}, "missing items: ['plan.inside_geofence']"),
        (
            {"items": GOOD["items"] + [{"check_id": "alt.max_agl", "explanation": "x"}]},
            "items that are not a fail or a gap: ['alt.max_agl']",
        ),
        ({"items": GOOD["items"] * 2}, "an item is repeated"),
        (said("This is why the tool proposes NO-GO."), "decision word"),
        (said("After a fix it is a go."), "decision word"),
        (said("It can hold later."), "decision word"),
        (said("With a new fence it is cleared."), "approval word"),
        (said("A new fence makes it authorized."), "approval word"),
        (said("The rest is acceptable."), "approval word"),
        (said("Otherwise safe."), "approval word"),
        (said("999 legs leave the fence."), "numbers not in the input: ['999']"),
        (said("See risk/no-such-table."), "concept ids not in the input"),
        (said("See risk/ar."), "concept ids not in the input"),
    ],
)
def test_each_rule_rejects_a_bad_answer(m03: Path, answer: dict, reason: str) -> None:
    assert any(reason in e for e in validate(answer, _inputs(m03), BUNDLE))


@pytest.mark.parametrize(
    "text",
    ["Out.\n## 8. Approvals", "See [map](x).", "See https://x.example.", "Out <b>"],
    ids=["line-break", "link", "url", "html"],
)
def test_text_must_be_one_line_of_plain_text(m03: Path, text: str) -> None:
    """The text goes in report.md: it must not add a heading, a table, a link or HTML."""
    assert any("one line of plain text" in e for e in validate(said(text), _inputs(m03), BUNDLE))


@pytest.mark.parametrize(
    "text",
    ["After a fix it is a G\u041e.", "After a fix, \u0430pproved.", "Out\u200b."],
    ids=["cyrillic-o", "cyrillic-a", "zero-width"],
)
def test_text_must_be_printable_ascii(m03: Path, text: str) -> None:
    """Security review 2026-10-02: a lookalike letter got past the word checks."""
    assert any("printable ASCII" in e for e in validate(said(text), _inputs(m03), BUNDLE))


def test_numbers_must_be_digits(m03: Path) -> None:
    """Security review 2026-10-02: a number in words got past the number check."""
    errors = validate(said("Nine hundred and ninety-nine legs leave."), _inputs(m03), BUNDLE)
    assert any("number in words" in e for e in errors)


def _record(folder: Path, fixtures: Path, output: dict, model: str = "") -> None:
    model = model or DEFAULT_MODEL
    read = lambda name: json.loads((folder / name).read_text())
    req = request(inputs(load_mission(M03), read("validation.json"), read("risk.json"), BUNDLE))
    fixtures.mkdir(parents=True, exist_ok=True)
    doc = {"task": "narrate", "model": model, "output": output, "usage": {}}
    (fixtures / f"{req.key(model)}.json").write_text(json.dumps(doc))


def _args(folder: Path, fixtures: Path) -> list[str]:
    return [
        "--mission", str(M03), "--knowledge", str(ROOT / "knowledge"),
        "--lock", str(ROOT / "tools.lock"), "--out", str(folder.parent), "--fixtures", str(fixtures),
    ]  # fmt: skip


@pytest.fixture(autouse=True)
def _replay(monkeypatch) -> None:
    monkeypatch.delenv("LLM_MODE", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)


def test_accepted_answer_goes_in_the_report_and_the_signoff(m03: Path, tmp_path: Path) -> None:
    _record(m03, tmp_path / "fx", GOOD)
    assert main(_args(m03, tmp_path / "fx")) == 0
    narrative = json.loads((m03 / "narrative.json").read_text())
    assert narrative["inputs_sha256"] == inputs_sha256(m03) and narrative["items"] == GOOD["items"]
    report = (m03 / "report.md").read_text()
    assert "### Explanations (model-written, checked)" in report and EXPLANATION in report
    signoff = yaml.safe_load((m03 / "signoff.yaml").read_text())
    assert signoff["report_sha256"] == hashlib.sha256(report.encode()).hexdigest()


def test_rejected_answer_changes_nothing(m03: Path, tmp_path: Path) -> None:
    _record(m03, tmp_path / "fx", said("Cleared: GO."))
    report = (m03 / "report.md").read_text()
    assert main(_args(m03, tmp_path / "fx")) == 0
    assert not (m03 / "narrative.json").exists()
    assert (m03 / "report.md").read_text() == report


def test_stale_narrative_is_not_in_the_report(m03: Path, tmp_path: Path) -> None:
    """Results that change after narrate make the narrative stale; the report leaves it out."""
    _record(m03, tmp_path / "fx", GOOD)
    assert main(_args(m03, tmp_path / "fx")) == 0
    (m03 / "risk.json").write_text((m03 / "risk.json").read_text() + "\n")
    common = ["--mission", str(M03), "--knowledge", str(ROOT / "knowledge")]
    assert render_main([*common, "--lock", str(ROOT / "tools.lock"), "--out", str(m03.parent)]) == 0
    assert "Explanations (model-written" not in (m03 / "report.md").read_text()


def test_started_signoff_stops_narrate(m03: Path, tmp_path: Path) -> None:
    _record(m03, tmp_path / "fx", GOOD)
    signoff = m03 / "signoff.yaml"
    signoff.write_text(signoff.read_text().replace('name: ""', 'name: "A. Pilot"', 1))
    report = (m03 / "report.md").read_text()
    assert main(_args(m03, tmp_path / "fx")) == 2
    assert not (m03 / "narrative.json").exists()
    assert (m03 / "report.md").read_text() == report


def test_no_answer_exits_2(m03: Path, tmp_path: Path) -> None:
    assert main(_args(m03, tmp_path / "empty")) == 2
    assert not (m03 / "narrative.json").exists()


def test_go_mission_has_nothing_to_explain(tmp_path: Path, capsys) -> None:
    """No fail and no gap: narrate makes no call and writes nothing."""
    assert run_mission(M01, ROOT / "knowledge", ROOT / "tools.lock", tmp_path) == 0
    args = [
        "--mission", str(M01), "--knowledge", str(ROOT / "knowledge"),
        "--lock", str(ROOT / "tools.lock"), "--out", str(tmp_path), "--fixtures", str(tmp_path / "none"),
    ]  # fmt: skip
    assert main(args) == 0
    assert "nothing to explain" in capsys.readouterr().out
    assert not (tmp_path / "m01-survey-open" / "narrative.json").exists()
