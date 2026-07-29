# System Design

## Goal

This application supports a simple lead intake workflow for Alma. Public prospects can submit their contact information and resume/CV, and authenticated internal users can review those leads and manually mark them as reached out.

The core workflow is intentionally narrow:

1. A prospect submits first name, last name, email, and resume/CV.
2. The backend persists the lead and uploaded resume metadata.
3. The backend sends local console email notifications to the prospect and internal team.
4. An internal user views submitted leads in an authenticated dashboard.
5. After manual outreach, the internal user marks the lead as `REACHED_OUT`.

## Requirements Interpreted

The prompt asks for an application that can create, get, and update leads. In this implementation:

- `POST /api/leads` creates a public lead submission.
- `GET /api/leads` returns submitted leads for authenticated internal users.
- `PATCH /api/leads/{lead_id}/status` updates a lead status for authenticated internal users.
- `GET /api/leads/{lead_id}/resume` downloads a lead's stored resume for authenticated internal users.
- `DELETE /api/leads/{lead_id}` removes a lead and its stored resume file for authenticated internal users.

The required lead fields are first name, last name, email, and resume/CV. Each lead also has a status that starts as `PENDING` and can transition to `REACHED_OUT` only through a manual internal action.

## Architecture

```text
Next.js frontend
  ├─ public intake form
  └─ internal dashboard

FastAPI backend
  ├─ request validation
  ├─ lead APIs
  ├─ bearer-token internal auth
  ├─ SQLite persistence
  ├─ local resume storage
  └─ console email provider
```

The repository is organized as a small monorepo:

- `apps/api`: FastAPI backend
- `apps/web`: Next.js frontend
- `docs`: design and coding-agent usage notes
- `storage`: local development storage

This keeps frontend, backend, and documentation clearly separated while avoiding unnecessary deployment or package-management complexity for the take-home.

## Data Model

The main domain model is `Lead`.

Stored fields:

- `id`: database primary key
- `first_name`: required prospect first name
- `last_name`: required prospect last name
- `email`: required prospect email, indexed
- `resume_original_filename`: original uploaded filename for display
- `resume_content_type`: MIME type used for validation and future download behavior
- `resume_storage_path`: local path to the stored file
- `status`: `PENDING` or `REACHED_OUT`
- `created_at`: submission timestamp
- `updated_at`: last update timestamp
- `reached_out_at`: timestamp for manual internal follow-up

The database stores resume metadata, not resume file bytes. The file itself is saved to local storage. This keeps SQLite records small and mirrors a production design where files would live in object storage.

## API Design

### `GET /health`

Public health check used to verify the API is running.

### `POST /api/leads`

Public endpoint for prospect submissions. It accepts `multipart/form-data`:

- `first_name`
- `last_name`
- `email`
- `resume`

The endpoint validates form fields, saves the resume, persists the lead, sends console email notifications, and returns the created lead. The created lead starts as `PENDING`.

### `GET /api/leads`

Authenticated internal endpoint. It returns all leads ordered newest-first.

For this take-home, the list is intentionally unpaginated because the expected dataset is small. In production, this would need pagination and likely status/search filters.

### `PATCH /api/leads/{lead_id}/status`

Authenticated internal endpoint. It accepts:

```json
{"status":"REACHED_OUT"}
```

The endpoint finds the lead, returns `404` if missing, and transitions `PENDING` leads to `REACHED_OUT`. If the lead is already `REACHED_OUT`, the endpoint treats the request as idempotent success.

### `DELETE /api/leads/{lead_id}`

Authenticated internal endpoint. It deletes the lead database row and removes the associated local resume file if it still exists. Missing leads return `404`.

## State Workflow

The lead workflow is deliberately small:

```text
PENDING -> REACHED_OUT
```

New leads start as `PENDING` by default. Automatic submission emails do not change the lead status. A lead becomes `REACHED_OUT` only when an authenticated internal user manually clicks `Mark reached out` after actual follow-up.

The status update schema requires clients to explicitly send a status field. Empty request bodies are rejected so state-changing requests must be intentional.

## Persistence and File Storage

SQLite is used for local persistence because it is durable, simple to run, and requires no external service. This makes local review straightforward and is a practical choice given the assignment's timeframe.

Resume/CV files are stored on the local filesystem under the configured `RESUME_STORAGE_DIR`. The storage service:

- accepts PDF, DOC, and DOCX uploads
- enforces a 5 MB size limit
- sanitizes filenames
- prefixes stored filenames with UUIDs
- returns metadata for the database

Production changes:

- Replace SQLite with Postgres.
- Replace local file storage with S3, GCS, or similar object storage.
- Serve resumes through signed URLs or object-storage-backed authenticated downloads.
- Add migrations with Alembic.

## Email Design

The application has an email service abstraction with a local console provider. On lead creation, the backend sends:

- a confirmation email to the prospect
- a notification email to the internal team

In local development, messages are printed to the FastAPI terminal. This keeps the app runnable without API keys or sender/domain verification.

Email sending happens after the lead is saved. If local email sending fails, the lead is not lost; the error is logged and the API still returns the saved lead. In production, email delivery should move to an asynchronous job with retries.

Production changes:

- Add a provider such as Resend, SendGrid, SES, or SMTP.
- Move email sending to a background queue.
- Track notification delivery status if the product needs it.

## Auth Design

The public lead submission endpoint is intentionally unauthenticated. Internal lead review, status update, and resume download endpoints require:

```text
Authorization: Bearer <INTERNAL_AUTH_TOKEN>
```

This bearer-token approach is intentionally simple. It satisfies the requirement that the internal UI be guarded by auth while keeping local setup easy for reviewers.

Production changes:

- Use SSO/OIDC through a provider such as Auth0, Clerk, WorkOS, Google Workspace, or Microsoft Entra ID.
- Add roles/permissions for internal users.
- Prefer secure cookies or short-lived tokens depending on deployment model.

## Frontend Design

The frontend is a Next.js app with two routes:

- `/`: public prospect intake form
- `/admin`: internal lead dashboard

The UI is inspired by Alma's public site: deep green accents, pale green surfaces, warm off-white background, rounded controls, and a calm operational dashboard style.

Public form decisions:

- The first screen is the actual intake workflow, not a marketing landing page.
- Prospects provide only required lead fields and resume/CV.
- Prospects do not choose status.
- Success and error states are visible inline.

Internal dashboard decisions:

- The dashboard stores a local token in `localStorage` for the take-home.
- Leads are shown with counts for total, pending, and reached out.
- `PENDING` and `REACHED_OUT` are displayed as badges.
- The action button says `Mark reached out` to distinguish manual attorney outreach from automatic submission emails.
- Resume filenames in the dashboard are clickable and trigger an authenticated download for the internal user.
- Each lead row also includes a `Delete` action that removes the lead and its uploaded resume file after confirmation.

## Validation and Error Handling

Validation is split by responsibility:

- Pydantic validates first name, last name, email, and status update payloads.
- FastAPI validates required form/file fields.
- The resume storage service validates file type, filename, and file size.
- Internal routes validate bearer-token auth.

Expected error responses:

- `400`: unsupported resume type or invalid upload
- `401`: missing or invalid internal auth
- `404`: lead not found
- `422`: invalid request data, such as malformed email or unsupported status

## Testing

The backend includes focused pytest coverage for the core workflow:

- public lead creation with PDF upload returns `PENDING`
- invalid resume content type is rejected
- internal lead list requires auth
- internal lead list succeeds with auth
- internal status update changes `PENDING` to `REACHED_OUT` and sets `reached_out_at`
- internal lead delete requires auth, removes the database row and resume file, and returns `404` for missing leads

Tests use temporary SQLite databases and temporary resume storage directories so they do not mutate local development data.

## Tradeoffs and Future Improvements

Intentional tradeoffs for the take-home:

- SQLite instead of Postgres
- local filesystem storage instead of object storage
- console email instead of real email delivery
- bearer-token internal auth instead of SSO/OIDC
- no pagination/filtering on the internal lead list
- no advanced resume preview, virus scanning, or object-storage-backed download flow
- no Alembic migrations

These choices keep the implementation small, easy to run, and complete end to end. The code is structured so the higher-fidelity production pieces can be swapped in behind existing boundaries.
