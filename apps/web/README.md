# Alma frontend

## Run locally

1. Install dependencies:
   ```bash
   cd apps/web
   npm install
   ```
2. Start the backend from the API app:
   ```bash
   cd apps/api
   python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
3. Start the frontend:
   ```bash
   cd apps/web
   npm run dev
   ```
4. Open the app at http://localhost:3000.

## Environment

The frontend uses the backend base URL from NEXT_PUBLIC_API_BASE_URL. If you need to point at a different backend, set:

```bash
export NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

The default is http://127.0.0.1:8000.
