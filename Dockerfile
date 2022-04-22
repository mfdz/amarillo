FROM python:3.9-slim

WORKDIR /code

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

COPY ./requirements.txt /code/requirements.txt

RUN \
	pip install --no-cache-dir --upgrade -r /code/requirements.txt \
	# For some reason, --no-cache-dir doesn't work. :(
	&& rm -rf ~/.cache/pip

ENV RIDE2GO_TOKEN=''

EXPOSE 8000

COPY ./app /code/app
COPY ./static /code/static
COPY config /code
COPY logging.conf /code

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]