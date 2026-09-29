"""Check that examples/ holds the current generated output of the seeded missions.

`make examples` writes examples/; nobody edits it by hand.
"""

from pathlib import Path

import pytest
import yaml
from seeded import run_all

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
MISSIONS = [e["mission"] for e in yaml.safe_load((ROOT / "missions" / "SEEDED.yaml").read_text())]
FILES = ["mission.plan", "validation.json", "risk.json", "report.md", "signoff.yaml"]


@pytest.fixture(scope="module")
def fresh(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("examples")
    run_all(ROOT / "missions" / "SEEDED.yaml", ROOT / "knowledge", ROOT / "tools.lock", out)
    return out


def test_examples_hold_every_seeded_mission() -> None:
    assert sorted(p.name for p in EXAMPLES.iterdir() if p.is_dir()) == sorted(MISSIONS)


@pytest.mark.parametrize("mission", MISSIONS)
def test_example_files_are_current(fresh: Path, mission: str) -> None:
    assert sorted(p.name for p in (EXAMPLES / mission).iterdir()) == sorted(FILES)
    for name in FILES:
        assert (EXAMPLES / mission / name).read_text() == (fresh / mission / name).read_text(), name
