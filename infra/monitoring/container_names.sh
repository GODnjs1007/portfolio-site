#!/bin/sh
# Grafana 컨테이너 패널의 ID(앞 12자리)가 어떤 컨테이너인지 대조
docker ps --format '{{.ID}}  {{.Names}}'
