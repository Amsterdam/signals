FROM amsterdam/python
MAINTAINER datapunt@amsterdam.nl

ENV PYTHONUNBUFFERED 1

EXPOSE 8000

RUN mkdir -p /static && chown datapunt /static

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

COPY app /app/
COPY deploy /deploy/

WORKDIR /app

USER datapunt

RUN export DJANGO_SETTINGS_MODULE=signals.settings

RUN python manage.py collectstatic --no-input

CMD uwsgi
