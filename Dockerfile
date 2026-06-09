FROM python:3.12-alpine AS builder

WORKDIR /tmp/build
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ============================================================================

FROM python:3.12-alpine

# Create non-root user
RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder --chown=1000:1000 /root/.local /home/appuser/.local

# Copy application
COPY --chown=1000:1000 app/ ./app/

# Set environment
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PORT=8080

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://127.0.0.1:8080/healthz', timeout=3)" || exit 1

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "30", "--access-logfile", "-", "--error-logfile", "-", "app.proxy:app"]
