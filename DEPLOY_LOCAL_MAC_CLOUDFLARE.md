# 本机 Mac + Cloudflare Pages Functions 部署指南

目标链路：

浏览器 -> Cloudflare Pages（前端 + Functions）-> Cloudflare Tunnel -> 本机 Docker 后端

本指南基于当前项目实现：`frontend/functions/api/[[path]].js`，不依赖单独 `worker.dev` 域名。

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

### 1.1 避免上传时报 `/data/workdir/uploads` 500

请确保 `backend/workdir` 存在（首次部署常见）：

```bash
mkdir -p backend/workdir
```

本项目已在应用启动时自动创建 `WORKDIR_ROOT`，但宿主机目录存在可避免 volume 初次挂载问题。

## 2. Cloudflare Tunnel 暴露本机后端

### 2.1 安装并登录 cloudflared（macOS）

```bash
brew install cloudflared
cloudflared tunnel login
```

### 2.2 创建 Tunnel 并绑定域名（可选）

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
curl https://api-local.yourdomain.com/api/v1/models
```

## 3. 使用 Pages Functions 代理 `/api*`

项目文件：`frontend/functions/api/[[path]].js`

当前行为：
- 处理 `/api` 与 `/api/*`
- 非 `/api*` 返回 `404`
- 支持 `GET/POST/PUT/PATCH/DELETE/HEAD/OPTIONS`
- 透传 query string、headers、body
- 自动附加 CORS 响应头
- 将路径前缀 `/api` 去掉后转发到 `${BACKEND_ORIGIN}`

路径映射示例：
- `GET /api/v1/models` -> `${BACKEND_ORIGIN}/v1/models`
- `GET /api/healthz` -> `${BACKEND_ORIGIN}/healthz`

因此本项目推荐：
- `BACKEND_ORIGIN` 以 `/api` 结尾
- 例如：`https://api-local.yourdomain.com/api`

这样：
- `/api/v1/models` -> `.../api/v1/models`（正确）

## 4. 部署 Pages（前端 + Functions 同项目）

### 4.1 Cloudflare Dashboard 配置（Pages）

1. Cloudflare Dashboard -> `Workers & Pages` -> `Create` -> `Pages`
2. 连接 Git 仓库
3. 构建参数：
   - Framework preset: `Vite`
   - Root directory: `frontend`
   - Build command: `npm run build`
   - Build output directory: `dist`
4. 前端环境变量：
   - `VITE_API_BASE_URL=/api`
5. Functions 变量（Settings -> Variables and Secrets）：
   - `BACKEND_ORIGIN=https://api-local.yourdomain.com/api`

> 注意：如果你使用 Wrangler 管理 Pages 配置，以 Wrangler 为准；Dashboard 变量需保持一致。

### 4.2 部署后验证

```bash
curl -i https://<your-pages-project>.pages.dev/api/v1/models
curl -i https://<your-pages-project>.pages.dev/api/healthz
```

访问前端：

```text
https://<your-pages-project>.pages.dev
```

前端与 API 都在同一 `*.pages.dev` 域名下，无需单独 `workers.dev` 入口。

## 5. 常见报错排查

1. `GET /api/v1/models` 返回 404，但 tunnel 直连是 200
- 检查 `BACKEND_ORIGIN` 是否漏了 `/api`
- 当前函数会去掉 `/api` 前缀，变量不带 `/api` 会被转发成 `/v1/models`（后端无此路由）

2. Functions 返回 `BACKEND_ORIGIN is not configured`
- 在 Pages 项目 Variables and Secrets 补充 `BACKEND_ORIGIN`

3. 上传时报 500，日志出现 `/data/workdir/uploads` not found
- 确认 `backend/workdir` 存在并被挂载
- 重启 backend：`docker compose up -d --build backend`

4. Functions 返回 `502 Bad Gateway`
- 本机 Docker 后端是否运行：`docker compose ps`
- Tunnel 是否运行：`cloudflared tunnel run ...`
- `BACKEND_ORIGIN` 是否可访问

5. `GET /api/healthz` 404（来自后端）
- 说明代理规则/`BACKEND_ORIGIN` 不匹配
- 当前推荐配置下，`/api/healthz` 应转发为后端 `/healthz`

## 6. 推荐验证顺序

1. `curl http://127.0.0.1:8000/healthz`
2. `curl https://api-local.yourdomain.com/healthz`
3. `curl https://api-local.yourdomain.com/api/v1/models`
4. `curl https://<your-pages-project>.pages.dev/api/v1/models`
5. 打开 `https://<your-pages-project>.pages.dev`，上传视频并观察轮询与下载
