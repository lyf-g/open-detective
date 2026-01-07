# Stage 1: Builder
FROM python:3.14-slim as builder

WORKDIR /app
COPY src/backend/requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Stage 2: Runtime
FROM python:3.14-slim

WORKDIR /app

# Install dependencies from builder
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir /wheels/*

# Copy application code
COPY src/backend ./src/backend
COPY data ./data

# Expose port
EXPOSE 8081

# Run application
CMD ["python", "-m", "uvicorn", "src.backend.main:app", "--host", "0.0.0.0", "--port", "8081"]