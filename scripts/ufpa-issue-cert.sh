#!/usr/bin/env bash
set -euo pipefail

DOMAIN="${DOMAIN:-fasitech.cameta.ufpa.br}"
EMAIL="${LETSENCRYPT_EMAIL:-eltonss@ufpa.br}"
APP_DIR="${APP_DIR:-/home/eltonss/FasiTech}"
WEBROOT="${WEBROOT:-$APP_DIR/certbot/www}"
COMPOSE_FILE="${COMPOSE_FILE:-$APP_DIR/docker-compose.productionUFPA.yml}"

cd "$APP_DIR"
mkdir -p "$WEBROOT"

NGINX_UFPA_CONF=./docker/nginx/nginx.ufpa.bootstrap.conf \
  docker compose -p fasitech -f "$COMPOSE_FILE" up -d --no-build nginx

docker run --rm \
  -v /etc/letsencrypt:/etc/letsencrypt \
  -v "$WEBROOT:/var/www/certbot" \
  certbot/certbot certonly \
    --webroot \
    --webroot-path /var/www/certbot \
    --domain "$DOMAIN" \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    --non-interactive

docker compose -p fasitech -f "$COMPOSE_FILE" up -d --no-build nginx
docker exec fasitech-nginx-prod nginx -t
docker exec fasitech-nginx-prod nginx -s reload
