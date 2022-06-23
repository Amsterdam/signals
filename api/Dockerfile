FROM amsterdam/python:3.9.6-slim-buster
LABEL org.opencontainers.image.authors="datapunt@amsterdam.nl"

ENV PYTHONUNBUFFERED 1
EXPOSE 8000
WORKDIR /app/
COPY requirements.txt /requirements.txt

RUN apt-get update \
    && apt-get install -y \
                libgdk-pixbuf2.0-0 \
                libmagic1 \
                libcairo2 \
                libpango1.0-0 \
                gcc \
                graphviz \
    && pip install -r /requirements.txt \
    && apt-get purge -y gcc \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /media && mkdir -p /static && chown datapunt /media && chown datapunt /static

ENV DJANGO_SETTINGS_MODULE=signals.settings
ARG DJANGO_SECRET_KEY=insecure_docker_build_key

COPY app /app/
COPY deploy /deploy/

RUN chgrp datapunt /app && chmod g+w /app

USER datapunt

RUN SECRET_KEY=$DJANGO_SECRET_KEY python manage.py collectstatic --no-input

CMD uwsgi
