include tools.lock

SCRIPTS := .claude/skills/drone-mission-compliance/scripts

PY := uv run python
OKF := reference-agent @ git+https://github.com/GoogleCloudPlatform/open-knowledge-format@$(OKF_COMMIT)
PX4_DIR := .tools/px4
PX4_BUILD := $(PX4_DIR)/build/px4_sitl_default

.PHONY: bootstrap plan seeded examples px4 sitl test lint verify render clean

bootstrap:
	uv sync

plan:
	$(PY) $(SCRIPTS)/gen_plan.py --mission $(MISSION) --knowledge knowledge --lock tools.lock --out out
	$(PY) $(SCRIPTS)/validate_plan.py --mission $(MISSION) --knowledge knowledge --out out
	$(PY) $(SCRIPTS)/score_risk.py --mission $(MISSION) --knowledge knowledge --out out
	$(PY) $(SCRIPTS)/render_report.py --mission $(MISSION) --knowledge knowledge --lock tools.lock --out out

seeded:
	$(PY) $(SCRIPTS)/seeded.py --seeded missions/SEEDED.yaml --knowledge knowledge --lock tools.lock --out out --data docs/data/seeded.json

examples:
	rm -rf examples
	$(PY) $(SCRIPTS)/seeded.py --seeded missions/SEEDED.yaml --knowledge knowledge --lock tools.lock --out examples --data docs/data/seeded.json

px4:
	test -d $(PX4_DIR) || git clone --depth 1 --branch $(PX4_VERSION) --recurse-submodules --shallow-submodules https://github.com/PX4/PX4-Autopilot $(PX4_DIR)
	uv venv --allow-existing --python 3.12 .tools/px4-venv  # PX4 build tools; 3.12 as in the prototype
	VIRTUAL_ENV=.tools/px4-venv uv pip install -r $(PX4_DIR)/Tools/setup/requirements.txt
	PATH="$(CURDIR)/.tools/px4-venv/bin:$$PATH" $(MAKE) -C $(PX4_DIR) px4_sitl_default

sitl:
	uv run --extra sitl python $(SCRIPTS)/sitl_fly.py --mission $(MISSION) --knowledge knowledge --lock tools.lock --out out --px4-build $(PX4_BUILD)

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
