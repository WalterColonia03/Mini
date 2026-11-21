FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY requirements.txt ./
RUN pip install --requirement requirements.txt
COPY . ./

RUN APP_ENV=test DJANGO_DEBUG=false DJANGO_SECRET_KEY=static-build-only \
    python manage.py collectstatic --noinput

RUN useradd --create-home --uid 10001 pmv \
    && chown -R pmv:pmv /app
USER pmv

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]

