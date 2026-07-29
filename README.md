# Alma Lead Intake

A small full-stack lead intake application for the Alma take-home assignment.

## Features

- Public lead submission form
- Resume/CV upload
- Lead persistence with SQLite
- Email notifications to the prospect and internal team on submission
- Manual follow-up email action from the internal dashboard
- Internal dashboard with Google OAuth
- Manual lead status transition between `PENDING` and `REACHED_OUT`
- Authenticated resume download for internal users

## Tech Stack

- Backend: FastAPI, SQLAlchemy, SQLite, Pydantic
- Frontend: Next.js, TypeScript
- Tests: pytest

## Project Structure

- `apps/api`: FastAPI backend
- `apps/web`: Next.js frontend
- `docs`: design and coding-agent usage notes
- `storage`: local development storage

## Requirements

- Python 3.11+
- Node.js 18+
- npm

## Run the App

### 1. Start the Backend

From the repository root:

```bash
cd apps/api
cp .env.example .env
pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok"}
```

### 2. Start the Frontend

In a second terminal:

```bash
cd apps/web
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

### 3. Open the Internal Dashboard

Open:

```text
http://localhost:3000/admin
```

The dashboard requires Google login. The currently verified internal emails are:

```text
lianne.cha@gmail.com
shuo@tryalma.ai
```

### Google OAuth Setup

The internal dashboard uses Google OAuth when credentials are configured. OAuth secrets are intentionally not committed to this repository. To test Google sign-in, create local env files in your own checkout using the provided Google OAuth client ID and client secret.

Create `apps/web/.env.local` in your local copy:

```text
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=<random-secret>
GOOGLE_CLIENT_ID=<provided-google-oauth-client-id>
GOOGLE_CLIENT_SECRET=<provided-google-oauth-client-secret>
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

Create or update `apps/api/.env` with the same Google client ID and at least one allowed reviewer email:

```text
GOOGLE_CLIENT_ID=<provided-google-oauth-client-id>
INTERNAL_ALLOWED_EMAILS=lianne.cha@gmail.com,shuo@tryalma.ai
INTERNAL_ALLOWED_EMAIL_DOMAIN=
```

The provided Google OAuth client is configured for local development with:

```text
http://localhost:3000
```

as the JavaScript origin and:

```text
http://localhost:3000/api/auth/callback/google
```

as the redirect URI.

Do not commit `apps/web/.env.local` or `apps/api/.env`; both are ignored because they contain local credentials.

After Google sign-in, the frontend sends the Google ID token to the backend:

```text
Authorization: Bearer <google-id-token>
```

The backend verifies the token signature and audience, requires `email_verified=true`, and allows only configured emails or the configured email domain.

## End-to-End Workflow

1. Start the backend.
2. Start the frontend.
3. Open `http://localhost:3000`.
4. Submit first name, last name, email, and a PDF/DOC/DOCX resume.
5. Confirm a success message appears.
6. Confirm the app sends or prints a confirmation email to the prospect and a notification email to `lianne.cha@gmail.com`, depending on the configured email provider.
7. Open `http://localhost:3000/admin`.
8. Sign in with one of the verified Google accounts.
9. Confirm the lead appears as `PENDING`.
10. Click `Mark reached out`.
11. Confirm the lead changes to `REACHED_OUT`.
12. In the admin dashboard, click the resume filename to download the uploaded resume.
13. Use the `Delete` action in the admin dashboard to remove a lead and its uploaded resume file.
14. Use `Send email` on a lead to send a follow-up message without changing its status.

## Tests

The backend test suite covers the core lead workflow, including submission emails, the default attorney recipient, internal auth enforcement, authenticated follow-up email sending, status preservation, and authenticated lead deletion.

From `apps/api`:

```bash
pytest
```

Expected result:

```text
22 passed
```

## Design Notes

See `docs/DESIGN.md`.

For Alma-inspired visual direction, see `docs/ALMA_STYLE_GUIDE.md`.

## Local Development Notes

- SQLite database files are ignored by Git.
- Uploaded resumes are stored locally and ignored by Git.
- OAuth credentials live only in local `.env` files and should be shared out-of-band if a reviewer needs the exact same Google client.
- Email delivery defaults to a console provider for local development, with Gmail SMTP and Resend available through environment configuration.
- Lead creation emails the prospect and the configurable internal recipient, which defaults to `lianne.cha@gmail.com`. The dashboard's `Send email` action sends a manual follow-up to the selected lead.
- Configure `INTERNAL_NOTIFICATION_EMAIL` in `apps/api/.env` to change the attorney recipient. Keep provider credentials in local environment variables; the default console provider requires none.
- Production would use Postgres, object storage, queued email delivery, and organization-managed SSO/groups/roles.

## Real Email Delivery

By default, emails are printed in the FastAPI terminal. To send real emails without a custom domain, configure Gmail SMTP in `apps/api/.env`:

```text
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=lianne.cha@gmail.com
SMTP_PASSWORD=<gmail-app-password>
EMAIL_FROM=Alma <lianne.cha@gmail.com>
INTERNAL_NOTIFICATION_EMAIL=lianne.cha@gmail.com
```

`SMTP_PASSWORD` must be a Gmail App Password, not the normal Google account password. The Gmail account must have 2-Step Verification enabled before Google will let you create an app password. After updating `.env`, restart the backend. New lead submissions will send a real email to the prospect and a real attorney notification to `INTERNAL_NOTIFICATION_EMAIL`; the dashboard's `Send email` button will send a real follow-up email to that lead.

Resend is also supported if you have a verified sending domain:

```text
EMAIL_PROVIDER=resend
RESEND_API_KEY=<your-resend-api-key>
EMAIL_FROM=Alma <onboarding@your-verified-domain.com>
INTERNAL_NOTIFICATION_EMAIL=lianne.cha@gmail.com
```
