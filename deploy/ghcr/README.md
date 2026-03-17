# GHCR Backend Image Deployment

This guide packages the backend into a Docker image, pushes it to GitHub Container Registry, and lets Render or Koyeb pull that image directly.

Target architecture:

```text
GitHub repository
  -> GitHub Actions
  -> GHCR image
  -> Render / Koyeb
  -> Cloudflare Pages proxy
```

## 1. Files Added For This Flow

- [backend/Dockerfile](/Users/collie/workspace/video-subtitle-stitch/backend/Dockerfile)
  now copies pre-downloaded model artifacts from `build-artifacts/models`
- [scripts/download_hf_model.py](/Users/collie/workspace/video-subtitle-stitch/scripts/download_hf_model.py)
  downloads the `small` model into the Docker build context
- [.github/workflows/backend-image.yml](/Users/collie/workspace/video-subtitle-stitch/.github/workflows/backend-image.yml)
  builds and publishes the backend image to GHCR
- [build-artifacts/models/.gitkeep](/Users/collie/workspace/video-subtitle-stitch/build-artifacts/models/.gitkeep)
  keeps the copy target directory present in the repository

## 2. What You Need To Change To Real Values

Open [.github/workflows/backend-image.yml](/Users/collie/workspace/video-subtitle-stitch/.github/workflows/backend-image.yml) and review these values.

### Branch Triggers

Current values:

```yaml
branches:
  - main
  - master
  - cloud_flare_test_clean
```

Change this if:
- your long-term default branch is not `main`
- you do not want images from `cloud_flare_test_clean`

### Image Name

Current value:

```yaml
IMAGE_NAME: ghcr.io/${{ github.repository_owner }}/video-subtitle-stitch-backend
```

This usually does not need to change.

Real expanded result will be:

```text
ghcr.io/<your-github-username>/video-subtitle-stitch-backend
```

### Hugging Face Model Repository

Current value:

```yaml
HF_MODEL_REPO: Systran/faster-whisper-small
```

Keep this if you want the image to contain the `small` model.

### Model Output Directory

Current value:

```yaml
MODEL_OUTPUT_DIR: build-artifacts/models/faster-whisper-small
```

Usually keep this unchanged.

## 3. GitHub Configuration

### Repository Permissions

This workflow uses:

- `contents: read`
- `packages: write`

That is already declared in the workflow file.

### Repository Secret

Only add this if your Hugging Face model source requires authentication:

- `HUGGINGFACE_HUB_TOKEN`

For public model downloads, you can leave this secret unset.

### GHCR Visibility

After the first successful push, open the package in GitHub and decide:

- public image: easiest for Render and Koyeb
- private image: requires registry credentials on Render or Koyeb

Recommended for easiest setup:

- make the backend image public first

## 4. How The Workflow Works

1. Checks out the repo
2. Installs Python and `huggingface_hub`
3. Downloads `small` into `build-artifacts/models/faster-whisper-small`
4. Logs in to `ghcr.io`
5. Builds the Docker image from [backend/Dockerfile](/Users/collie/workspace/video-subtitle-stitch/backend/Dockerfile)
6. Pushes tags such as:
   - branch name
   - git tag name
   - `sha-<commit>`
   - `latest` on the default branch

## 5. Render Configuration Using GHCR

In Render, choose image-based deployment instead of Git-based deployment.

Fill these with real values:

- `Image URL`:
  `ghcr.io/<your-github-username>/video-subtitle-stitch-backend:main`

If you want an exact immutable release, use:

- `ghcr.io/<your-github-username>/video-subtitle-stitch-backend:sha-<commit>`

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

Disk:

- `Mount Path`: `/data`
- `Disk Size`: `5 GB`

Health check:

- `/healthz`

Cloudflare Pages variable after Render is live:

```env
BACKEND_ORIGIN=https://<your-render-domain>.onrender.com/api
```

## 6. Koyeb Configuration Using GHCR

In Koyeb, create a service from an existing container image.

Use:

- `Image`: `ghcr.io/<your-github-username>/video-subtitle-stitch-backend:main`

Use the same runtime environment variables as Render.

If the image is private, configure registry credentials:

- username: your GitHub username
- password: a GitHub token with `read:packages`

## 7. Verification Order

1. Push a branch that triggers the workflow
2. Wait for `Publish Backend Image` to pass in GitHub Actions
3. Confirm the GHCR package exists
4. Deploy the image on Render or Koyeb
5. Verify:

```bash
curl https://<backend-domain>/healthz
curl https://<backend-domain>/api/v1/models
```

6. Update Cloudflare Pages `BACKEND_ORIGIN`
7. Verify:

```bash
curl https://<your-pages-domain>/api/v1/models
```

## 8. Notes

- This workflow keeps the repository free of large model binaries
- The image contains `small`, so runtime does not depend on first-request model download
- If you later want `medium` or `large`, keep them out of Git and switch the workflow download source instead
