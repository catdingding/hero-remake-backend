FROM python:3.6-buster
WORKDIR /app

RUN apt-get update && apt-get install -y musl-dev libffi-dev default-libmysqlclient-dev build-essential

COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000

ENV DJANGO_SETTINGS_MODULE=hero.settings
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "hero.asgi:application"]