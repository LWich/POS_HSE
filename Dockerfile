FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && mkdir -p /data \
    && chown 10001:10001 /data

FROM base AS runtime
ENV POS_API_HOST=0.0.0.0
COPY pos ./pos
USER 10001:10001
EXPOSE 8000
CMD ["python", "-m", "pos.adapters.api"]

FROM base AS test-deps
COPY requirements-test.txt .
RUN pip install --no-cache-dir -r requirements-test.txt

FROM test-deps AS test
COPY pos ./pos
COPY tests ./tests
USER 10001:10001
CMD ["python", "-m", "unittest", "discover", "-s", "tests", "-v"]

FROM test-deps AS quality
COPY pyproject.toml .
RUN pip install --disable-pip-version-check --no-cache-dir pip==26.3 \
    && pip install --disable-pip-version-check --no-cache-dir -c requirements.txt -c requirements-test.txt --group dev \
    && chown 10001:10001 /app
COPY --chown=10001:10001 pos ./pos
COPY --chown=10001:10001 tests ./tests
ENV HOME=/tmp
USER 10001:10001
CMD ["sh", "-ec", "ruff check . && ruff format --check . && mypy && basedpyright && python -m pytest --cov=pos"]

FROM runtime AS default
