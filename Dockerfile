# syntax=docker/dockerfile:1
FROM python:3.12-slim AS builder
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --upgrade pip && \
    pip install --no-cache-dir ".[dev]" && \
    pip install --no-cache-dir .

FROM python:3.12-slim AS runtime
# Non-root user for security
RUN useradd --create-home --shell /bin/bash pyra
WORKDIR /app
# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=builder /usr/local/bin /usr/local/bin
# Copy app source
COPY --chown=pyra:pyra . .
USER pyra
EXPOSE 7340
ENV PYRA_HOST=0.0.0.0
ENV PYRA_PORT=7340
CMD ["python", "-m", "uvicorn", "main:app._starlette", "--host", "0.0.0.0", "--port", "7340"]
