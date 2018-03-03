#!/usr/bin/env sh

docker pull lambdalint/apex-builder
docker run -ti -v $(pwd):/app lambdalint/apex-builder pip install --no-use-wheel -r requirements.txt -t .
