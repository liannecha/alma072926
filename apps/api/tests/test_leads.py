from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core import config as config_module
from app.core import database as database_module
from app.models.lead import Lead, LeadStatus


class DummyEmailService:
    def send_prospect_confirmation(self, **kwargs: Any) -> None:
        return None

    def send_internal_notification(self, **kwargs: Any) -> None:
        return None

    def send_follow_up(self, **kwargs: Any) -> None:
        return None


class RecordingEmailService(DummyEmailService):
    def __init__(self) -> None:
        self.prospect_calls: list[dict[str, Any]] = []
        self.internal_calls: list[dict[str, Any]] = []
        self.follow_up_calls: list[dict[str, Any]] = []

    def send_prospect_confirmation(self, **kwargs: Any) -> None:
        self.prospect_calls.append(kwargs)

    def send_internal_notification(self, **kwargs: Any) -> None:
        self.internal_calls.append(kwargs)

    def send_follow_up(self, **kwargs: Any) -> None:
        self.follow_up_calls.append(kwargs)


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "test.db"
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir(parents=True, exist_ok=True)

    config_module.settings.database_url = f"sqlite:///{db_path}"
    config_module.settings.resume_storage_dir = str(storage_dir)
    config_module.settings.internal_auth_token = "test-token"
    config_module.settings.google_client_id = ""
    config_module.settings.internal_allowed_emails = ""
    config_module.settings.internal_allowed_email_domain = ""
    config_module.settings.internal_notification_email = "lianne.cha@gmail.com"

    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    database_module.engine = engine
    database_module.SessionLocal = SessionLocal
    database_module.Base.metadata.create_all(bind=engine)

    import importlib

    import app.api.leads as leads_module
    import app.api.routes as routes_module
    import app.main as main_module

    importlib.reload(leads_module)
    importlib.reload(routes_module)
    importlib.reload(main_module)

    def override_get_db() -> Any:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    main_module.app.dependency_overrides[leads_module.get_db] = override_get_db
    monkeypatch.setattr(leads_module, "get_email_service", lambda: DummyEmailService())

    with TestClient(main_module.app) as test_client:
        yield test_client

    main_module.app.dependency_overrides.clear()


def _create_lead(client: TestClient, *, email: str = "lead@example.com") -> dict[str, Any]:
    pdf_bytes = b"%PDF-1.4\n%test"
    response = client.post(
        "/api/leads",
        data={"first_name": "Ada", "last_name": "Lovelace", "email": email},
        files={"resume": ("resume.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_public_lead_creation_succeeds_with_pdf_upload_and_returns_pending(client: TestClient) -> None:
    response = _create_lead(client, email="public@example.com")

    assert response["status"] == LeadStatus.PENDING.value
    assert response["resume_original_filename"] == "resume.pdf"
    assert response["email"] == "public@example.com"


def test_lead_creation_sends_prospect_and_internal_emails_with_submission_time(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.api.leads as leads_module

    email_service = RecordingEmailService()
    monkeypatch.setattr(leads_module, "get_email_service", lambda: email_service)

    response = _create_lead(client, email="prospect@example.com")

    assert len(email_service.prospect_calls) == 1
    assert email_service.prospect_calls[0]["email"] == "prospect@example.com"
    assert len(email_service.internal_calls) == 1
    assert email_service.internal_calls[0]["email"] == "prospect@example.com"
    assert email_service.internal_calls[0]["submitted_at"] is not None
    assert config_module.settings.internal_notification_email == "lianne.cha@gmail.com"


def test_lead_creation_preserves_lead_when_email_sending_fails(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.api.leads as leads_module

    class FailingEmailService(DummyEmailService):
        def send_prospect_confirmation(self, **kwargs: Any) -> None:
            raise RuntimeError("email provider unavailable")

        def send_internal_notification(self, **kwargs: Any) -> None:
            raise RuntimeError("email provider unavailable")

    monkeypatch.setattr(leads_module, "get_email_service", lambda: FailingEmailService())

    response = _create_lead(client, email="email-failure@example.com")

    assert response["email"] == "email-failure@example.com"


def test_invalid_resume_content_type_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/leads",
        data={"first_name": "Ada", "last_name": "Lovelace", "email": "bad@example.com"},
        files={"resume": ("resume.txt", b"plain text", "text/plain")},
    )

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_internal_lead_list_requires_auth(client: TestClient) -> None:
    _create_lead(client)

    response = client.get("/api/leads")

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing authorization credentials"


def test_internal_lead_list_rejects_invalid_bearer_token(client: TestClient) -> None:
    _create_lead(client)

    response = client.get(
        "/api/leads",
        headers={"Authorization": "Bearer not-the-token"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing authorization credentials"


def test_internal_lead_list_succeeds_with_auth(client: TestClient) -> None:
    created = _create_lead(client, email="staff@example.com")

    response = client.get(
        "/api/leads",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert any(item["id"] == created["id"] for item in payload)


def test_internal_lead_list_accepts_allowed_google_id_token(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.core.security as security_module

    created = _create_lead(client, email="google@example.com")
    config_module.settings.google_client_id = "google-client-id"
    config_module.settings.internal_allowed_emails = "staff@example.com"

    monkeypatch.setattr(
        security_module,
        "verify_google_id_token",
        lambda token: {"email": "staff@example.com", "email_verified": True},
    )

    response = client.get(
        "/api/leads",
        headers={"Authorization": "Bearer google-id-token"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert any(item["id"] == created["id"] for item in payload)


def test_internal_lead_list_rejects_invalid_google_id_token(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.core.security as security_module

    _create_lead(client, email="google-invalid@example.com")
    config_module.settings.google_client_id = "google-client-id"
    monkeypatch.setattr(
        security_module,
        "verify_google_id_token",
        lambda token: (_ for _ in ()).throw(ValueError("invalid token")),
    )

    response = client.get(
        "/api/leads",
        headers={"Authorization": "Bearer google-id-token"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing authorization credentials"


def test_internal_lead_list_rejects_unallowed_google_identity(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.core.security as security_module

    _create_lead(client, email="google-denied@example.com")
    config_module.settings.google_client_id = "google-client-id"
    config_module.settings.internal_allowed_email_domain = "example.com"

    monkeypatch.setattr(
        security_module,
        "verify_google_id_token",
        lambda token: {"email": "outsider@other.com", "email_verified": True},
    )

    response = client.get(
        "/api/leads",
        headers={"Authorization": "Bearer google-id-token"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Google account is not allowed for internal access"


def test_internal_status_update_changes_pending_lead_to_reached_out_and_sets_timestamp(client: TestClient) -> None:
    created = _create_lead(client, email="status@example.com")

    response = client.patch(
        f"/api/leads/{created['id']}/status",
        headers={"Authorization": "Bearer test-token"},
        json={"status": LeadStatus.REACHED_OUT.value},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == LeadStatus.REACHED_OUT.value
    assert payload["id"] == created["id"]
    assert payload["reached_out_at"] is not None
    parsed = datetime.fromisoformat(payload["reached_out_at"])
    assert parsed.tzinfo is not None


def test_internal_status_update_can_move_reached_out_lead_back_to_pending(client: TestClient) -> None:
    created = _create_lead(client, email="status-revert@example.com")
    headers = {"Authorization": "Bearer test-token"}

    reached_response = client.patch(
        f"/api/leads/{created['id']}/status",
        headers=headers,
        json={"status": LeadStatus.REACHED_OUT.value},
    )
    assert reached_response.status_code == 200

    pending_response = client.patch(
        f"/api/leads/{created['id']}/status",
        headers=headers,
        json={"status": LeadStatus.PENDING.value},
    )

    assert pending_response.status_code == 200
    payload = pending_response.json()
    assert payload["status"] == LeadStatus.PENDING.value
    assert payload["reached_out_at"] is None


def test_send_email_requires_auth(client: TestClient) -> None:
    created = _create_lead(client, email="send-auth@example.com")

    response = client.post(f"/api/leads/{created['id']}/send-email")

    assert response.status_code == 401


def test_send_email_returns_404_for_missing_lead(client: TestClient) -> None:
    response = client.post(
        "/api/leads/999999/send-email",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Lead not found"


def test_send_email_sends_to_lead_without_changing_status(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.api.leads as leads_module

    email_service = RecordingEmailService()
    monkeypatch.setattr(leads_module, "get_email_service", lambda: email_service)
    created = _create_lead(client, email="follow-up@example.com")

    response = client.post(
        f"/api/leads/{created['id']}/send-email",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    assert response.json()["detail"] == "Follow-up email sent"
    assert email_service.follow_up_calls == [{"first_name": "Ada", "email": "follow-up@example.com"}]

    leads = client.get("/api/leads", headers={"Authorization": "Bearer test-token"}).json()
    sent_lead = next(item for item in leads if item["id"] == created["id"])
    assert sent_lead["status"] == LeadStatus.PENDING.value


def test_internal_delete_requires_auth(client: TestClient) -> None:
    created = _create_lead(client, email="delete-auth@example.com")

    response = client.delete(f"/api/leads/{created['id']}")

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing authorization credentials"


def test_internal_delete_removes_lead_and_resume_file(client: TestClient) -> None:
    created = _create_lead(client, email="delete@example.com")

    db = database_module.SessionLocal()
    try:
        lead = db.get(Lead, created["id"])
        assert lead is not None
        resume_path = Path(lead.resume_storage_path)
        assert resume_path.exists()

        response = client.delete(
            f"/api/leads/{created['id']}",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 200
        assert response.json()["detail"] == "Lead deleted"
        db.expire_all()
        assert db.get(Lead, created["id"]) is None
        assert not resume_path.exists()
    finally:
        db.close()


def test_internal_delete_missing_lead_returns_404(client: TestClient) -> None:
    response = client.delete(
        "/api/leads/999999",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Lead not found"
