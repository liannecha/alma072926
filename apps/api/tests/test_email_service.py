from typing import Any

from app.core import config as config_module
from app.services.email import ConsoleEmailService, EmailMessage, ResendEmailService, SmtpEmailService, get_email_service


class FakeResponse:
    def __init__(self) -> None:
        self.raise_for_status_called = False

    def raise_for_status(self) -> None:
        self.raise_for_status_called = True


def test_get_email_service_returns_resend_provider() -> None:
    original_provider = config_module.settings.email_provider
    try:
        config_module.settings.email_provider = "resend"

        service = get_email_service()

        assert isinstance(service, ResendEmailService)
    finally:
        config_module.settings.email_provider = original_provider


def test_get_email_service_returns_smtp_provider() -> None:
    original_provider = config_module.settings.email_provider
    try:
        config_module.settings.email_provider = "smtp"

        service = get_email_service()

        assert isinstance(service, SmtpEmailService)
    finally:
        config_module.settings.email_provider = original_provider


def test_follow_up_email_mentions_alma_review(monkeypatch) -> None:
    messages: list[EmailMessage] = []
    monkeypatch.setattr(ConsoleEmailService, "send", lambda _self, message: messages.append(message))

    ConsoleEmailService().send_follow_up(first_name="Ada", email="ada@example.com")

    assert len(messages) == 1
    assert messages[0].to == "ada@example.com"
    assert "An Alma team member has reviewed your information." in messages[0].body


def test_resend_provider_posts_email_payload(monkeypatch) -> None:
    calls: list[dict[str, Any]] = []
    fake_response = FakeResponse()

    def fake_post(*args: Any, **kwargs: Any) -> FakeResponse:
        calls.append({"args": args, "kwargs": kwargs})
        return fake_response

    monkeypatch.setattr("app.services.email.requests.post", fake_post)

    original_api_key = config_module.settings.resend_api_key
    original_email_from = config_module.settings.email_from
    try:
        config_module.settings.resend_api_key = "re_test_key"
        config_module.settings.email_from = "Alma <onboarding@example.com>"

        ResendEmailService().send(
            EmailMessage(
                to="prospect@example.com",
                subject="Alma follow-up",
                body="Thanks for submitting your information.",
            )
        )

        assert len(calls) == 1
        assert calls[0]["args"] == (ResendEmailService.api_url,)
        assert calls[0]["kwargs"]["headers"]["Authorization"] == "Bearer re_test_key"
        assert calls[0]["kwargs"]["headers"]["User-Agent"] == "alma-lead-intake/1.0"
        assert calls[0]["kwargs"]["json"] == {
            "from": "Alma <onboarding@example.com>",
            "to": ["prospect@example.com"],
            "subject": "Alma follow-up",
            "text": "Thanks for submitting your information.",
        }
        assert calls[0]["kwargs"]["timeout"] == 10
        assert fake_response.raise_for_status_called is True
    finally:
        config_module.settings.resend_api_key = original_api_key
        config_module.settings.email_from = original_email_from


def test_smtp_provider_sends_mime_message(monkeypatch) -> None:
    smtp_calls: list[dict[str, Any]] = []

    class FakeSmtp:
        def __init__(self, host: str, port: int, timeout: int) -> None:
            smtp_calls.append({"event": "init", "host": host, "port": port, "timeout": timeout})

        def __enter__(self) -> "FakeSmtp":
            smtp_calls.append({"event": "enter"})
            return self

        def __exit__(self, *args: Any) -> None:
            smtp_calls.append({"event": "exit"})

        def starttls(self) -> None:
            smtp_calls.append({"event": "starttls"})

        def login(self, username: str, password: str) -> None:
            smtp_calls.append({"event": "login", "username": username, "password": password})

        def send_message(self, message: Any) -> None:
            smtp_calls.append(
                {
                    "event": "send_message",
                    "from": message["From"],
                    "to": message["To"],
                    "subject": message["Subject"],
                    "body": message.get_content(),
                }
            )

    monkeypatch.setattr("app.services.email.smtplib.SMTP", FakeSmtp)

    original_email_from = config_module.settings.email_from
    original_host = config_module.settings.smtp_host
    original_port = config_module.settings.smtp_port
    original_username = config_module.settings.smtp_username
    original_password = config_module.settings.smtp_password
    try:
        config_module.settings.email_from = "Alma <lianne.cha@gmail.com>"
        config_module.settings.smtp_host = "smtp.gmail.com"
        config_module.settings.smtp_port = 587
        config_module.settings.smtp_username = "lianne.cha@gmail.com"
        config_module.settings.smtp_password = "app-password"

        SmtpEmailService().send(
            EmailMessage(
                to="lead@example.com",
                subject="Alma follow-up",
                body="Thanks for submitting your information.",
            )
        )

        assert smtp_calls == [
            {"event": "init", "host": "smtp.gmail.com", "port": 587, "timeout": 10},
            {"event": "enter"},
            {"event": "starttls"},
            {"event": "login", "username": "lianne.cha@gmail.com", "password": "app-password"},
            {
                "event": "send_message",
                "from": "Alma <lianne.cha@gmail.com>",
                "to": "lead@example.com",
                "subject": "Alma follow-up",
                "body": "Thanks for submitting your information.\n",
            },
            {"event": "exit"},
        ]
    finally:
        config_module.settings.email_from = original_email_from
        config_module.settings.smtp_host = original_host
        config_module.settings.smtp_port = original_port
        config_module.settings.smtp_username = original_username
        config_module.settings.smtp_password = original_password
