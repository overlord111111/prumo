.PHONY: install check lint test dados docs demo wheel clean

install:
	python -m pip install -e ".[dev]"

lint:
	ruff check src tests

test:
	pytest -q

dados:
	prumo dados

docs:
	prumo docs

check: lint dados test
	prumo docs --check

demo:
	python examples/fluxo-completo-linux.py

wheel:
	python -m build --wheel

clean:
	rm -rf build dist .pytest_cache .ruff_cache **/__pycache__
