FROM tiangolo/uvicorn-gunicorn:python3.10-slim

LABEL maintainer="info@mfdz.de"

WORKDIR /app

RUN \
	apt update \
	&& apt install -y \
	# GDAL headers are required for fiona, which is required for geopandas.
	# Also gcc is used to compile C++ code.
	libgdal-dev g++ \
	# libspatialindex is required for rtree.
	libspatialindex-dev \
	# Remove package index obtained by `apt update`.
	&& rm -rf /var/lib/apt/lists/*

 ENV ADMIN_TOKEN=''
 ENV RIDE2GO_TOKEN=''
 ENV SECRET_KEY=''
 ENV METRICS_USER=''
 ENV METRICS_PASSWORD=''

EXPOSE 80

ARG PLUGINS

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt ${PLUGINS}

# set MODULE_NAME explicitly
ENV MODULE_NAME=amarillo.main

COPY ./amarillo /app/amarillo
COPY ./amarillo/plugins /app/amarillo/plugins
COPY ./amarillo/static/static /app/static
COPY ./amarillo/static/templates /app/templates
COPY ./amarillo/static/config /app
COPY ./amarillo/static/logging.conf /app
COPY ./amarillo/static/data /app/data

# This image inherits uvicorn-gunicorn's CMD. If you'd like to start uvicorn, use this instead
# CMD ["uvicorn", "amarillo.main:app", "--host", "0.0.0.0", "--port", "8000"]
