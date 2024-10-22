# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.12

##################################################
#                   Python                       #
##################################################
FROM python:${PYTHON_VERSION}-slim-bookworm AS prod

ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE=signals.settings
ENV NLTK_DOWNLOAD_DIR=/tmp/nltk_data
ARG DJANGO_SECRET_KEY=insecure_docker_build_key

WORKDIR /app

RUN useradd --no-create-home signals

RUN set -eux;  \
    apt-get update && apt-get install -y \
        libgeos3.11.1 \
        gdal-bin \
        libgdal32 \
        libspatialite7 \
        libfreexl1 \
        libgeotiff5 \
        libwebp7 \
        proj-bin \
        mime-support \
        gettext \
        libwebpmux3 \
        libwebpdemux2 \
        libxml2 \
        libfreetype6 \
        libtiff6 \
        libgdk-pixbuf2.0-0 \
        libmagic1 \
        libcairo2 \
        libpango1.0-0 \
        libpcre3 \
        libpcre3-dev \
        libpq-dev \
        gcc \
        graphviz \
    ; \
    rm -rf /var/lib/apt/lists/*

COPY app/requirements /app/requirements
COPY app/signals/apps/classification/requirements.txt /app/signals/apps/classification/requirements.txt

RUN set -eux; \
    pip install --no-cache -r /app/requirements/requirements.txt; \
    pip install --no-cache -r /app/signals/apps/classification/requirements.txt; \
    pip install --no-cache tox; \
    chgrp signals /app; \
    chmod g+w /app; \
    mkdir -p /app/static /app/media; \
    chown signals /app/static; \
    chown signals /app/media

COPY app /app

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


##################################################
#                    TEST                        #
##################################################
FROM prod AS test

USER root

RUN set -eux; \
    pip install pip-tools; \
    pip-sync requirements/requirements.txt requirements/requirements_test.txt

USER signals
