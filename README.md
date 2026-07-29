# Alma Lead Intake

A small full-stack lead intake application for the Alma take-home assignment.

## Features

- Public lead submission form
- Resume/CV upload
- Lead persistence with SQLite
- Console email notifications to the prospect and internal team
- Internal authenticated dashboard
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

Default local token:

```text
change-me
```

This comes from `INTERNAL_AUTH_TOKEN` in `apps/api/.env.example`.

Internal API requests use:

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
8. Enter the internal token.
9. Confirm the lead appears as `PENDING`.
10. Click `Mark reached out`.
11. Confirm the lead changes to `REACHED_OUT`.
12. In the admin dashboard, click the resume filename to download the uploaded resume.

## Tests

The backend test suite covers the core lead workflow: public lead creation with a resume upload, invalid resume rejection, internal auth enforcement, authenticated lead listing, and status transition from `PENDING` to `REACHED_OUT`.

From `apps/api`:

```bash
pytest
```

Expected result:

```text
5 passed
```

## Design Notes

See `docs/DESIGN.md`.

## Local Development Notes

- SQLite database files are ignored by Git.
- Uploaded resumes are stored locally and ignored by Git.
- Email delivery uses a console provider for local development.
- Production would use Postgres, object storage, real email delivery, and SSO/OIDC auth.
