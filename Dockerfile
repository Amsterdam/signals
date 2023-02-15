# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.10

##################################################
#                   Python                       #
##################################################
FROM python:${PYTHON_VERSION}-slim-buster

ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE=signals.settings
ARG DJANGO_SECRET_KEY=insecure_docker_build_key

WORKDIR /app/app

RUN useradd --no-create-home signals

COPY api/requirements.txt /app/requirements.txt

RUN set -eux;  \
    apt-get update; \
    apt-get install -y \
        libgeos-3.7 \
        gdal-bin \
        libgdal20 \
        libspatialite7 \
        libfreexl1 \
        libgeotiff2 \
        libwebp6 \
        proj-bin \
        mime-support \
        gettext \
        libwebpmux3 \
        libwebpdemux2 \
        libxml2 \
        libfreetype6 \
        libtiff5 \
        libgdk-pixbuf2.0-0 \
        libmagic1 \
        libcairo2 \
        libpango1.0-0 \
        gcc \
        graphviz \
    ; \
    pip install --no-cache -r /app/requirements.txt; \
    apt-get purge -y gcc; \
    rm -rf /var/lib/apt/lists/*

COPY api/ /app

RUN set -eux; \
    chgrp signals /app; \
    chmod g+w /app; \
    mkdir -p /app/static /app/media; \
    chown signals /app/static; \
    chown signals /app/media

USER signals

RUN SECRET_KEY=$DJANGO_SECRET_KEY python manage.py collectstatic --no-input

CMD uwsgi
