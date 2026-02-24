"""
notifiers.py

Notification channel helpers for SMS (Twilio) and email (SMTP SSL).
"""

from __future__ import annotations

import os
import smtplib
import socket
import ssl
from email.message import EmailMessage


class EnvReader:
    """Read and sanitize configuration values from environment variables."""

    @staticmethod
    def get(*names: str) -> str | None:
        """Return the first non-empty environment variable from `names`."""
        for name in names:
            value = os.environ.get(name)
            if value is None:
                continue
            cleaned = value.strip().strip('"').strip("'").strip()
            if cleaned:
                return cleaned
        return None


def humanize_smtp_error(exc: Exception) -> str:
    """Translate technical SMTP/TLS/network errors into readable messages."""
    if isinstance(exc, socket.gaierror):
        return "SMTP host konnte nicht aufgelöst werden (DNS/Hostname prüfen)."
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return "SMTP-Timeout (Port/Firewall/Netz prüfen)."
    if isinstance(exc, ssl.SSLCertVerificationError):
        return "SSL-Zertifikatprüfung fehlgeschlagen (Hostname/Zeit/CA prüfen)."
    if isinstance(exc, ssl.SSLError):
        return "SSL/TLS-Fehler (Modus/Port prüfen: SSL 465 oder STARTTLS 587)."
    if isinstance(exc, smtplib.SMTPAuthenticationError):
        if exc.smtp_code == 535:
            return "SMTP Login abgelehnt (535): Benutzer/Passwort oder Provider-Policy (z. B. App-Passwort) prüfen."
        return f"SMTP-Authentifizierung fehlgeschlagen ({exc.smtp_code})."
    if isinstance(exc, smtplib.SMTPResponseException):
        return f"SMTP-Fehler {exc.smtp_code}: {exc.smtp_error!r}"
    return f"SMTP-Fehler: {exc}"


class SmsNotifier:
    """Twilio SMS sender using environment-based credentials."""

    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        """Initialize notifier with explicit Twilio credentials."""
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number

    @classmethod
    def from_env(cls) -> "SmsNotifier":
        """Build a notifier from `.env` values (supports alias variable names)."""
        account_sid = EnvReader.get("TWILIO_ACCOUNT_SID", "TWILIO_SID")
        auth_token = EnvReader.get("TWILIO_AUTH_TOKEN")
        from_number = EnvReader.get("TWILIO_FROM_NUMBER", "TWILIO_PHONE")
        if not account_sid or not auth_token or not from_number:
            raise RuntimeError(
                "Missing TWILIO credentials in .env (TWILIO_ACCOUNT_SID|TWILIO_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER|TWILIO_PHONE)."
            )
        return cls(account_sid=account_sid, auth_token=auth_token, from_number=from_number)

    def send_messages(self, messages: list[str], to_numbers: list[str]) -> None:
        """Send each message to each recipient number."""
        if not messages or not to_numbers:
            return

        from twilio.rest import Client

        client = Client(self.account_sid, self.auth_token)
        for to_number in to_numbers:
            for message in messages:
                client.messages.create(from_=self.from_number, body=message, to=to_number)


class EmailNotifier:
    """SMTP SSL email sender using environment-based configuration."""

    def __init__(self, host: str, port: int, user: str, password: str, from_address: str):
        """Initialize notifier with explicit SMTP settings."""
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.from_address = from_address

    @classmethod
    def from_env(cls) -> "EmailNotifier":
        """Build a notifier from `.env` SMTP values."""
        host = EnvReader.get("SMTP_HOST")
        port = int(EnvReader.get("SMTP_PORT") or "465")
        user = EnvReader.get("SMTP_USER")
        password = EnvReader.get("SMTP_PASSWORD")
        from_address = EnvReader.get("SMTP_FROM") or user

        if not host or not user or not password or not from_address:
            raise RuntimeError("Missing SMTP_HOST/SMTP_USER/SMTP_PASSWORD/SMTP_FROM in environment (.env).")

        return cls(host=host, port=port, user=user, password=password, from_address=from_address)

    def send(self, subject: str, body: str, to_addresses: list[str]) -> None:
        """Send a plain-text email to one or multiple recipients."""
        if not to_addresses:
            return

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.from_address
        msg["To"] = ", ".join(to_addresses)
        msg.set_content(body)

        context = ssl.create_default_context()
        try:
            with smtplib.SMTP_SSL(self.host, self.port, timeout=20, context=context) as server:
                server.login(self.user, self.password)
                server.send_message(msg)
        except Exception as exc:
            raise RuntimeError(humanize_smtp_error(exc)) from exc
