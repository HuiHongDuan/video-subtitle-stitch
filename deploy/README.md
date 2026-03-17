# Deployment Modes

This repository supports three deployment modes without changing business code.

## Modes

### 1. Local

Use this during development.

- Frontend runs locally
- Backend runs locally
- API base points to `http://127.0.0.1:8000`

Guide:
- [deploy/local/README.md](/Users/collie/workspace/video-subtitle-stitch/deploy/local/README.md)

Env example:
- [env/local.example](/Users/collie/workspace/video-subtitle-stitch/env/local.example)

### 2. Cloudflare Pages + Local Backend Through Tunnel

Use this for temporary public demo or edge-proxy debugging.

- Frontend runs on Cloudflare Pages
- Pages Functions proxy `/api/*`
- Backend still runs on your local machine
- `BACKEND_ORIGIN` points to your tunnel URL and should end with `/api`

Guide:
- [deploy/cloudflare-tunnel/README.md](/Users/collie/workspace/video-subtitle-stitch/deploy/cloudflare-tunnel/README.md)

Proxy deep dive:
- [deploy/cloudflare-tunnel/PAGES_FUNCTIONS_PROXY_GUIDE.md](/Users/collie/workspace/video-subtitle-stitch/deploy/cloudflare-tunnel/PAGES_FUNCTIONS_PROXY_GUIDE.md)

Env example:
- [env/cloudflare-tunnel.example](/Users/collie/workspace/video-subtitle-stitch/env/cloudflare-tunnel.example)

### 3. Cloudflare Pages + Render Backend

Use this as the production-oriented deployment path.

- Frontend runs on Cloudflare Pages
- Backend runs on Render
- Pages Functions proxy `/api/*`
- `BACKEND_ORIGIN` points to the Render backend and should end with `/api`

Guide:
- [deploy/render/README.md](/Users/collie/workspace/video-subtitle-stitch/deploy/render/README.md)

Env example:
- [env/render.example](/Users/collie/workspace/video-subtitle-stitch/env/render.example)

### 4. GHCR Image Pipeline

Use this when you want GitHub Actions to build the backend image once and let Render or Koyeb pull that image directly.

Guide:
- [deploy/ghcr/README.md](/Users/collie/workspace/video-subtitle-stitch/deploy/ghcr/README.md)

### 5. Self-Hosted Backend Security

Use this when your backend runs on your own machine, VPS, or other self-managed compute platform and you want a practical security baseline.

Guide:
- [deploy/security/README.md](/Users/collie/workspace/video-subtitle-stitch/deploy/security/README.md)

## Recommended Usage

- Treat `local` as the development mode
- Treat `cloudflare-tunnel` as a temporary public-debug mode
- Treat `render` as the production deployment mode
- Treat `ghcr` as the registry/distribution layer for production backends

This keeps one codebase, one API shape, and one frontend behavior while isolating deployment differences into docs and environment configuration.
