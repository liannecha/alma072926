# System Design

## Goal

This application supports a simple lead intake workflow for Alma. Public prospects can submit their contact information and resume/CV, and authenticated internal users can review those leads and manually mark them as reached out.

The core workflow is intentionally narrow:

1. A prospect submits first name, last name, email, and resume/CV.
2. The backend persists the lead and uploaded resume metadata.
3. The backend sends a confirmation to the prospect and a notification to the attorney/internal recipient.
4. An internal user views submitted leads in an authenticated dashboard.
5. After manual outreach, the internal user marks the lead as `REACHED_OUT`.

## Requirements Interpreted

The prompt asks for an application that can create, get, and update leads. In this implementation:

- `POST /api/leads` creates a public lead submission.
- `GET /api/leads` returns submitted leads for authenticated internal users.
- `PATCH /api/leads/{lead_id}/status` updates a lead status for authenticated internal users.
- `GET /api/leads/{lead_id}/resume` downloads a lead's stored resume for authenticated internal users.
- `DELETE /api/leads/{lead_id}` removes a lead and its stored resume file for authenticated internal users.
- `POST /api/leads/{lead_id}/send-email` sends a manual follow-up email to an authenticated lead.

The required lead fields are first name, last name, email, and resume/CV. Each lead starts as `PENDING` and can move between `PENDING` and `REACHED_OUT` through manual internal actions.

## Architecture

```text
Next.js frontend
  ├─ public intake form
  └─ internal dashboard

FastAPI backend
  ├─ request validation
  ├─ lead APIs
  ├─ Google ID token internal auth
  ├─ SQLite persistence
  ├─ local resume storage
  └─ email provider abstraction with console and Resend providers
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

The endpoint validates form fields, saves the resume, persists the lead, sends a confirmation to the prospect and a notification to the configured attorney recipient, and returns the created lead. The created lead starts as `PENDING`.

### `GET /api/leads`

Authenticated internal endpoint. It returns all leads ordered newest-first.

For this take-home, the list is intentionally unpaginated because the expected dataset is small. In production, this would need pagination and likely status/search filters.

### `PATCH /api/leads/{lead_id}/status`

Authenticated internal endpoint. It accepts:

```json
{"status":"REACHED_OUT"}
```

The endpoint finds the lead, returns `404` if missing, and supports both status transitions. Moving to `REACHED_OUT` records `reached_out_at`; moving back to `PENDING` clears it. Repeating either status update is idempotent.

### `DELETE /api/leads/{lead_id}`

Authenticated internal endpoint. It deletes the lead database row and removes the associated local resume file if it still exists. Missing leads return `404`.

### `POST /api/leads/{lead_id}/send-email`

Authenticated internal endpoint. It sends a simple Alma follow-up message to the lead's email address. Missing leads return `404`; sending this email does not change the lead status.

## State Workflow

The lead workflow is deliberately small:

```text
PENDING <-> REACHED_OUT
```

New leads start as `PENDING` by default. Automatic submission emails do not change the lead status. Internal users can manually mark a lead `REACHED_OUT` after follow-up or move it back to `PENDING` after confirmation.

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

The application has an email service abstraction with a local console provider plus SMTP and Resend providers for real delivery. On lead creation, the backend sends:

- a confirmation email to the prospect
- a notification email to the internal team

The internal recipient is configurable with `INTERNAL_NOTIFICATION_EMAIL` and defaults to `lianne.cha@gmail.com`. The internal dashboard also exposes a manual `Send email` action for individual follow-up messages.

In local development, messages are printed to the FastAPI terminal by default. When `EMAIL_PROVIDER=smtp`, the backend sends through an SMTP server such as Gmail's `smtp.gmail.com` using a local app password. When `EMAIL_PROVIDER=resend`, the backend posts to Resend's email API using `RESEND_API_KEY`; `EMAIL_FROM` must be a verified sender.

Email sending happens after the lead is saved. Prospect and attorney messages are attempted independently, so a failure in one does not prevent the other from being attempted. If email sending fails, the lead is not lost; the error is logged and the API still returns the saved lead. The local console provider prints messages unless a real provider is configured. In production, email delivery should move to an asynchronous job with retries.

Production changes:

- Move email sending to a background queue.
- Track notification delivery status if the product needs it.

## Auth Design

The public lead submission endpoint is intentionally unauthenticated. Internal lead review, status update, resume download, and delete endpoints require an `Authorization: Bearer <token>` header.

The primary internal dashboard flow uses Google OAuth through NextAuth/Auth.js on the frontend. After a successful Google sign-in, the frontend stores the Google ID token in the NextAuth JWT/session and passes that ID token to the FastAPI backend when calling internal APIs.

The backend verifies Google ID tokens with `google-auth`:

- token signature and issuer are validated by Google's verifier
- token audience must match `GOOGLE_CLIENT_ID`
- `email_verified` must be true
- the email must be listed in `INTERNAL_ALLOWED_EMAILS` or match `INTERNAL_ALLOWED_EMAIL_DOMAIN`

Missing or invalid bearer credentials return `401`. A valid Google identity that is not on the internal allowlist returns `403`.

Local Google OAuth configuration is intentionally env-driven:

- `apps/web/.env.local` holds `NEXTAUTH_URL`, `NEXTAUTH_SECRET`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `NEXT_PUBLIC_API_BASE_URL`.
- `apps/api/.env` holds the matching `GOOGLE_CLIENT_ID` plus `INTERNAL_ALLOWED_EMAILS` or `INTERNAL_ALLOWED_EMAIL_DOMAIN`.
- The Google OAuth client must allow `http://localhost:3000` as a JavaScript origin and `http://localhost:3000/api/auth/callback/google` as a redirect URI.
- Real OAuth credentials are not tracked in Git; reviewers should create their own client or receive credentials out-of-band.

Production changes:

- Use organization-managed SSO/OIDC through a provider such as Auth0, Clerk, WorkOS, Google Workspace, or Microsoft Entra ID.
- Use organization allowlists, groups, or role claims instead of hand-maintained env-var email lists.
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

- Google OAuth is the primary dashboard sign-in flow when `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are configured.
- The frontend exposes `/api/auth/google-enabled` so the admin page can confirm Google sign-in is configured.
- Leads are shown with counts for total, pending, and reached out.
- `PENDING` and `REACHED_OUT` are displayed as badges.
- The action button says `Mark reached out` to distinguish manual attorney outreach from automatic submission emails.
- Resume filenames in the dashboard are clickable and trigger an authenticated download for the internal user.
- Each lead row also includes a `Delete` action that removes the lead and its uploaded resume file after confirmation.
- Each lead row includes a `Send email` action for manual follow-up; this does not mark the lead as `REACHED_OUT`.

## Validation and Error Handling

Validation is split by responsibility:

- Pydantic validates first name, last name, email, and status update payloads.
- FastAPI validates required form/file fields.
- The resume storage service validates file type, filename, and file size.
- Internal routes validate a verified Google ID token for dashboard access.

Expected error responses:

- `400`: unsupported resume type or invalid upload
- `401`: missing or invalid internal auth
- `403`: valid Google identity that is not allowed for internal access
- `404`: lead not found
- `422`: invalid request data, such as malformed email or unsupported status

## Testing

The backend includes focused pytest coverage for the core workflow:

- public lead creation with PDF upload returns `PENDING`
- invalid resume content type is rejected
- internal lead list requires auth
- internal lead list rejects invalid bearer tokens
- internal lead list succeeds with auth
- internal lead list accepts a verified and allowed Google identity
- internal lead list rejects invalid Google ID tokens
- internal lead list rejects a verified but unallowed Google identity
- internal status update moves `PENDING` to `REACHED_OUT`, and can move it back to `PENDING` while clearing `reached_out_at`
- lead creation sends prospect and internal emails and preserves the lead if email sending fails
- authenticated follow-up email sends to the lead, rejects missing auth, returns `404` for a missing lead, and preserves `PENDING` status
- internal lead delete requires auth, removes the database row and resume file, and returns `404` for missing leads

Tests use temporary SQLite databases and temporary resume storage directories so they do not mutate local development data.

## Tradeoffs and Future Improvements

Intentional tradeoffs for the take-home:

- SQLite instead of Postgres
- local filesystem storage instead of object storage
- synchronous email sending instead of queued delivery tracking
- env-var email/domain allowlists instead of organization groups or roles
- no pagination/filtering on the internal lead list
- no advanced resume preview, virus scanning, or object-storage-backed download flow
- no Alembic migrations

These choices keep the implementation small, easy to run, and complete end to end. The code is structured so the higher-fidelity production pieces can be swapped in behind existing boundaries.
