# Cloudflare Pages + Local Backend Through Tunnel

Target architecture:

```text
Browser
  -> Cloudflare Pages (frontend + Pages Functions)
  -> Cloudflare Tunnel
  -> Local Backend
```

This mode is best for temporary public demos and debugging the Cloudflare edge path without moving the backend off your machine.

There are two ways to run it:

- Quick tunnel: no domain required, good for temporary testing
- Named tunnel with your own domain: stable hostname, better for long-term use

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

### Option A. Quick Temporary Tunnel

Use this when you want a fast temporary public URL and do not care if the hostname changes.

Command:

```bash
cloudflared tunnel --url http://127.0.0.1:8000
```

What you get:

- A random `https://<random>.trycloudflare.com`
- Good for temporary demos and debugging
- Not suitable for long-term backend origin configuration

Notes:

- The hostname changes when you restart
- Cloudflare documents quick tunnels as development/testing only
- Quick tunnels have a 200 concurrent request limit and do not support SSE

Official reference:
- [Cloudflare Tunnel setup](https://developers.cloudflare.com/tunnel/setup/)

What to do next:

1. Copy the `https://<random>.trycloudflare.com` hostname shown in your terminal
2. Set `BACKEND_ORIGIN=https://<random>.trycloudflare.com/api` in Cloudflare Pages
3. Redeploy Pages

Verification:

```bash
curl https://<random>.trycloudflare.com/healthz
curl https://<random>.trycloudflare.com/api/v1/models
```

### Option B. Named Tunnel With Your Own Domain

Use this when you want a stable backend hostname such as:

```text
api.example.com
```

This is the recommended path if you plan to keep the backend online for a while, attach Cloudflare Access, or reuse the setup for multiple applications.

Cloudflare currently recommends remotely-managed tunnels for most use cases:

- [Cloudflare Tunnel overview](https://developers.cloudflare.com/tunnel/)
- [Locally-managed vs remotely-managed tunnels](https://developers.cloudflare.com/tunnel/advanced/local-management/)

#### B1. Prerequisites

Before you start, make sure:

- Your domain is already on Cloudflare DNS
- `cloudflared` is installed on the machine running the backend
- Your backend is reachable locally at `http://127.0.0.1:8000`

Quick health check:

```bash
curl http://127.0.0.1:8000/healthz
```

#### B2. Create the Tunnel in Cloudflare

Dashboard path:

```text
Cloudflare Dashboard -> Networking -> Tunnels
```

Steps:

1. Click `Create Tunnel`
2. Choose `Cloudflared`
3. Give it a name, for example:

```text
video-subtitle-backend
```

4. Select your server OS and architecture
5. Cloudflare will show you a connector command or token

Official reference:
- [Set up Cloudflare Tunnel](https://developers.cloudflare.com/tunnel/setup/)

#### B3. Connect Your Machine to the Tunnel

There are two common ways to do this.

##### Way 1. Remotely-managed tunnel

Cloudflare gives you a tunnel token. Use it to install the tunnel as a service.

Typical command on macOS / Linux:

```bash
sudo cloudflared service install <TUNNEL_TOKEN>
```

After installation, the tunnel process runs as a background service.

##### Way 2. Locally-managed tunnel

If you prefer CLI-managed config:

```bash
cloudflared tunnel login
cloudflared tunnel create video-subtitle-backend
```

Then create DNS routing:

```bash
cloudflared tunnel route dns video-subtitle-backend api.example.com
```

Official references:
- [Create a locally-managed tunnel](https://developers.cloudflare.com/tunnel/advanced/local-management/create-local-tunnel/)
- [DNS routing for tunnel](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/routing-to-tunnel/dns/)

#### B4. Add a Published Route to Your Local Backend

If you use the Cloudflare dashboard route editor:

1. Open your tunnel
2. Under `Routes`, click `Add route`
3. Choose `Published application`
4. Fill:
- `Hostname`: `api.example.com`
- `Service URL`: `http://127.0.0.1:8000`
5. Save

This tells Cloudflare:

```text
api.example.com -> tunnel -> http://127.0.0.1:8000
```

Official reference:
- [Set up Cloudflare Tunnel](https://developers.cloudflare.com/tunnel/setup/)

#### B5. Optional Local Config File

If you use a locally-managed tunnel, a typical `~/.cloudflared/config.yml` looks like this:

```yaml
tunnel: <TUNNEL_ID>
credentials-file: /Users/<you>/.cloudflared/<TUNNEL_ID>.json

ingress:
  - hostname: api.example.com
    service: http://127.0.0.1:8000
  - service: http_status:404
```

Then run:

```bash
cloudflared tunnel run video-subtitle-backend
```

Or, if the config file is not in the default location:

```bash
cloudflared tunnel --config /path/to/config.yml run video-subtitle-backend
```

#### B6. Point Pages to the Stable Tunnel Hostname

In Cloudflare Pages, set:

- `VITE_API_BASE_URL=/api`
- `BACKEND_ORIGIN=https://api.example.com/api`

The `/api` suffix still matters because the current Pages Function strips `/api` from the incoming path before forwarding.

#### B7. Verification

Run in this order:

```bash
curl http://127.0.0.1:8000/healthz
curl https://api.example.com/healthz
curl https://api.example.com/api/v1/models
curl https://<your-pages-project>.pages.dev/api/v1/models
```

Then open:

```text
https://<your-pages-project>.pages.dev
```

Upload a small video and confirm the full path works.

#### B8. Why This Is Better Than a Quick Tunnel

With a named tunnel and your own domain, you get:

- Stable backend origin
- Better fit for Cloudflare Access
- Easier security policy management
- Reusable hostname for long-term deployment
- Cleaner setup if you later host multiple applications

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
- `1016` from Cloudflare on your custom domain:
  the DNS record points to the tunnel but the tunnel is not currently running
- Quick tunnel URL changed after restart:
  update `BACKEND_ORIGIN` and redeploy Pages, or switch to a named tunnel
