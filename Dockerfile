FROM python:3.10-slim-buster as Builder

WORKDIR /app

COPY . .

RUN set -xe; \
    apt-get update; \
    apt-get -y install git build-essential; \
    pip3 install -r requirements.txt

FROM python:3.10-slim-buster

WORKDIR /app

COPY --from=Builder /app .
COPY --from=Builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

CMD [ "bash", "start.sh" ]
