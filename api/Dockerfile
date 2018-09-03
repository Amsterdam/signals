FROM amsterdam/python
MAINTAINER datapunt@amsterdam.nl

ENV PYTHONUNBUFFERED 1

EXPOSE 8000

RUN mkdir -p /static && chown datapunt /static
RUN mkdir -p /app && chown datapunt /app
RUN mkdir -p /deploy && chown datapunt /deploy

COPY requirements.txt /requirements.txt
COPY app /app/
COPY deploy /deploy/

RUN pip install --no-cache-dir -r /requirements.txt

WORKDIR /app

USER datapunt

ENV DJANGO_SETTINGS_MODULE=signals.settings.production
ARG DJANGO_SECRET_KEY=insecure_docker_build_key
RUN SECRET_KEY=$DJANGO_SECRET_KEY python manage.py collectstatic --no-input

CMD uwsgi
