#!/usr/bin/env bash
# One-shot: deploy PagueloFacil WhatsApp to production on Oracle (run ON the VM as ubuntu or via ssh).
set -euo pipefail

TG="/home/ubuntu/EspaLuzFamilybot"
WA="/home/ubuntu/EspaLuzWhatsApp"

echo "== Backup reminder =="
echo "Rollback branch: backup/pre-paguelofacil-whatsapp-jun27-2026"
echo "See: $TG/deploy/BACKUP_AND_ROLLBACK_PAGUELOFACIL_WA.md"
echo ""

echo "== Pull latest main =="
sudo -u ubuntu bash -lc "cd '$TG' && git pull origin main"
sudo -u ubuntu bash -lc "cd '$WA' && git pull origin main"

echo "== Env (idempotent) =="
bash "$TG/deploy/set_paguelofacil_whatsapp_env.sh"

echo "== Payment webhooks + restart all =="
bash "$TG/deploy/oracle_rollout_payment_webhooks.sh"

echo ""
echo "== Verify =="
curl -sS "http://127.0.0.1:5000/paguelofacil-webhook" | head -c 300 && echo ""
curl -sS "http://127.0.0.1:5000/health" | head -c 200 && echo ""
systemctl is-active espaluz-familybot espaluz-payments-webhook espaluz-whatsapp

echo ""
echo "Production ready:"
echo "  Telegram: /pagar"
echo "  WhatsApp: pagar"
echo "  Webhook:  https://webhook.aideazz.xyz/paguelofacil-webhook"
