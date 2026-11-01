FROM node:22-alpine AS ui
WORKDIR /src/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
ENV PYTHONPATH=/app/backend/src
ENV FRONTEND_DIST=/app/frontend/dist
COPY backend /app/backend
COPY --from=ui /src/frontend/dist /app/frontend/dist
RUN pip install --no-cache-dir /app/backend
CMD ["python", "-m", "shoul_donation.main"]
