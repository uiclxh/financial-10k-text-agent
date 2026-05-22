FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m pip install --upgrade pip \
    && python -m pip install -e ".[dev]"

COPY configs ./configs
COPY data ./data
COPY docs ./docs
COPY examples ./examples
COPY tests ./tests
COPY FINANCIAL_TEXT_FACTOR_LAB_GLOBAL_WORKFLOW.md CHANGELOG.md requirements.lock ./

CMD ["python", "-m", "text_factor_lab", "run", "--config", "configs/text_factor_lab/e2e_smoke.yaml", "--execute"]
