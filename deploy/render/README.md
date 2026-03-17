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
- Render can now start without bundled local whisper model files
- If `/app/models` does not contain a local model, the backend will download the requested model on first use

## 2. Render Create Service Form

Fill the create page according to the fields visible in the current Render UI.

### Top Section

- `Source Code`: your connected repository
  Current example in your screenshot: `HuiHongDuan / video-subtitle-stitch`
- `Name`: `video-subtitle-stitch`
  You can keep this as-is, or rename it to `video-subtitle-backend` if you want the service purpose to be more explicit
- `Language`: `Docker`
- `Branch`: `cloud_flare_test`
  Use the branch you actually want Render to deploy from
- `Region`: `Singapore (Southeast Asia)`
- `Root Directory`: leave empty
  This repo should build from the repository root
- `Dockerfile Path`: `backend/Dockerfile`

### Environment Variables Section

Add these one by one:

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

### Advanced Section

Use these values:

- `Health Check Path`: `/healthz`
- `Registry Credential`: `No credential`
- `Docker Build Context Directory`: `.`
- `Dockerfile Path`: `backend/Dockerfile`
- `Docker Command`: leave empty
- `Pre-Deploy Command`: leave empty
- `Auto-Deploy`: `On Commit`

### Build Filters

For the first deployment, the simplest choice is:

- `Included Paths`: leave empty
- `Ignored Paths`: leave empty

This avoids accidentally blocking deploys while you are still validating the setup.

If later you want backend-only changes to trigger deploys, you can narrow this down.

### Deploy Button

After filling the page, click:

- `Deploy Web Service`

## 3. After The Service Is Created

Once the Render service exists, open its settings and add one persistent disk.

### Disk

Add:

- `Mount Path`: `/data`
- `Disk Size`: `5 GB`

Why this matters:
- uploads and output files need writable persistent storage
- this matches the app setting `WORKDIR_ROOT=/data/workdir`
- keeping a persistent disk also helps if the runtime or library caches downloaded model data outside the image

## 4. Why These Values Match This Repo

- The backend listens on port `8000`
- The Docker image already starts `uvicorn`
- Health check route is `/healthz`
- The backend writes files under `WORKDIR_ROOT`
- The service can use local whisper models if present, or auto-download standard models such as `small`

Relevant files:
- [backend/Dockerfile](/Users/collie/workspace/video-subtitle-stitch/backend/Dockerfile)
- [backend/app/main.py](/Users/collie/workspace/video-subtitle-stitch/backend/app/main.py)
- [docker-compose.yml](/Users/collie/workspace/video-subtitle-stitch/docker-compose.yml)

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

Note about the first real transcription job:
- the first request using `small` may take noticeably longer because Render may need to download the model before transcription starts

## 6. Current Page Cheat Sheet

If you want a one-screen summary matching the fields shown in your screenshots:

- `Name`: `video-subtitle-stitch`
- `Language`: `Docker`
- `Branch`: `cloud_flare_test`
- `Region`: `Singapore (Southeast Asia)`
- `Root Directory`: leave empty
- `Dockerfile Path`: `backend/Dockerfile`
- `Health Check Path`: `/healthz`
- `Docker Build Context Directory`: `.`
- `Docker Command`: leave empty
- `Pre-Deploy Command`: leave empty
- `Auto-Deploy`: `On Commit`

Environment variables:

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
