"""
MyGreenGarden V7.0 — Service email SMTP.
Identifiants chargés depuis .env (plus de credentials en dur).
"""
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from config import settings

logger = logging.getLogger(__name__)


def send_alert_email(subject: str, body_text: str) -> bool:
    """
    Envoie un email d'alerte via SMTP SSL.
    Retourne True si envoi réussi.
    """
    if not all([settings.smtp_user, settings.smtp_password, settings.email_sender]):
        logger.warning("Email non configuré (.env) — alerte non envoyée")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = settings.email_sender
        msg["To"]      = settings.email_receiver

        now = datetime.now().strftime("%-d.%-m.%Y à %H:%M:%S")
        html = f"""
        <html><body style="font-family: Arial, sans-serif; background:#f0fdf4; padding:20px;">
          <div style="max-width:500px; margin:auto; background:white; border-radius:12px;
                      border-left:5px solid #dc2626; padding:24px; box-shadow:0 2px 8px rgba(0,0,0,.1)">
            <h2 style="color:#dc2626; margin-top:0">⚠️ MyGreenGarden — Alerte</h2>
            <p style="color:#374151; font-size:16px">{body_text}</p>
            <hr style="border-color:#e5e7eb">
            <p style="color:#9ca3af; font-size:13px">
              Envoyé le {now}<br>
              <em>MyGreenGarden V7.0 — Serre automatisée</em>
            </p>
          </div>
        </body></html>
        """

        msg.attach(MIMEText(body_text, "plain", "utf-8"))
        msg.attach(MIMEText(html, "html", "utf-8"))

        with smtplib.SMTP_SSL(settings.smtp_server, settings.smtp_port) as server:
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.email_sender, settings.email_receiver, msg.as_string())

        logger.info(f"Email d'alerte envoyé : {subject}")
        return True

    except Exception as e:
        logger.error(f"Erreur envoi email : {e}")
        return False
