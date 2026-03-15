# 本机 Mac + Cloudflare Pages Functions 部署指南

目标链路：

浏览器 -> Cloudflare Pages（前端 + Functions）-> Cloudflare Tunnel -> 本机 Docker 后端

## 1. 启动本机 Docker 后端

在项目根目录：

```bash
docker compose up -d --build backend
docker compose ps
curl http://127.0.0.1:8000/healthz
```

确认点：
- `docker-compose.yml` 已将后端端口暴露为 `8000:8000`
- 后端监听地址应为 `0.0.0.0`

本项目当前已满足：
- `docker-compose.yml` 中 `APP_HOST=0.0.0.0`
- `backend/app/core/config.py` 默认 `app_host='0.0.0.0'`

如果你本地改成了 `127.0.0.1`，改回：
- 环境变量 `APP_HOST=0.0.0.0`

## 2. Cloudflare Tunnel 暴露本机后端

### 2.1 安装并登录 cloudflared（macOS）

```bash
brew install cloudflared
cloudflared tunnel login
```

### 2.2 创建 Tunnel 并绑定域名

```bash
cloudflared tunnel create video-subtitle-local
cloudflared tunnel route dns video-subtitle-local api-local.yourdomain.com
```

### 2.3 配置 ingress

在 `~/.cloudflared/config.yml` 写入（替换 tunnel id 和域名）：

```yaml
tunnel: <YOUR_TUNNEL_ID>
credentials-file: /Users/<YOU>/.cloudflared/<YOUR_TUNNEL_ID>.json

ingress:
  - hostname: api-local.yourdomain.com
    service: http://127.0.0.1:8000
  - service: http_status:404
```

启动：

```bash
cloudflared tunnel run video-subtitle-local
```

验证：

```bash
curl https://api-local.yourdomain.com/healthz
```

## 3. 使用 Pages Functions 代理 `/api/*`

项目已提供：`frontend/functions/api/[[path]].js`

行为：
- 仅处理 `/api/*`
- 非 `/api/*` 返回 `404`
- 支持 `GET/POST/PUT/PATCH/DELETE/HEAD/OPTIONS`
- 保留 query string
- 将 `/api/xxx` 转发到 `${BACKEND_ORIGIN}/xxx`

说明：
- 本项目后端路由为 `/api/v1/*`
- 因此建议 `BACKEND_ORIGIN` 以 `/api` 结尾，例如：
  - `https://api-local.yourdomain.com/api`

## 4. 部署 Pages（前端 + Functions 同项目）

### 4.1 Cloudflare Dashboard 配置（Pages）

1. Cloudflare Dashboard -> `Workers & Pages` -> `Create` -> `Pages`
2. 连接 Git 仓库
3. 构建参数：
   - Framework preset: `Vite`
   - Root directory: `frontend`
   - Build command: `npm run build`
   - Build output directory: `dist`
4. 环境变量：
   - `VITE_API_BASE_URL=/api`
5. Functions 变量（Settings -> Variables and Secrets）：
   - `BACKEND_ORIGIN=https://api-local.yourdomain.com/api`

> 注意：如果你使用 Wrangler 管理 Pages 项目配置，以 Wrangler 文件为准；Dashboard 变量需保持一致。

### 4.2 部署后验证

```bash
curl https://<your-pages-project>.pages.dev/api/v1/models
curl https://<your-pages-project>.pages.dev/api/healthz
```

访问前端：

```text
https://<your-pages-project>.pages.dev
```

前端与 API 都在同一 `*.pages.dev` 域名下，无需单独 `workers.dev` 入口。

## 5. 常见报错排查

1. 页面可访问，但 `/api/...` 返回 404
- 确认 Pages 项目根目录是 `frontend`
- 确认仓库中存在 `frontend/functions/api/[[path]].js`

2. Functions 返回 `BACKEND_ORIGIN is not configured`
- 在 Pages 项目 Variables and Secrets 补充 `BACKEND_ORIGIN`

3. Functions 返回 `502 Bad Gateway`
- 本机 Docker 后端是否运行：`docker compose ps`
- Tunnel 是否运行：`cloudflared tunnel run ...`
- `BACKEND_ORIGIN` 是否可访问

4. 本地可访问，公网不可访问
- 检查 cloudflared ingress `hostname` 与 DNS 绑定一致

## 6. 推荐验证顺序

1. `curl http://127.0.0.1:8000/healthz`
2. `curl https://api-local.yourdomain.com/healthz`
3. `curl https://<your-pages-project>.pages.dev/api/v1/models`
4. 打开 `https://<your-pages-project>.pages.dev`，上传视频并观察轮询与下载
