# Alma Lead Intake

A small full-stack lead intake application for the Alma take-home assignment.

## Features

- Public lead submission form
- Resume/CV upload
- Lead persistence with SQLite
- Console email notifications to the prospect and internal team
- Internal dashboard with Google OAuth
- Manual lead status transition from `PENDING` to `REACHED_OUT`
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

## Backend Setup

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

## Frontend Setup

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

If the API is running on a different port, set `NEXT_PUBLIC_API_BASE_URL` before starting the frontend.

macOS/Linux:

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8001 npm run dev
```

Windows PowerShell:

```powershell
$env:NEXT_PUBLIC_API_BASE_URL="http://127.0.0.1:8001"
npm run dev
```

Or create `apps/web/.env.local`:

```text
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8001
```

Then run:

```bash
npm run dev
```

## Internal Dashboard

Open:

```text
http://localhost:3000/admin
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
INTERNAL_ALLOWED_EMAILS=<your-google-email@example.com>
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

### Local Fallback

If Google OAuth env vars are missing, `/admin` shows a local token fallback for reviewers. Default local token:

```text
change-me
```

This comes from `INTERNAL_AUTH_TOKEN` in `apps/api/.env.example`.

Fallback internal API requests use:

```text
Authorization: Bearer change-me
```

## End-to-End Workflow

1. Start the backend.
2. Start the frontend.
3. Open `http://localhost:3000`.
4. Submit first name, last name, email, and a PDF/DOC/DOCX resume.
5. Confirm a success message appears.
6. Confirm the backend terminal prints two console emails.
7. Open `http://localhost:3000/admin`.
8. Sign in with Google, or use the local token fallback if Google OAuth is not configured.
9. Confirm the lead appears as `PENDING`.
10. Click `Mark reached out`.
11. Confirm the lead changes to `REACHED_OUT`.
12. In the admin dashboard, click the resume filename to download the uploaded resume.
13. Use the `Delete` action in the admin dashboard to remove a lead and its uploaded resume file.

## Tests

The backend test suite covers the core lead workflow: public lead creation with a resume upload, invalid resume rejection, internal auth enforcement, authenticated lead listing, Google ID token authorization behavior, status transition from `PENDING` to `REACHED_OUT`, and authenticated lead deletion.

From `apps/api`:

```bash
pytest
```

Expected result:

```text
12 passed
```

## Design Notes

See `docs/DESIGN.md`.

For Alma-inspired visual direction, see `docs/ALMA_STYLE_GUIDE.md`.

## Local Development Notes

- SQLite database files are ignored by Git.
- Uploaded resumes are stored locally and ignored by Git.
- OAuth credentials live only in local `.env` files and should be shared out-of-band if a reviewer needs the exact same Google client.
- Email delivery uses a console provider for local development.
- Production would use Postgres, object storage, real email delivery, and organization-managed SSO/groups/roles.
