#!/usr/bin/env sh

set -ex

docker pull lambdalint/apex-builder
docker run -ti -v $(pwd):/app lambdalint/apex-builder python3 -m pip install --no-use-wheel -r requirements.txt -t .
