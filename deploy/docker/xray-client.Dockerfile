FROM ghcr.io/xtls/xray-core:25.12.8 AS xray

FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    XRAY_BIN=/usr/local/bin/xray

WORKDIR /app

RUN pip install --no-cache-dir fastapi==0.116.0 uvicorn==0.35.0

COPY --from=xray /usr/local/bin/xray /usr/local/bin/xray
COPY deploy/services/xray_client/app.py /app/app.py

EXPOSE 8081 10808 10809

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8081"]
