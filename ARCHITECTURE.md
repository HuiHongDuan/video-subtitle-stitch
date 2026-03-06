# ARCHITECTURE

## 目录结构
```text
.
├── backend/
│   ├── app/api          # FastAPI 路由层
│   ├── app/services     # 任务与上传管理 + pipeline 编排
│   ├── app/domain       # 视频/ASR/SRT/评测核心能力
│   ├── app/models       # Pydantic 数据模型
│   └── tests            # API/单元/smoke 测试
├── frontend/
│   └── src              # Stitch 风格页面 + API client + polling hooks
├── scripts/             # 本地运行与 smoke test 脚本
└── docs: README/SPEC/TEST_PLAN
```

## 调用链
1. 前端 `App.tsx` 上传文件到 `/api/v1/uploads`
2. 前端使用 `upload_id` 调用 `/api/v1/jobs` 创建任务
3. 后端 `pipeline_service` 异步执行：探测分辨率 → 抽音频 → ASR → SRT → 烧录视频
4. 前端轮询 `/api/v1/jobs/{id}`，任务完成后展示下载链接

## 关键复用点
- 复用原 Python pipeline 能力：`domain/video.py`, `domain/asr.py`, `domain/subtitles.py`, `domain/pipeline.py`
- UI 层由 Streamlit 替换为 React + FastAPI API

## 状态机
- `queued`
- `processing`（stage: `probe` / `extract_audio` / `asr` / `render`）
- `completed`
- `failed`

## 设计说明
- 前后端解耦：UI 不直接调用 ffmpeg/whisper，全部走 API。
- 上传与任务分离：为后续扩展分片上传/重试预留能力。
- 错误格式统一：前端可稳定显示可读错误信息。
