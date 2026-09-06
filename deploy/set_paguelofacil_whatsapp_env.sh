#!/usr/bin/env bash
# Append PagueloFacil WhatsApp + internal notify vars to Oracle .env files (idempotent).
set -eu

TG="/home/ubuntu/EspaLuzFamilybot"
WA="/home/ubuntu/EspaLuzWhatsApp"
TG_ENV="$TG/.env"
WA_ENV="$WA/.env"

ensure_line() {
  local file="$1"
  local key="$2"
  local value="$3"
  if [[ ! -f "$file" ]]; then
    echo "Missing $file — create it first with PAGUELOFACIL_CCLW etc."
    exit 1
  fi
  if grep -q "^${key}=" "$file" 2>/dev/null; then
    echo "  ok (exists): $key in $file"
  else
    echo "${key}=${value}" >> "$file"
    echo "  added: $key to $file"
  fi
}

SECRET=""
if [[ -f "$TG_ENV" ]] && grep -q "^INTERNAL_WEBHOOK_SECRET=" "$TG_ENV" 2>/dev/null; then
  SECRET=$(grep "^INTERNAL_WEBHOOK_SECRET=" "$TG_ENV" | cut -d= -f2-)
fi
if [[ -z "$SECRET" ]]; then
  SECRET=$(openssl rand -hex 24)
  echo "Generated new INTERNAL_WEBHOOK_SECRET"
fi

echo "== Familybot $TG_ENV =="
ensure_line "$TG_ENV" "PAGUELOFACIL_SANDBOX" "false"
ensure_line "$TG_ENV" "PAGUELOFACIL_WA_NOTIFY_URL" "http://127.0.0.1:8081/internal/paguelofacil-grant"
ensure_line "$TG_ENV" "INTERNAL_WEBHOOK_SECRET" "$SECRET"

echo "== WhatsApp $WA_ENV =="
ensure_line "$WA_ENV" "ESPALUZ_FAMILYBOT_PATH" "$TG"
ensure_line "$WA_ENV" "PAGUELOFACIL_PAYMENTS_FILE" "$TG/paguelofacil_payments.json"
ensure_line "$WA_ENV" "PAGUELOFACIL_WA_ENABLED" "true"
ensure_line "$WA_ENV" "PAGUELOFACIL_AMOUNT_WA" "11.00"
ensure_line "$WA_ENV" "PAGUELOFACIL_WA_NOTIFY_URL" "http://127.0.0.1:8081/internal/paguelofacil-grant"
ensure_line "$WA_ENV" "INTERNAL_WEBHOOK_SECRET" "$SECRET"

echo ""
echo "Done. Restart: sudo systemctl restart espaluz-familybot espaluz-payments-webhook espaluz-whatsapp"
