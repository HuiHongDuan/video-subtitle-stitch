# Render Backend Deployment

This is the production-oriented deployment path for the current repository.

Target architecture:

```text
Browser
  -> Cloudflare Pages
  -> Pages Functions /api/*
  -> Render Web Service (FastAPI backend)
```

## 1. Environment File

Use:
- [env/render.example](/Users/collie/workspace/video-subtitle-stitch/env/render.example)

Important values:
- `VITE_API_BASE_URL=/api`
- `BACKEND_ORIGIN=https://<your-render-backend>.onrender.com/api`

## 2. Render Create Service

Use these values in Render:

- `Service Type`: `Web Service`
- `Environment`: `Docker`
- `Name`: `video-subtitle-backend`
- `Branch`: your production branch
- `Dockerfile Path`: `backend/Dockerfile`
- `Docker Build Context Directory`: `.`
- `Start Command`: leave empty
- `Health Check Path`: `/healthz`

## 3. Render Disk

Add one persistent disk:

- `Mount Path`: `/data`
- `Disk Size`: `5 GB`

## 4. Render Environment Variables

```env
APP_ENV=production
APP_HOST=0.0.0.0
APP_PORT=8000
CORS_ORIGINS=https://video-subtitle-stitch.pages.dev
MAX_UPLOAD_MB=500
DEFAULT_MODEL_SIZE=small
WORKDIR_ROOT=/data/workdir
ASR_MODEL_ROOT=/app/models
FONTSIZE_RATIO=0.032
FONTSIZE_MIN=14
FONTSIZE_MAX=40
MARGINV_RATIO=0.035
MARGINV_MIN=14
MARGINV_MAX=52
SUBTITLE_FONT_NAME=Noto Sans CJK SC
```

## 5. Deploy Verification

After Render deploys, verify:

1. `curl https://<your-render-backend>.onrender.com/healthz`
2. `curl https://<your-render-backend>.onrender.com/api/v1/models`

Then update Cloudflare Pages:

- `BACKEND_ORIGIN=https://<your-render-backend>.onrender.com/api`

Redeploy Pages and verify:

1. `curl https://<your-pages-project>.pages.dev/api/v1/models`
2. Open `https://<your-pages-project>.pages.dev`
3. Upload a small video and verify the full job flow

## 6. Why This Works With The Current Repo

- The backend already has `GET /healthz`
- The current Docker image already runs `uvicorn`
- The current app expects writable `WORKDIR_ROOT`
- The current repo already includes local whisper models under `backend/models`
