FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libegl1 libglib2.0-0 libdbus-1-3 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY app ./app

RUN pip install --no-cache-dir -e ".[dev]"

RUN apt-get update \
    && apt-get install -y --no-install-recommends libfontconfig1 libxkbcommon0 \
        libxcb-cursor0 libxkbcommon-x11-0 libxcb-xinerama0 \
        libxcb-icccm4 libxcb-keysyms1 libxcb-shape0 \
    && rm -rf /var/lib/apt/lists/*

COPY tests ./tests
COPY docs ./docs
COPY templates ./templates
COPY assets ./assets

CMD ["pytest"]
