# Codex Prompt

你现在要基于本仓库补全一个“前后端分离”的视频字幕 Web App。

## 背景
旧项目是 `Streamlit + Python pipeline`，新目标是：
- **前端**改为 Stitch 风格的 React/Vite 页面
- **后端**改为 FastAPI，但仍然复用原 Python pipeline 的处理逻辑
- **功能绝不能缩水**：上传视频、中文 ASR、生成 SRT、烧录字幕、可选静音、下载产物

## 关键要求
1. 保留原业务参数：`remove_audio`、`model_size`、字幕自适应规则
2. 不要引入与当前需求无关的多租户/数据库复杂度
3. 以本仓库的 `SPEC.md / ARCHITECTURE.md / TEST_PLAN.md / TASKS.md` 为准
4. 先保证本地跑通最小闭环，再做视觉与工程化优化

## 你要优先完成的文件
### backend
- `backend/app/main.py`
- `backend/app/api/routes.py`
- `backend/app/services/job_store.py`
- `backend/app/services/pipeline_service.py`

### frontend
- `frontend/src/App.tsx`
- `frontend/src/lib/api.ts`
- `frontend/src/hooks/useJobPolling.ts`

## UI 迁移原则
把 Stitch demo 中这些静态元素改成真实业务数据：
- `interview_footage_final.mp4` -> 上传文件名
- `Success` -> 依据 job status 动态切换
- `下载视频` / `下载字幕` -> 真实 download URL
- `S / M` -> 实际 whisper 模型选择
- 静音图标 -> `remove_audio`

## 完成标准
- `uvicorn app.main:app --reload` 可启动
- `npm run dev` 可启动
- 前端可以调用后端完成一次完整任务
- pytest 至少通过非依赖样例视频的单元测试
