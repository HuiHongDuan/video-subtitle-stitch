# Video Subtitle App · Stitch Frontend Rebuild

将原 `video-subtitle-app` 的 Streamlit 前端替换为 Stitch 风格 Web 前端，保留核心视频字幕处理能力：上传视频、ASR 转写、SRT 生成、字幕烧录、静音输出、结果下载。

## 项目结构
```text
.
├── backend/                  # FastAPI API + Python subtitle pipeline
├── frontend/                 # React + TypeScript + Vite + Stitch 风格 UI
├── scripts/                  # 本地启动 / smoke test 脚本
├── ARCHITECTURE.md
├── SPEC.md
├── TEST_PLAN.md
└── .env.example
```

## 功能覆盖
- ✅ 上传视频
- ✅ 选择模型（tiny/base/small/medium）
- ✅ 选择是否静音输出
- ✅ 创建任务并轮询状态
- ✅ 下载 SRT
- ✅ 下载烧录视频
- ✅ 统一错误返回

## API 概览
- `GET /healthz`
- `GET /api/v1/models`
- `POST /api/v1/uploads`
- `POST /api/v1/jobs`
- `GET /api/v1/jobs/{job_id}`
- `GET /api/v1/jobs/{job_id}/files/subtitles`
- `GET /api/v1/jobs/{job_id}/files/video`

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
- `whisper_cache` volume 用于缓存模型，避免重复下载。

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
复制 `.env.example`，常用项：
- `MAX_UPLOAD_MB`
- `DEFAULT_MODEL_SIZE`
- `WORKDIR_ROOT`
- `CORS_ORIGINS`
- `VITE_API_BASE_URL`

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
