# Backend Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY src/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/backend ./src/backend
COPY data ./data

# Init DB
RUN python data/etl_scripts/mock_data.py

EXPOSE 8000
CMD ["uvicorn", "src.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
