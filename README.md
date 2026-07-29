# Alma Lead Intake

Take-home assignment for a lead intake workflow.

This repo is structured as a small full-stack application:

- `apps/api`: FastAPI backend
- `apps/web`: Next.js frontend
- `docs`: design and agent-usage notes
- `storage`: local development file storage

## Run the frontend

1. Start the backend:
   ```bash
   cd apps/api
   python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
2. In a second terminal, start the frontend:
   ```bash
   cd apps/web
   npm install
   npm run dev
   ```
3. Open http://localhost:3000.

The frontend reads its API base from NEXT_PUBLIC_API_BASE_URL and defaults to http://127.0.0.1:8000 if it is not set.
