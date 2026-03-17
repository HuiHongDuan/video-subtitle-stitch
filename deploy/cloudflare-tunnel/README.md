# Cloudflare Pages + Local Backend Through Tunnel

Target architecture:

```text
Browser
  -> Cloudflare Pages (frontend + Pages Functions)
  -> Cloudflare Tunnel
  -> Local Backend
```

This mode is best for temporary public demos and debugging the Cloudflare edge path without moving the backend off your machine.

## 1. Environment File

Use:
- [env/cloudflare-tunnel.example](/Users/collie/workspace/video-subtitle-stitch/env/cloudflare-tunnel.example)

Important values:
- `VITE_API_BASE_URL=/api`
- `BACKEND_ORIGIN=https://<your-tunnel-host>/api`

The `/api` suffix matters because the current Pages Function strips `/api` from the incoming path before forwarding.

## 2. Start Local Backend

```bash
mkdir -p backend/workdir
docker compose up -d --build backend
curl http://127.0.0.1:8000/healthz
```

## 3. Start Tunnel

Quick temporary tunnel:

```bash
cloudflared tunnel --url http://127.0.0.1:8000
```

Or use a named tunnel if you already created one in Cloudflare.

## 4. Pages Configuration

In Cloudflare Pages:

- `Root directory`: `frontend`
- `Build command`: `npm run build`
- `Build output directory`: `dist`

Pages variables:

- `VITE_API_BASE_URL=/api`
- `BACKEND_ORIGIN=https://<your-tunnel-host>/api`

## 5. Verification

Run in this order:

1. `curl http://127.0.0.1:8000/healthz`
2. `curl https://<your-tunnel-host>/healthz`
3. `curl https://<your-tunnel-host>/api/v1/models`
4. `curl https://<your-pages-project>.pages.dev/api/v1/models`
5. Open `https://<your-pages-project>.pages.dev`
6. Upload a small video and confirm end-to-end processing works

## 6. Typical Failure Cases

- `/api/v1/models` returns 404:
  `BACKEND_ORIGIN` is likely missing the `/api` suffix
- Upload returns 500:
  confirm `backend/workdir` exists and the backend can write to `WORKDIR_ROOT`
- `502 Bad Gateway` from Pages:
  the tunnel is down or the tunnel URL is wrong
