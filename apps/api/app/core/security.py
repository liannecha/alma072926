from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token

from app.core.config import settings

bearer_scheme = HTTPBearer(auto_error=False)


def _auth_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing authorization credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _parse_allowed_emails(value: str) -> set[str]:
    return {email.strip().lower() for email in value.split(",") if email.strip()}


def _is_allowed_google_email(email: str) -> bool:
    normalized_email = email.strip().lower()
    allowed_emails = _parse_allowed_emails(settings.internal_allowed_emails)
    if normalized_email in allowed_emails:
        return True

    allowed_domain = settings.internal_allowed_email_domain.strip().lower().lstrip("@")
    if allowed_domain:
        return normalized_email.endswith(f"@{allowed_domain}")

    return False


def verify_google_id_token(token: str) -> dict[str, Any]:
    if not settings.google_client_id:
        raise ValueError("Google OAuth is not configured")

    payload = id_token.verify_oauth2_token(token, GoogleRequest(), settings.google_client_id)
    if not isinstance(payload, dict):
        raise ValueError("Invalid Google token payload")
    return payload


def require_internal_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> None:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _auth_error()

    token = credentials.credentials
    if settings.internal_auth_token and token == settings.internal_auth_token:
        return

    try:
        google_payload = verify_google_id_token(token)
    except Exception as exc:
        raise _auth_error() from exc

    email = str(google_payload.get("email") or "")
    email_verified = google_payload.get("email_verified") is True or google_payload.get("email_verified") == "true"
    if not email or not email_verified:
        raise _auth_error()

    if not _is_allowed_google_email(email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Google account is not allowed for internal access",
        )
