#!/usr/bin/env bash
set -euo pipefail
ENV="/home/ubuntu/EspaLuzFamilybot/.env"
CCLW="${1:?CCLW required}"
touch "$ENV"
grep -v '^PAGUELOFACIL_' "$ENV" > "$ENV.tmp" 2>/dev/null || cp "$ENV" "$ENV.tmp"
mv "$ENV.tmp" "$ENV"
{
  echo "PAGUELOFACIL_CCLW=${CCLW}"
  echo "PAGUELOFACIL_SANDBOX=false"
  echo "PAGUELOFACIL_AMOUNT=11.00"
  echo "PAGUELOFACIL_ACCESS_DAYS=30"
} >> "$ENV"
echo "CCLW length: ${#CCLW}"
sudo systemctl restart espaluz-payments-webhook espaluz-familybot
sleep 2
systemctl is-active espaluz-payments-webhook espaluz-familybot
cd /home/ubuntu/EspaLuzFamilybot
python3 << 'PY'
from espaluz_paguelofacil import is_configured, create_payment_link
print("configured:", is_configured())
r = create_payment_link("1494063516")
print("success:", r.get("success"))
if r.get("url"):
    print("url:", r["url"][:90] + "...")
else:
    print("error:", r.get("error"))
PY
