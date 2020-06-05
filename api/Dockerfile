FROM amsterdam/python:3.8.2-buster
MAINTAINER datapunt@amsterdam.nl

# libgdk-pixbuf is needed to generate PDF files with rendered JPEG images.
RUN apt-get update && apt-get install -y libgdk-pixbuf2.0-0

ENV PYTHONUNBUFFERED 1

EXPOSE 8000
WORKDIR /app/
COPY requirements.txt /requirements.txt

RUN pip install -r /requirements.txt

RUN mkdir -p /media && chown datapunt /media
RUN mkdir -p /static && chown datapunt /static

ENV DJANGO_SETTINGS_MODULE=signals.settings.production
ARG DJANGO_SECRET_KEY=insecure_docker_build_key

COPY app /app/
COPY deploy /deploy/

USER datapunt

RUN SECRET_KEY=$DJANGO_SECRET_KEY python manage.py collectstatic --no-input

CMD uwsgi
