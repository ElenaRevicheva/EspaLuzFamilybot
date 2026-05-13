#!/usr/bin/env bash
set -euo pipefail
# Canonical VM paths — ORACLE_ALL_PRODUCTS_RESILIENCE.md
TG="/home/ubuntu/EspaLuzFamilybot"
WA="/home/ubuntu/EspaLuzWhatsApp"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "== Pull EspaLuzFamilybot / EspaLuzWhatsApp =="
sudo -u ubuntu bash -lc "cd '$TG' && git pull origin main"
sudo -u ubuntu bash -lc "cd '$WA' && git pull origin main"

echo "== Ensure Flask deps exist (venv recommended on server — see systemd unit ExecStart) =="
sudo -u ubuntu bash -lc "python3 -c 'import flask' 2>/dev/null || pip3 install --user 'Flask>=2' python-dotenv requests"

echo "== systemd: payment webhooks (:5000) =="
sudo cp "$SCRIPT_DIR/espaluz-payments-webhook.service" /etc/systemd/system/espaluz-payments-webhook.service

sudo systemctl daemon-reload
sudo systemctl enable espaluz-payments-webhook
sudo systemctl restart espaluz-payments-webhook

echo "== Restart BOTH messengers (systemd names from resilience doc) =="
sudo systemctl restart espaluz-familybot || true
sudo systemctl restart espaluz-whatsapp || true

echo ""
echo "== Nginx NOTE =="
echo "If webhook.aideazz.xyz already proxies location / → 127.0.0.1:5000, /paguelofacil-webhook is already routed."
echo "Otherwise merge: $SCRIPT_DIR/webhook.aideazz.xyz.nginx.snippet.conf"
echo "then: sudo nginx -t && sudo systemctl reload nginx"
echo ""

echo "== Local probes (:5000) =="
curl -sS "http://127.0.0.1:5000/health" | head -c 220 && echo "" || echo "FAIL :5000 health"
curl -sS "http://127.0.0.1:5000/paguelofacil-webhook" | head -c 350 && echo "" || echo "FAIL pf GET probe"
