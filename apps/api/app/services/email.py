from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

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

    def send_internal_notification(self, *, first_name: str, last_name: str, email: str, resume_original_filename: str) -> None:
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

    def send_internal_notification(self, *, first_name: str, last_name: str, email: str, resume_original_filename: str) -> None:
        message = EmailMessage(
            to=settings.internal_notification_email,
            subject="New lead submitted",
            body=(
                f"New lead received from {first_name} {last_name} ({email}). "
                f"Resume: {resume_original_filename}"
            ),
        )
        self.send(message)


def get_email_service() -> EmailService:
    provider = settings.email_provider.lower()
    if provider == "console":
        return ConsoleEmailService()
    raise ValueError(f"Unsupported email provider: {settings.email_provider}")
