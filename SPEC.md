# SPEC

## 目标
保持原 `video-subtitle-app` 业务语义（上传视频、ASR、SRT、烧录字幕、静音选项、结果下载），并以 Stitch 风格 React 前端替代 Streamlit 页面。

## 核心用户流程
1. 进入页面
2. 上传视频文件
3. 选择模型与参数（model_size / remove_audio）
4. 提交任务
5. 轮询任务状态（queued / processing / completed / failed）
6. 下载 `subtitles.srt`
7. 下载 `output.mp4`（若生成）

## API 契约
- `GET /healthz`
- `GET /api/v1/models`
- `POST /api/v1/uploads`
- `POST /api/v1/jobs`
- `GET /api/v1/jobs/{job_id}`
- `GET /api/v1/jobs/{job_id}/files/subtitles`
- `GET /api/v1/jobs/{job_id}/files/video`

统一错误格式：
```json
{"error": "message", "code": "ERROR_CODE"}
```

## 处理流程约束
- 上传文件大小受 `MAX_UPLOAD_MB` 控制
- 工作目录按 `job_id` 隔离
- 字幕换行策略与原业务一致（最大行数/行宽）
- 字幕样式按视频分辨率自适应
- 支持静音输出（ffmpeg `-an`）

## 测试范围
- backend: 健康检查、模型接口、参数校验、任务查询、字幕/评测单元测试、可选 pipeline smoke test
- frontend: TypeScript 类型检查 + 构建验证
