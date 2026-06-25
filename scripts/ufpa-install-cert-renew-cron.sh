#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/home/eltonss/FasiTech}"
CRON_CMD="17 3 * * * $APP_DIR/scripts/ufpa-renew-cert.sh >> $APP_DIR/certbot/renew.log 2>&1"

chmod +x "$APP_DIR/scripts/ufpa-issue-cert.sh" "$APP_DIR/scripts/ufpa-renew-cert.sh"
mkdir -p "$APP_DIR/certbot"

(crontab -l 2>/dev/null | grep -Fv "$APP_DIR/scripts/ufpa-renew-cert.sh"; echo "$CRON_CMD") | crontab -
crontab -l | grep -F "$APP_DIR/scripts/ufpa-renew-cert.sh"
