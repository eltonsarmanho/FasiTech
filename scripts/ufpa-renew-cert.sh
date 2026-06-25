#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/home/eltonss/FasiTech}"
WEBROOT="${WEBROOT:-$APP_DIR/certbot/www}"

mkdir -p "$WEBROOT"

docker run --rm \
  -v /etc/letsencrypt:/etc/letsencrypt \
  -v "$WEBROOT:/var/www/certbot" \
  certbot/certbot renew \
    --webroot \
    --webroot-path /var/www/certbot \
    --quiet

docker exec fasitech-nginx-prod nginx -t
docker exec fasitech-nginx-prod nginx -s reload
