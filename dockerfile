FROM python:3.12-slim

RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

RUN pip install "poetry"

WORKDIR /app

COPY pyproject.toml poetry.lock ./
COPY app ./app

RUN poetry install --only main --no-root

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
