FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services ./services
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini
COPY scripts ./scripts
COPY docs ./docs

# Las migraciones y la semilla se aplican al arrancar (ver services/viajes-crud/app/main.py),
# por lo que el contenedor es reproducible desde una BD vacía.
CMD ["uvicorn", "services.viajes_crud.app.main:app", "--host", "0.0.0.0", "--port", "8100"]
