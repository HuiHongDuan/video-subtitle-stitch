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
1. **ffmpeg/ffprobe 不存在**：请先在系统安装 ffmpeg。
2. **ASR 下载模型慢**：首次运行 `faster-whisper` 可能需要下载模型。
3. **smoke test 被跳过**：仓库默认不附带大视频样例，补充到 `backend/tests/assets/sample_3min.mp4` 即可运行。
