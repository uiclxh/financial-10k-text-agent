.PHONY: install install-ml lint test smoke-run docker-build docker-smoke clean

install:
	python -m pip install --upgrade pip
	python -m pip install -e ".[dev]"

install-ml:
	python -m pip install -e ".[dev,ml]"

lint:
	python -m ruff check .

test:
	python -m pytest

smoke-run:
	python -m text_factor_lab run --config configs/text_factor_lab/e2e_smoke.yaml --execute

docker-build:
	docker build -t financial-10k-text-agent:local .

docker-smoke:
	docker run --rm financial-10k-text-agent:local

clean:
	python -c "import shutil; shutil.rmtree('runs/text_factor_lab/tflab_e2e_smoke_001', ignore_errors=True)"
