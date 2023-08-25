# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.11

##################################################
#                   Python                       #
##################################################
FROM python:${PYTHON_VERSION}-slim-buster AS prod

ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE=signals.settings
ARG DJANGO_SECRET_KEY=insecure_docker_build_key

WORKDIR /app

RUN useradd --no-create-home signals

RUN set -eux;  \
    apt-get update && apt-get install -y \
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
        libpq-dev \
        gcc \
        graphviz \
    ; \
    rm -rf /var/lib/apt/lists/*

COPY app /app

RUN set -eux; \
    pip install --no-cache -r /app/requirements/requirements.txt; \
    pip install --no-cache tox; \
    chgrp signals /app; \
    chmod g+w /app; \
    mkdir -p /app/static /app/media; \
    chown signals /app/static; \
    chown signals /app/media

USER signals

RUN SECRET_KEY=$DJANGO_SECRET_KEY python manage.py collectstatic --no-input

CMD uwsgi


##################################################
#                    DEV                         #
##################################################
FROM prod AS dev

USER root

RUN set -eux; \
    pip install pip-tools; \
    pip-sync requirements/requirements.txt requirements/requirements_dev.txt

USER signals
