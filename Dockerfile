FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN SECRET_KEY="dummy-key-for-build" \
    DB_NAME="dummy" \
    DB_USER="dummy" \
    DB_PASSWORD="dummy" \
    DB_HOST="localhost" \
    python manage.py collectstatic --noinput

RUN useradd -r -m appuser && chown -R appuser:appuser /app

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

EXPOSE 8000

# Uruchamiane przez "sh", nie bezposrednio - dzieki temu nie zalezy od bitu
# wykonywalnosci, ktory na Windowsie i tak sie nie przenosi.
ENTRYPOINT ["/bin/sh", "/app/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
