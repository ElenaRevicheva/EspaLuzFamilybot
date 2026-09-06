#!/usr/bin/env python3
"""One-off: grant PagueloFacil access when webhook was received but not processed."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from espaluz_paguelofacil import grant_access, notify_user_paid, get_access_info, PLATFORM_TELEGRAM, PLATFORM_WHATSAPP

if __name__ == "__main__":
    user_id = sys.argv[1] if len(sys.argv) > 1 else "5481526862"
    cod_oper = sys.argv[2] if len(sys.argv) > 2 else "LK-PMYTCC2O2UFF"
    email = sys.argv[3] if len(sys.argv) > 3 else os.environ.get("PF_GRANT_EMAIL", "")
    platform = (sys.argv[4] if len(sys.argv) > 4 else "telegram").lower()
    if platform in ("wa", "whatsapp"):
        platform = PLATFORM_WHATSAPP
    else:
        platform = PLATFORM_TELEGRAM
    result = grant_access(user_id, cod_oper=cod_oper, amount="11.00", email=email, platform=platform)
    ok = notify_user_paid(user_id, cod_oper, result.get("paid_until"), platform=platform)
    info = get_access_info(user_id)
    print("granted:", result)
    print("notify_ok:", ok)
    print("access:", info)
