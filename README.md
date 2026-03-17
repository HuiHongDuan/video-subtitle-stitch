# Video Subtitle App · Stitch Frontend Rebuild

将原 `video-subtitle-app` 的 Streamlit 前端替换为 Stitch 风格 Web 前端，保留核心视频字幕处理能力：上传视频、ASR 转写、SRT 生成、字幕烧录、静音输出、结果下载。

## 项目结构
```text
.
├── backend/                  # FastAPI API + Python subtitle pipeline
├── deploy/                   # 各部署模式说明：local / cloudflare-tunnel / render
├── env/                      # 各部署模式环境变量示例
├── frontend/                 # React + TypeScript + Vite + Stitch 风格 UI
├── scripts/                  # 本地启动 / smoke test 脚本
├── ARCHITECTURE.md
├── SPEC.md
├── TEST_PLAN.md
└── .env.example
```

## 功能覆盖
- ✅ 上传视频
- ✅ 选择模型（tiny/base/small/medium/large，本地目录自动发现）
- ✅ 选择是否静音输出
- ✅ 按秒数剪辑后再生成字幕
- ✅ 创建任务并轮询状态
- ✅ 下载 SRT
- ✅ 下载烧录视频
- ✅ 下载无声无字幕视频
- ✅ 统一错误返回

## API 概览
- `GET /healthz`
- `GET /api/v1/models`
- `POST /api/v1/uploads`
- `POST /api/v1/jobs`
- `GET /api/v1/jobs/{job_id}`
- `GET /api/v1/jobs/{job_id}/files/subtitles`
- `GET /api/v1/jobs/{job_id}/files/video`
- `GET /api/v1/jobs/{job_id}/files/video_silent`

## 部署模式
- 本地开发：见 [deploy/local/README.md](/Users/collie/workspace/video-subtitle-stitch/deploy/local/README.md)
- Cloudflare Pages + 本地后端（Tunnel）：见 [deploy/cloudflare-tunnel/README.md](/Users/collie/workspace/video-subtitle-stitch/deploy/cloudflare-tunnel/README.md)
- Cloudflare Pages + Render 后端：见 [deploy/render/README.md](/Users/collie/workspace/video-subtitle-stitch/deploy/render/README.md)
- GHCR 镜像发布与平台拉取：见 [deploy/ghcr/README.md](/Users/collie/workspace/video-subtitle-stitch/deploy/ghcr/README.md)
- 自托管后端安全清单：见 [deploy/security/README.md](/Users/collie/workspace/video-subtitle-stitch/deploy/security/README.md)
- 部署模式总览：见 [deploy/README.md](/Users/collie/workspace/video-subtitle-stitch/deploy/README.md)

## 本地启动
### 1) Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2) Frontend
```bash
cd frontend
npm install
npm run dev
```

默认前端读取 `VITE_API_BASE_URL=http://127.0.0.1:8000`。

## Docker（推荐：macOS 隔离运行）
```bash
# 启动（自动构建）
./scripts/docker_up.sh

# 查看日志
./scripts/docker_logs.sh
# 或只看后端/前端
./scripts/docker_logs.sh backend
./scripts/docker_logs.sh frontend
./scripts/docker_logs.sh all

# 停止
./scripts/docker_down.sh
```

也可直接使用：
```bash
docker compose up -d --build
```

说明：
- backend 容器内自带 `ffmpeg` 与 Python 依赖，不污染宿主机。
- frontend 容器内自带 Node/npm，不依赖宿主机 npm。
- `./backend/workdir` 挂载到容器 `/data/workdir`，产物会保存在本地仓库。
- `./backend/models` 挂载到容器 `/app/models`，用于读取本地 fast-whisper 模型目录。
- `whisper_cache` volume 用于缓存模型，避免重复下载。

模型目录建议：
- `./backend/models/small`
- `./backend/models/medium`
- `./backend/models/large` 或 `./backend/models/large-v3`

## macOS 一键安装与启动
```bash
./scripts/install_macos.sh
./scripts/run_backend.sh
./scripts/run_frontend.sh
```

脚本会自动处理：
- 安装 `ffmpeg` / `python` / `node`（通过 Homebrew）
- 创建 `backend/.venv` 并安装 Python 依赖
- 安装 frontend `node_modules`

## 环境变量
通用默认值仍可参考 `.env.example`。

按部署模式选择更合适的示例：
- 本地：见 [env/local.example](/Users/collie/workspace/video-subtitle-stitch/env/local.example)
- Cloudflare Tunnel：见 [env/cloudflare-tunnel.example](/Users/collie/workspace/video-subtitle-stitch/env/cloudflare-tunnel.example)
- Render：见 [env/render.example](/Users/collie/workspace/video-subtitle-stitch/env/render.example)

常用项：
- `MAX_UPLOAD_MB`
- `DEFAULT_MODEL_SIZE`
- `WORKDIR_ROOT`
- `ASR_MODEL_ROOT`
- `CORS_ORIGINS`
- `VITE_API_BASE_URL`

## Cloudflare Pages 部署（同域 API）
- 将 Pages 项目 Root directory 设置为 `frontend`。
- 使用 `frontend/functions/api/[[path]].js` 作为 `/api/*` 代理（Pages Functions）。
- 在 Pages 项目中配置：
  - `VITE_API_BASE_URL=/api`
  - `BACKEND_ORIGIN=https://<your-backend-origin>/api`
- 部署后前端与 API 同域：
  - `https://<your-pages-project>.pages.dev`
  - `https://<your-pages-project>.pages.dev/api/v1/models`

详细步骤见 [deploy/cloudflare-tunnel/README.md](/Users/collie/workspace/video-subtitle-stitch/deploy/cloudflare-tunnel/README.md)。

## 测试
### backend
```bash
cd backend
pytest -q
```

### frontend
```bash
cd frontend
npm run lint
npm run build
```

## 常见问题
1. **`npm: command not found`**：执行 `brew install node`，或直接运行 `./scripts/install_macos.sh` 自动安装。
2. **`uvicorn: command not found`**：请通过 `./scripts/run_backend.sh` 启动（脚本会自动激活 `backend/.venv` 并使用 `python -m uvicorn`）。
3. **ffmpeg/ffprobe 不存在**：请先在系统安装 ffmpeg（`./scripts/install_macos.sh` 会自动安装）。
4. **ASR 下载模型慢**：首次运行 `faster-whisper` 可能需要下载模型。
5. **smoke test 被跳过**：仓库默认不附带大视频样例，补充到 `backend/tests/assets/sample_3min.mp4` 即可运行。
6. **字幕显示方框**：请重建 backend 镜像（`docker compose up -d --build backend`）。镜像内已安装 `fonts-noto-cjk`，默认字幕字体为 `Noto Sans CJK SC`（可通过 `SUBTITLE_FONT_NAME` 调整）。
