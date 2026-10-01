FROM python:3.14-slim

ENV PYTHONDOTWRITEBYTECODE = 1 \
PYTHONNUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
&& poetry install --no-root --no-interaction

COPY . .
EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]