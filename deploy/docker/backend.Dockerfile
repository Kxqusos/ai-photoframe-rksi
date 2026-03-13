FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

WORKDIR /app/backend

RUN pip install --no-cache-dir uv

COPY backend/ /app/backend/
RUN uv sync --no-dev --frozen

COPY deploy/scripts/backend-entrypoint.sh /usr/local/bin/backend-entrypoint.sh
COPY deploy/scripts/wait-for-postgres.sh /usr/local/bin/wait-for-postgres.sh
RUN chmod +x /usr/local/bin/backend-entrypoint.sh /usr/local/bin/wait-for-postgres.sh \
    && mkdir -p /app/backend/storage /app/backend/logs

EXPOSE 8000

ENTRYPOINT ["backend-entrypoint.sh"]
