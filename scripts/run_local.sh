#!/usr/bin/env bash
set -e
docker run --rm -p 9091:9090 --name user-crud-lab user-crud-lab:latest
