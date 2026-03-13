FROM node:20-alpine

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci && npm install -g serve

COPY frontend/ /app/frontend/
COPY deploy/scripts/frontend-entrypoint.sh /usr/local/bin/frontend-entrypoint.sh
RUN chmod +x /usr/local/bin/frontend-entrypoint.sh

EXPOSE 4173

ENTRYPOINT ["frontend-entrypoint.sh"]
