# PagueloFacil WhatsApp — backup & rollback

## Backup branches (before WhatsApp PF production rollout)

| Repo | Branch | Purpose |
|------|--------|---------|
| EspaLuzFamilybot | `backup/pre-paguelofacil-whatsapp-jun27-2026` | State before WA platform support in `espaluz_paguelofacil.py` |
| EspaLuzWhatsApp | `backup/pre-paguelofacil-whatsapp-jun27-2026` | State before WA `/pagar` + PayPangea removal |

## Rollback on Oracle VM

```bash
TG=/home/ubuntu/EspaLuzFamilybot
WA=/home/ubuntu/EspaLuzWhatsApp

sudo -u ubuntu bash -lc "cd '$TG' && git fetch origin && git checkout backup/pre-paguelofacil-whatsapp-jun27-2026"
sudo -u ubuntu bash -lc "cd '$WA' && git fetch origin && git checkout backup/pre-paguelofacil-whatsapp-jun27-2026"

sudo systemctl restart espaluz-familybot espaluz-payments-webhook espaluz-whatsapp
```

Return to latest after rollback test:

```bash
sudo -u ubuntu bash -lc "cd '$TG' && git checkout main && git pull"
sudo -u ubuntu bash -lc "cd '$WA' && git checkout main && git pull"
sudo systemctl restart espaluz-familybot espaluz-payments-webhook espaluz-whatsapp
```

## Production deploy (latest main)

```bash
bash /home/ubuntu/EspaLuzFamilybot/deploy/oracle_rollout_payment_webhooks.sh
bash /home/ubuntu/EspaLuzFamilybot/deploy/set_paguelofacil_whatsapp_env.sh
sudo systemctl restart espaluz-familybot espaluz-payments-webhook espaluz-whatsapp
```
