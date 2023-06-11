#!/bin/bash
docker stop rancher_exporter
docker rm rancher_exporter
docker run -i -t -d \
  --name rancher_exporter \
  -p 12009:12009 \
  --cpus=2 --memory=512m \
  --env rancher_token="token-12345:tokentokentokentokentokentokentoken" \
  --env rancher_endpoint="https://rancher.local/v3/" \
  --restart=always \
  harbor.local/library/rancher-exporter:1.0