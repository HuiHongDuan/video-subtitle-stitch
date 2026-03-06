# ARCHITECTURE

## 总体架构
```text
React Frontend
  ├─ 上传文件 / 发起任务
  ├─ 轮询任务状态
  └─ 下载产物
        │
        ▼
FastAPI Backend
  ├─ /api/v1/jobs              创建任务
  ├─ /api/v1/jobs/{id}         查询状态
  ├─ /api/v1/jobs/{id}/files/* 下载结果
  └─ pipeline_service          编排处理流程
        │
        ▼
Domain Pipeline
  ├─ video.py       ffmpeg / ffprobe
  ├─ asr.py         faster-whisper
  ├─ subtitles.py   segments -> srt
  ├─ eval.py        predicted vs golden
  └─ storage        工作目录隔离
```

## 为什么不继续用 Streamlit
原项目 UI 与业务强耦合在 `app.py`，而 Stitch 前端是标准 React/Vite 工程。为了“前端彻底替换且后续可持续迭代”，应把 UI 层迁移为 Web API + SPA：
- 业务逻辑仍复用 Python
- UI 切换成本最低
- Codex 容易继续补齐

## 目录职责
### backend/app/domain
来自原项目的核心实现或等价迁移：
- `asr.py`
- `eval.py`
- `pipeline.py`
- `settings.py`
- `storage.py`
- `subtitles.py`
- `video.py`

### backend/app/services
服务层封装：
- 文件落盘
- 后台任务线程 / 任务状态
- pipeline 调用
- 结果路径映射

### frontend/src
- `App.tsx`：页面容器与全局状态
- `components/`：上传卡片、控制区、状态区、下载区
- `lib/api.ts`：API client
- `hooks/useJobPolling.ts`：轮询 job 状态

## API 契约
### POST `/api/v1/jobs`
`multipart/form-data`
- `file`: 上传视频
- `remove_audio`: boolean
- `model_size`: string

返回：
```json
{
  "job_id": "uuid",
  "status": "queued"
}
```

### GET `/api/v1/jobs/{job_id}`
返回：
```json
{
  "job_id": "uuid",
  "status": "processing",
  "stage": "asr",
  "progress": 45,
  "error": null,
  "result": null
}
```

### 成功结果
```json
{
  "job_id": "uuid",
  "status": "completed",
  "stage": "done",
  "progress": 100,
  "result": {
    "resolution": {"width": 1920, "height": 1080},
    "fontsize": 54,
    "margin_v": 65,
    "segments": 123,
    "download_urls": {
      "srt": "/api/v1/jobs/{job_id}/files/subtitles",
      "video": "/api/v1/jobs/{job_id}/files/video"
    }
  }
}
```
