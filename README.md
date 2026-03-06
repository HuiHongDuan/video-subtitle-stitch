# Video Subtitle App · Stitch Frontend Rebuild

这是一套为 Codex 准备的“重跑项目”骨架：
- 保留 `video-subtitle-app` 的核心业务能力：上传视频、中文 ASR、生成 SRT、烧录字幕、可选静音输出。
- 用 `ai-subtitles-ui.zip` 的 Stitch 风格前端替换原来的 Streamlit UI。
- 将系统拆为：`frontend` (Vite + React) + `backend` (FastAPI + 复用原 Python pipeline)。

## 设计目标
1. **不改变业务能力**：处理参数、输出产物、字幕自适应规则、评测口径保持一致。
2. **替换前端交互层**：把 Stitch demo 改造成真实可用的上传/轮询/下载界面。
3. **让 Codex 可继续开发**：文档、环境变量、测试、脚本、目录结构全部齐备。

## 项目结构
```text
.
├── backend/                  # FastAPI API + Python subtitle pipeline
├── frontend/                 # Stitch 风格 React UI
├── scripts/                  # 本地启动 / smoke test / 安装脚本
├── SPEC.md
├── ARCHITECTURE.md
├── TASKS.md
├── TEST_PLAN.md
└── CODEX_PROMPT.md
```

## 本地开发
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

## Codex 执行顺序建议
1. 先补全 `backend/app/services/pipeline_service.py` 与任务状态管理。
2. 接着把 `frontend/src/App.tsx` 与 `frontend/src/lib/api.ts` 接通真实接口。
3. 最后跑 `scripts/smoke_test.sh` 与 `pytest`。
