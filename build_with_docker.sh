#!/usr/bin/env sh

set -ex

docker pull lambdalint/apex-builder
docker run -ti -v "$(pwd):/app" lambdalint/apex-builder pip-3.6 install -r requirements.txt -t .
zip function.zip -r ./ -x .git -x *.pyc
