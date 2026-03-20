#!/bin/bash
# ============================================================
# USAM Career Compass — SSL Certificate Setup
# Uses Let's Encrypt via Certbot
# Run AFTER ec2-setup.sh and after DNS is pointed to this server
# Usage: bash ssl-setup.sh yourdomain.com
# ============================================================
set -euo pipefail

DOMAIN="${1:-}"

if [ -z "$DOMAIN" ]; then
  echo "Usage: bash ssl-setup.sh yourdomain.com"
  exit 1
fi

echo "================================================================"
echo " Setting up SSL for: ${DOMAIN} and www.${DOMAIN}"
echo "================================================================"

# Ensure nginx is running
systemctl is-active --quiet nginx || systemctl start nginx

# Install certbot if not present
if ! command -v certbot &>/dev/null; then
  apt-get install -y certbot python3-certbot-nginx
fi

# Update nginx.conf with actual domain (replace placeholder)
sed -i "s/YOUR_DOMAIN/${DOMAIN}/g" /etc/nginx/sites-available/usam
nginx -t && systemctl reload nginx

# Obtain certificate
certbot --nginx \
  -d "${DOMAIN}" \
  -d "www.${DOMAIN}" \
  --non-interactive \
  --agree-tos \
  --email "admin@${DOMAIN}" \
  --redirect

# Test auto-renewal
certbot renew --dry-run

# Set up cron for auto-renewal (runs twice daily)
CRON_JOB="0 3,15 * * * root certbot renew --quiet --deploy-hook 'systemctl reload nginx'"
CRON_FILE="/etc/cron.d/certbot-usam"

if [ ! -f "$CRON_FILE" ]; then
  echo "$CRON_JOB" > "$CRON_FILE"
  chmod 644 "$CRON_FILE"
  echo "→ Cron renewal job installed at $CRON_FILE"
fi

echo ""
echo "================================================================"
echo " ✅ SSL setup complete for ${DOMAIN}"
echo "================================================================"
echo " Certificate: /etc/letsencrypt/live/${DOMAIN}/fullchain.pem"
echo " Renewal:     Automatic (cron at 3:00 and 15:00 UTC daily)"
echo " Visit:       https://${DOMAIN}"
echo "================================================================"
