FROM python:3.12-slim

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
	# curl is required for healthcheck.
	curl \
	# Remove package index obtained by `apt update`.
	&& rm -rf /var/lib/apt/lists/*

EXPOSE 80

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# set MODULE_NAME explicitly
ENV MODULE_NAME=amarillo.main
ENV MAX_WORKERS=1

COPY ./amarillo /app/amarillo
COPY enhancer.py /app
COPY docker_start.sh /app
RUN chmod +x /app/docker_start.sh

COPY ./static /app/static
COPY ./templates /app/templates
COPY config /app
COPY logging.conf /app
COPY ./conf /app/conf

CMD ["./docker_start.sh"]
