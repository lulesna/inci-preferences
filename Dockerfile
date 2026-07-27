FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN SECRET_KEY="dummy-key-for-build" \
    DEBUG=False \
    DB_NAME="dummy" \
    DB_USER="dummy" \
    DB_PASSWORD="dummy" \
    DB_HOST="localhost" \
    DB_PORT="5432" \
    USE_POSTGRES=False \
    ALLOWED_HOSTS="localhost" \
    python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]