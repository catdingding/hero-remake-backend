FROM python:3.9.5-buster
WORKDIR /app

RUN apt-get update && apt-get install -y musl-dev libffi-dev default-libmysqlclient-dev build-essential nginx supervisor

COPY docker_build_files/nginx/default.conf /etc/nginx/conf.d/
COPY docker_build_files/supervisor/asgi.conf /etc/supervisor/conf.d/
RUN mkdir /run/daphne/
RUN rm /etc/nginx/sites-enabled/default

COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . .

ENV DJANGO_SETTINGS_MODULE=hero.settings
CMD supervisord && nginx -g "daemon off;"