# Cloudflare Pages Functions 同域 API 代理通用教程

本教程用于把“前端静态站点 + 独立后端 API”部署为同域访问：

- 前端：`https://your-app.pages.dev`
- API：`https://your-app.pages.dev/api/*`

核心思路是：在 Pages 项目内使用 `functions/api/[[path]].js` 把 `/api/*` 请求反向代理到你自己的后端入口（例如 Tunnel、云主机 API）。

---

## 1. 这类方案解决了什么问题

- 前端与 API 同域，减少跨域配置和调试成本
- 不需要单独暴露 `workers.dev` 入口
- 前端代码里 API 基址可以稳定写成 `/api`
- 可以把现有 Worker 代理逻辑几乎原样迁移到 Pages Functions

---

## 2. 目录与文件放置

如果你的 Pages Root directory 是 `frontend`，则 Functions 必须放在：

```text
frontend/functions/api/[[path]].js
```

如果你的 Pages Root directory 是仓库根目录，则放在：

```text
functions/api/[[path]].js
```

`[[path]]` 是 Pages Functions 的“捕获路由”写法，表示匹配 `/api/*` 的任意层级路径。

---

## 3. `[[path]].js` 逐段解析（按当前实现）

示例文件：`frontend/functions/api/[[path]].js`

### 3.1 允许的方法清单

```js
const ALLOWED_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'];
```

用途：
- 白名单控制，避免意外方法透传到上游
- `OPTIONS` 用于预检

### 3.2 CORS 辅助函数（`corsHeaders` / `withCors`）

用途：
- 统一为正常响应和错误响应补充 CORS 头
- 避免浏览器把后端错误“吃掉”为泛化跨域错误，便于前端拿到真实错误信息

关键点：
- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Methods` 来自方法白名单
- `Access-Control-Allow-Headers` 使用请求里声明的预检头

### 3.3 读取并规范化上游地址

```js
function normalizeBackendOrigin(env) {
  const origin = env.BACKEND_ORIGIN;
  if (!origin || !origin.trim()) return null;
  return origin.trim().replace(/\/+$/, '');
}
```

用途：
- 从 Pages 环境变量读取 `BACKEND_ORIGIN`
- 去掉末尾斜杠，避免后续拼接成 `//path`

### 3.4 生成上游请求 URL

```js
function buildUpstreamUrl(requestUrl, backendOrigin) {
  const incomingUrl = new URL(requestUrl);
  const upstreamPath = incomingUrl.pathname.replace(/^\/api/, '') || '/';
  return `${backendOrigin}${upstreamPath}${incomingUrl.search}`;
}
```

用途：
- 将前端请求路径 `/api/...` 改写后转发到上游
- 保留 query string（`incomingUrl.search`）

注意：
- 你当前实现会去掉路径前缀 `/api`
- 因此若前端请求 `/api/v1/models`，上游会收到 `/v1/models`
- 所以常见配置是把 `BACKEND_ORIGIN` 设为 `https://upstream.example.com/api`

### 3.5 主入口：`onRequest(context)`

```js
export async function onRequest(context) {
  const { request, env } = context;
  const incomingUrl = new URL(request.url);
```

用途：
- Pages Functions 的 HTTP 入口
- `request` 是原始请求，`env` 是 Pages 变量/密钥绑定

### 3.6 只处理 `/api` 或 `/api/*` 路径

```js
if (!(incomingUrl.pathname === '/api' || incomingUrl.pathname.startsWith('/api/'))) {
  return new Response('Not Found', { status: 404 });
}
```

用途：
- 防止函数误处理非 API 路由

### 3.7 方法校验与预检处理

```js
if (!ALLOWED_METHODS.includes(request.method)) {
  return new Response('Method Not Allowed', { status: 405 });
}

if (request.method === 'OPTIONS') {
  return new Response(null, { status: 204 });
}
```

用途：
- 非白名单方法直接 405
- 预检请求快速返回 204

### 3.8 环境变量缺失保护

```js
const backendOrigin = normalizeBackendOrigin(env);
if (!backendOrigin) {
  return new Response('BACKEND_ORIGIN is not configured', { status: 500 });
}
```

用途：
- 未配置上游地址时给出明确错误

### 3.9 透传请求头并补充转发头

```js
const headers = new Headers(request.headers);
headers.set('X-Forwarded-Proto', incomingUrl.protocol.replace(':', ''));
headers.set('X-Forwarded-Host', incomingUrl.host);
```

用途：
- 保留原请求头（如 `Authorization`）
- 给后端提供来源协议/域名信息

### 3.10 透传请求体（排除 GET/HEAD）

```js
const init = {
  method: request.method,
  headers,
  redirect: 'manual',
};

if (!['GET', 'HEAD'].includes(request.method)) {
  init.body = request.body;
}
```

用途：
- 上传文件、表单、JSON 都直接透传
- `redirect: 'manual'` 防止自动跟随重定向造成行为不一致

### 3.11 发起上游请求并回传响应

```js
try {
  const upstreamResp = await fetch(upstreamUrl, init);
  return withCors(upstreamResp, request);
} catch {
  return withCors(new Response('Bad Gateway', { status: 502 }), request);
}
```

用途：
- 成功时原样返回上游响应
- 上游不可达时返回 502

---

## 4. 通用部署步骤（可复用）

1. 确认 Pages Root directory（决定 `functions` 放在哪）。
2. 新增 `functions/api/[[path]].js` 代理文件。
3. 前端 API 基址改为 `/api`（例如 `VITE_API_BASE_URL=/api`）。
4. 在 Pages 项目配置 `BACKEND_ORIGIN`。
5. 触发部署。
6. 依次验证：
   - `GET https://<pages>.pages.dev/api/healthz`（或你的健康检查）
   - `GET https://<pages>.pages.dev/api/v1/models`（或你的业务接口）
   - 上传/鉴权等关键接口

---

## 5. 变量配置建议

- `VITE_API_BASE_URL=/api`
- `BACKEND_ORIGIN=https://your-upstream.example.com/api`（适用于“去掉 `/api` 前缀”的代理实现）

若你改成“路径不去前缀、直接透传”，则通常配置：
- `BACKEND_ORIGIN=https://your-upstream.example.com`

---

## 6. 常见故障与定位

### 6.1 `/api/v1/models` 404，但直连上游 200

常见原因：路径改写与 `BACKEND_ORIGIN` 不匹配。

排查：
- 看代理代码是否 `replace(/^\/api/, '')`
- 看 `BACKEND_ORIGIN` 是否应带 `/api`

### 6.2 前端报 500，后端日志 `FileNotFoundError: /data/workdir/uploads`

原因：后端工作目录不存在。

修复：
- 应用启动时自动 `mkdir -p WORKDIR_ROOT`
- 或提前创建并正确挂载 volume

### 6.3 `healthz` 通，业务接口失败

说明：网络链路通，但业务层失败。需看后端日志和请求参数。

### 6.4 上传成功后渲染失败

说明：多半是后端处理环节（如空字幕、ffmpeg 参数、字体）问题，而不是代理层。

---

## 7. 可复用模板（最小代理）

```js
export async function onRequest(context) {
  const { request, env } = context;
  const incoming = new URL(request.url);

  if (!incoming.pathname.startsWith('/api/')) {
    return new Response('Not Found', { status: 404 });
  }

  const origin = env.BACKEND_ORIGIN?.trim()?.replace(/\/+$/, '');
  if (!origin) {
    return new Response('BACKEND_ORIGIN is not configured', { status: 500 });
  }

  const upstreamPath = incoming.pathname.replace(/^\/api/, '') || '/';
  const upstreamUrl = `${origin}${upstreamPath}${incoming.search}`;

  const headers = new Headers(request.headers);
  headers.set('X-Forwarded-Proto', incoming.protocol.replace(':', ''));
  headers.set('X-Forwarded-Host', incoming.host);

  const resp = await fetch(upstreamUrl, {
    method: request.method,
    headers,
    body: ['GET', 'HEAD'].includes(request.method) ? undefined : request.body,
    redirect: 'manual',
  });

  return resp;
}
```

---

## 8. 迁移到其他项目时的清单

- [ ] 明确 Root directory
- [ ] 放置 `functions/api/[[path]].js`
- [ ] 统一前端 API 前缀 `/api`
- [ ] 对齐路径改写规则与 `BACKEND_ORIGIN`
- [ ] 配置 Pages 变量（Production/Preview 分环境）
- [ ] 验证健康检查、列表接口、上传接口
- [ ] 检查后端日志，确认 4xx/5xx 的真实来源
