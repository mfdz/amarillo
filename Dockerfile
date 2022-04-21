# FROM tiangolo/uvicorn-gunicorn:python3.9
FROM   tiangolo/uvicorn-gunicorn-fastapi:python3.9

LABEL maintainer="info@mfdz.de"

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY ./app /app/app
COPY config /app
COPY logging.conf /app
COPY prestart.sh /app
COPY enhancer.py /app