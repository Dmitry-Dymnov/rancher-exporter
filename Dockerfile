FROM python:alpine3.18
WORKDIR exporter
RUN apk update && pip install pipenv flask requests urllib3 pyyaml
COPY ./rancher /exporter
EXPOSE 12009
HEALTHCHECK  --interval=3m --timeout=10s --start-period=5m \
  CMD wget --no-verbose --tries=1 --spider http://localhost:12009/metrics || exit 1
ENTRYPOINT ["/usr/local/bin/python", "./app.py"]