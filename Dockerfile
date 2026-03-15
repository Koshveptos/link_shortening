
FROM python:3.13-slim-bookworm


COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app


COPY pyproject.toml uv.lock ./


RUN uv sync --frozen --no-dev --no-install-project


COPY . .


RUN uv sync --frozen --no-dev --no-editable


COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh


ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/app/.venv/bin:$PATH"


EXPOSE 8000


HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1


CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
