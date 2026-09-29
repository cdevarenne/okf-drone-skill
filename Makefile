include tools.lock

SCRIPTS := .claude/skills/drone-mission-compliance/scripts

PY := uv run python
OKF := reference-agent @ git+https://github.com/GoogleCloudPlatform/open-knowledge-format@$(OKF_COMMIT)

.PHONY: bootstrap plan test lint verify render clean

bootstrap:
	uv sync

plan:
	$(PY) $(SCRIPTS)/gen_plan.py --mission $(MISSION) --knowledge knowledge --lock tools.lock --out out
	$(PY) $(SCRIPTS)/validate_plan.py --mission $(MISSION) --knowledge knowledge --out out
	$(PY) $(SCRIPTS)/score_risk.py --mission $(MISSION) --knowledge knowledge --out out
	$(PY) $(SCRIPTS)/render_report.py --mission $(MISSION) --knowledge knowledge --lock tools.lock --out out

test:
	uv run pytest -q

lint:
	uv run ruff check .

verify: lint test

render:
	mkdir -p out
	uvx --python 3.14 --from "$(OKF)" reference-agent visualize --bundle knowledge --out out/knowledge-viz.html

clean:
	rm -rf out .pytest_cache .ruff_cache
