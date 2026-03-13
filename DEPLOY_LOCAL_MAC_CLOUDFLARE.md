# 本机 Mac + Cloudflare 部署指南

目标链路：

浏览器 -> Cloudflare Pages -> Cloudflare Worker -> Cloudflare Tunnel -> 本机 Docker 后端

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

## 3. 部署 Worker（API 代理）

`worker/src/index.js` 已实现：
- 仅处理 `/api/*`
- 非 `/api/*` 返回 `404`
- 支持 `GET/POST/PUT/PATCH/DELETE/OPTIONS`
- 支持 CORS
- 保留 query string

### 3.1 本地准备

```bash
cd worker
npm install
cp .dev.vars.example .dev.vars
```

`.dev.vars` 示例：

```bash
BACKEND_ORIGIN=https://api-local.yourdomain.com/api
```

说明：
- Worker 会把 `/api/xxx` 转发到 `${BACKEND_ORIGIN}/xxx`
- 本项目后端路由是 `/api/v1/*`，所以建议 `BACKEND_ORIGIN` 以 `/api` 结尾

### 3.2 Cloudflare 后台配置（Worker）

1. Cloudflare Dashboard -> `Workers & Pages` -> `Create` -> `Workers`  
2. 选择 `Import a repository` 或先命令行 `npm run deploy`  
3. 若走命令行部署：`cd worker && npm run deploy`  
4. 在 Worker -> `Settings` -> `Variables and Secrets` 新增：  
   - Key: `BACKEND_ORIGIN`  
   - Value: `https://api-local.yourdomain.com/api`  
5. 在 Worker -> `Settings` -> `Triggers` -> `Routes` 新增路由：  
   - `your-app-domain.com/api/*`

## 4. 部署 Pages（前端）

### 4.1 Cloudflare 后台配置（Pages）

1. Cloudflare Dashboard -> `Workers & Pages` -> `Create` -> `Pages`  
2. 连接 Git 仓库  
3. 填写构建参数：
   - Framework preset: `Vite`
   - Root directory: `frontend`
   - Build command: `npm run build`
   - Build output directory: `dist`
4. `Environment variables` 增加：
   - `VITE_API_BASE_URL=/api`

### 4.2 自定义域

1. Pages 项目 -> `Custom domains` -> `Set up a custom domain`  
2. 绑定你的前端域名（例如 `your-app-domain.com`）  
3. 保证 Worker 路由和 Pages 域名一致：  
   - Pages: `your-app-domain.com/*`  
   - Worker route: `your-app-domain.com/api/*`

## 5. 常见报错排查

1. 前端报 `404 /api/...`  
- 检查 Worker 是否绑定了 `your-app-domain.com/api/*` 路由

2. Worker 报 `BACKEND_ORIGIN is not configured`  
- 去 Worker `Settings -> Variables and Secrets` 补 `BACKEND_ORIGIN`

3. Worker 报 `502 Bad Gateway`  
- 本机 Docker 后端是否运行：`docker compose ps`
- Tunnel 是否运行：`cloudflared tunnel run ...`
- `BACKEND_ORIGIN` 域名是否可访问

4. 后端本地可访问，公网不可访问  
- 检查 `cloudflared` ingress 的 `hostname` 与 DNS 绑定是否一致

5. CORS 报错  
- 本 Worker 已返回基础 CORS；若浏览器仍拦截，确认是否跨域访问了非 Worker 域名

## 6. 推荐验证顺序

1. `curl http://127.0.0.1:8000/healthz`
2. `curl https://api-local.yourdomain.com/healthz`
3. `curl https://your-app-domain.com/api/v1/models`
4. 打开 `https://your-app-domain.com`，上传视频并观察轮询与下载
