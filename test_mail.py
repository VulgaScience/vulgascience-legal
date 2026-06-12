
# test_mail.py
# Test d'envoi d'email via SMTP en lisant les credentials dans .env
# Usage :
# 1) Créer .env à la racine du repo (voir README), y mettre MAIL_SMTP_* et MAIL_SMTP_PASS
# 2) Activer un venv (recommandé) et installer python-dotenv :
#    pip install python-dotenv
# 3) Exécuter : python test_mail.py

import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("MAIL_SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("MAIL_SMTP_PORT", "587"))
SMTP_USER = os.getenv("MAIL_SMTP_USER")
SMTP_PASS = os.getenv("MAIL_SMTP_PASS")
TO = os.getenv("MAIL_TEST_TO", SMTP_USER)  # envoi à toi-même par défaut

if not SMTP_USER or not SMTP_PASS:
    print("Erreur : variables MAIL_SMTP_USER / MAIL_SMTP_PASS non définies dans .env")
    raise SystemExit(1)

msg = EmailMessage()
msg["Subject"] = "Test pipeline email — VulgaScience"
msg["From"] = SMTP_USER
msg["To"] = TO
msg.set_content("Ceci est un test envoyé depuis le pipeline VulgaScience. Si tu vois ce message, la configuration SMTP fonctionne.")

try:
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
        smtp.set_debuglevel(0)
        smtp.ehlo()
        smtp.starttls()
        smtp.login(SMTP_USER, SMTP_PASS)
        smtp.send_message(msg)
    print(f"Email envoyé avec succès à {TO}")
except Exception as e:
    print("Envoi échoué :", repr(e))
    raise
