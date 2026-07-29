# Backend API

This directory contains the initial FastAPI backend for the Alma lead intake take-home assignment.

## Run locally

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the API:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Database

The backend uses SQLite locally by default. The connection string can be changed in the .env file via DATABASE_URL if you want to point at a different database later.

## Resume storage

Resume uploads are stored locally under RESUME_STORAGE_DIR during development. The service validates allowed content types and file size before saving files to disk.

## Email

Local email delivery uses the console provider. Messages are printed to the terminal so the backend can be exercised locally without configuring a real mail provider.

Real email delivery is intentionally deferred as an optional enhancement. The provider abstraction allows a production service like Resend, SendGrid, or SES to be added later through environment configuration without changing lead submission logic.

## Internal auth

Internal endpoints will require an Authorization header in the form `Bearer <INTERNAL_AUTH_TOKEN>`. The public lead submission endpoint remains open and does not require authentication.

Real authentication is intentionally deferred as an optional enhancement. The bearer-token dependency keeps local setup simple for reviewers, while a production application would use SSO/OAuth/OIDC through a provider such as Auth0, Clerk, WorkOS, Google Workspace, or Microsoft Entra ID.

## Health check

Once running, visit:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status": "ok"}
```
