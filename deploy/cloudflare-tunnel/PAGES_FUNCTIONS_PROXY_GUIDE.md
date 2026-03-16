# Cloudflare Pages Functions Same-Origin Proxy Guide

This guide explains how the current `frontend/functions/api/[[path]].js` proxy works and how to reuse the same pattern in other projects.

## 1. What This Solves

- Frontend and API share the same origin
- The browser only talks to `/api/*`
- Pages Functions forwards requests to the real backend
- You do not need a separate `workers.dev` entrypoint

## 2. File Location

In this repository, the Pages root is `frontend`, so the proxy file lives here:

- [frontend/functions/api/[[path]].js](/Users/collie/workspace/video-subtitle-stitch/frontend/functions/api/[[path]].js)

## 3. Core Rule

The current proxy removes the incoming `/api` prefix before forwarding.

That means:

- Request from browser: `/api/v1/models`
- Forwarded upstream path: `/v1/models`

So the upstream base must usually end with `/api`, for example:

- `BACKEND_ORIGIN=https://your-backend.example.com/api`

## 4. What The Proxy Handles

- `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD`, `OPTIONS`
- Query strings
- Request headers
- Request body
- CORS response headers
- `X-Forwarded-Proto` and `X-Forwarded-Host`

## 5. Common Problems

### 404 On `/api/v1/models`

Most common cause:
- `BACKEND_ORIGIN` does not end with `/api`

### 500 During Upload

Most common cause:
- the backend work directory is missing or not writable

### 502 From Pages

Most common cause:
- the backend origin is unreachable

## 6. Reuse Checklist

When using this pattern in another project:

1. Put `[[path]].js` under that Pages root
2. Standardize frontend API calls to `/api`
3. Align `BACKEND_ORIGIN` with the path rewrite rule
4. Verify health, list, upload, and authenticated endpoints
