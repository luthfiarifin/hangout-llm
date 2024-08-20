#!/bin/bash

docker login -u "laam012" -p "Qw4TSQaub2*s3C$"
DOCKER_DEFAULT_PLATFORM=linux/amd64 docker build -t api:llm-dev . -f Dockerfile.development
docker tag api:llm-dev laam012/api:llm-dev
docker push laam012/api:llm-dev