include tools.lock

PY := uv run python
OKF := reference-agent @ git+https://github.com/GoogleCloudPlatform/open-knowledge-format@$(OKF_COMMIT)

.PHONY: bootstrap test lint verify render clean

bootstrap:
	uv sync

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
