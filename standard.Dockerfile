ARG DOCKER_REGISTRY
FROM ${DOCKER_REGISTRY}/amarillo/amarillo-base

ARG PLUGINS=\
"amarillo-metrics "\
"amarillo-gtfs-exporter "

ARG PACKAGE_REGISTRY_URL

ENV METRICS_USER=''
ENV METRICS_PASSWORD=''

# RUN pip install $PLUGINS

RUN --mount=type=secret,id=AMARILLO_REGISTRY_CREDENTIALS \
pip install --no-cache-dir --upgrade --extra-index-url https://$(cat /run/secrets/AMARILLO_REGISTRY_CREDENTIALS)@${PACKAGE_REGISTRY_URL} ${PLUGINS}
