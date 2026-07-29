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

Local email delivery uses the console provider by default. Messages are printed to the terminal so the backend can be exercised locally without configuring a real mail provider.

To send real emails with Gmail SMTP, set these values in `apps/api/.env` and restart the backend:

```text
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=lianne.cha@gmail.com
SMTP_PASSWORD=<gmail-app-password>
EMAIL_FROM=Alma <lianne.cha@gmail.com>
INTERNAL_NOTIFICATION_EMAIL=lianne.cha@gmail.com
```

`SMTP_PASSWORD` must be a Gmail App Password, not the normal Google password.

Resend is also supported if you have a verified sending domain:

```text
EMAIL_PROVIDER=resend
RESEND_API_KEY=<your-resend-api-key>
EMAIL_FROM=Alma <onboarding@your-verified-domain.com>
INTERNAL_NOTIFICATION_EMAIL=lianne.cha@gmail.com
```

`EMAIL_FROM` must be a verified sender in Resend.

## Internal auth

Internal endpoints require an Authorization header containing a verified Google ID token. The public lead submission endpoint remains open and does not require authentication.

## Health check

Once running, visit:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status": "ok"}
```
