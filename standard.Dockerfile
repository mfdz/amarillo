ARG DOCKER_REGISTRY
FROM ${DOCKER_REGISTRY}/amarillo/amarillo-base

ARG PLUGINS=\
"amarillo-metrics "\
"amarillo-gtfs-exporter "

ARG PACKAGE_REGISTRY_URL

ENV METRICS_USER=''
ENV METRICS_PASSWORD=''

# RUN pip install $PLUGINS

RUN pip install --no-cache-dir --upgrade --extra-index-url ${PACKAGE_REGISTRY_URL} ${PLUGINS}

# Create the error.log, otherwise we get a permission error when we try to write to it
RUN touch /app/error.log
RUN chmod 777 /app/error.log

RUN useradd amarillo
USER amarillo