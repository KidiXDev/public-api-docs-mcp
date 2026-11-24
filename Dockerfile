FROM python:3.13-slim

LABEL org.opencontainers.image.source="https://github.com/KidiXDev/public-api-docs-mcp"

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY public_api_docs_mcp/ ./public_api_docs_mcp/
RUN pip install --no-cache-dir .

USER 65532:65532
ENTRYPOINT ["public-api-docs-mcp"]
