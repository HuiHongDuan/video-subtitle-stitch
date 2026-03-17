# Local Deployment

This mode runs both frontend and backend on your machine.
It supports two common cases:

- local-only access on the same machine
- LAN debugging from other devices on the same network

Target architecture:

```text
Browser
  -> Local Frontend (Vite)
  -> Local Backend (FastAPI)
```

## 1. Environment File

Use:
- [env/local.example](/Users/collie/workspace/video-subtitle-stitch/env/local.example)

Important value:
- `VITE_API_BASE_URL=http://127.0.0.1:8000/api`

If you want other devices on the same LAN to use your machine as the backend, do not use `127.0.0.1`.
Use your machine's LAN IP instead, for example:

- `VITE_API_BASE_URL=http://192.168.0.207:8000/api`
- `CORS_ORIGINS=http://127.0.0.1:3000,http://localhost:3000,http://192.168.0.207:3000`

## 2. Start Backend

### Option A: Native Python

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Option B: Docker

```bash
mkdir -p backend/workdir
docker compose up -d --build backend
```

## 3. Start Frontend

### Same Machine

```bash
cd frontend
npm install
VITE_API_BASE_URL=http://127.0.0.1:8000/api npm run dev
```

### LAN Debugging From Another Device

Replace `192.168.0.207` with your machine's real LAN IP:

```bash
cd frontend
npm install
VITE_API_BASE_URL=http://192.168.0.207:8000/api npm run dev
```

At the same time, make sure the backend allows the frontend origin:

```bash
CORS_ORIGINS=http://127.0.0.1:3000,http://localhost:3000,http://192.168.0.207:3000
```

If you prefer to keep using Docker for both frontend and backend, use the helper script:

```bash
./scripts/docker_up_lan.sh 192.168.0.207
```

If you omit the IP, the script will try to detect it automatically:

```bash
./scripts/docker_up_lan.sh
```

## 4. Verification

Run in this order:

1. `curl http://127.0.0.1:8000/healthz`
2. `curl http://127.0.0.1:8000/api/v1/models`
3. Open `http://127.0.0.1:3000`
4. Upload a small video
5. Confirm job creation, polling, and file downloads work

### LAN Verification

If you are testing from another phone, tablet, or computer on the same network:

1. Start backend with `APP_HOST=0.0.0.0`
2. Confirm from the host machine:
   `curl http://192.168.0.207:8000/healthz`
3. Start frontend with:
   `VITE_API_BASE_URL=http://192.168.0.207:8000/api`
4. Open this from another device:
   `http://192.168.0.207:3000`
5. Confirm the browser requests:
   `http://192.168.0.207:8000/api/v1/models`

With Docker, the same mode can be started in one step:

```bash
./scripts/docker_up_lan.sh 192.168.0.207
```

## 5. What Success Looks Like

- Backend health check returns `{"ok": true}`
- Models endpoint returns the model list
- Frontend can upload and start a job
- Completed jobs expose download links

## 6. Why LAN Mode Fails If You Use 127.0.0.1

- `127.0.0.1` always means "this device itself"
- On a second device, `127.0.0.1:8000` points to that second device, not your dev machine
- For LAN testing, both the frontend URL and backend API URL must use your dev machine's LAN IP
