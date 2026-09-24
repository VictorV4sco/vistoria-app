FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY app ./app

RUN pip install --no-cache-dir -e ".[dev]"

COPY tests ./tests
COPY docs ./docs
COPY templates ./templates
COPY assets ./assets

CMD ["pytest"]
