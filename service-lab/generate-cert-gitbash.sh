#!/usr/bin/env bash
set -euo pipefail
mkdir -p certs
docker run --rm -v "$PWD/certs:/certs" alpine:3.22 sh -c "apk add --no-cache openssl >/dev/null && openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /certs/local.key -out /certs/local.crt -subj '/CN=app.local.test' -addext 'subjectAltName=DNS:app.local.test,DNS:other.local.test,DNS:localhost'"
echo "Created certs/local.crt and certs/local.key"
