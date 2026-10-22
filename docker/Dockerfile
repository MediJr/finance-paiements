FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Le serveur ne tourne jamais en root dans le conteneur.
RUN useradd --create-home --uid 1000 finance \
    && mkdir -p /app/media /app/staticfiles \
    && chown -R finance:finance /app
USER finance

EXPOSE 8001

# Production : Gunicorn (le docker-compose de développement remplace par runserver).
CMD ["gunicorn", "--chdir", "backend", "config.wsgi:application", \
     "--bind", "0.0.0.0:8001", "--workers", "3", "--access-logfile", "-"]
