from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from email.message import EmailMessage as MimeEmailMessage
import smtplib
from typing import Protocol

import requests

from app.core.config import settings


@dataclass(frozen=True)
class EmailMessage:
    to: str
    subject: str
    body: str


class EmailService(Protocol):
    def send(self, message: EmailMessage) -> None:
        ...

    def send_prospect_confirmation(self, *, first_name: str, last_name: str, email: str, resume_original_filename: str) -> None:
        ...

    def send_internal_notification(
        self,
        *,
        first_name: str,
        last_name: str,
        email: str,
        resume_original_filename: str,
        submitted_at: datetime,
    ) -> None:
        ...

    def send_follow_up(self, *, first_name: str, email: str) -> None:
        ...


class ConsoleEmailService:
    def send(self, message: EmailMessage) -> None:
        print(f"[console-email] From: {settings.email_from}")
        print(f"[console-email] To: {message.to}")
        print(f"[console-email] Subject: {message.subject}")
        print(f"[console-email] Body: {message.body}")

    def send_prospect_confirmation(self, *, first_name: str, last_name: str, email: str, resume_original_filename: str) -> None:
        message = EmailMessage(
            to=email,
            subject="Thanks for your lead submission",
            body=(
                f"Hi {first_name} {last_name},\n\n"
                f"We received your lead submission with resume '{resume_original_filename}'. "
                "We will review it shortly."
            ),
        )
        self.send(message)

    def send_internal_notification(
        self,
        *,
        first_name: str,
        last_name: str,
        email: str,
        resume_original_filename: str,
        submitted_at: datetime,
    ) -> None:
        message = EmailMessage(
            to=settings.internal_notification_email,
            subject="New lead submitted",
            body=(
                f"New lead received from {first_name} {last_name} ({email}). "
                f"Submitted: {submitted_at.isoformat()}. "
                f"Resume: {resume_original_filename}"
            ),
        )
        self.send(message)

    def send_follow_up(self, *, first_name: str, email: str) -> None:
        self.send(
            EmailMessage(
                to=email,
                subject="Alma follow-up",
                body=(
                    f"Hi {first_name},\n\n"
                    "An Alma team member has reviewed your information. "
                    "Thank you for submitting your profile. Alma will follow up with you shortly."
                ),
            )
        )


class ResendEmailService(ConsoleEmailService):
    api_url = "https://api.resend.com/emails"

    def send(self, message: EmailMessage) -> None:
        if not settings.resend_api_key:
            raise ValueError("RESEND_API_KEY is required when EMAIL_PROVIDER=resend")

        response = requests.post(
            self.api_url,
            headers={
                "Authorization": f"Bearer {settings.resend_api_key}",
                "Content-Type": "application/json",
                "User-Agent": "alma-lead-intake/1.0",
            },
            json={
                "from": settings.email_from,
                "to": [message.to],
                "subject": message.subject,
                "text": message.body,
            },
            timeout=10,
        )
        response.raise_for_status()


class SmtpEmailService(ConsoleEmailService):
    def send(self, message: EmailMessage) -> None:
        if not settings.smtp_username or not settings.smtp_password:
            raise ValueError("SMTP_USERNAME and SMTP_PASSWORD are required when EMAIL_PROVIDER=smtp")

        mime_message = MimeEmailMessage()
        mime_message["From"] = settings.email_from
        mime_message["To"] = message.to
        mime_message["Subject"] = message.subject
        mime_message.set_content(message.body)

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            smtp.starttls()
            smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(mime_message)


def get_email_service() -> EmailService:
    provider = settings.email_provider.lower()
    if provider == "console":
        return ConsoleEmailService()
    if provider == "resend":
        return ResendEmailService()
    if provider == "smtp":
        return SmtpEmailService()
    raise ValueError(f"Unsupported email provider: {settings.email_provider}")
