# SPEC

## 目标
在不改变 `video-subtitle-app` 业务功能的前提下，用 Stitch 风格前端替换原有 Streamlit UI，形成一套前后端分离的新项目：
- 前端：React + Vite + Tailwind 风格玻璃态界面
- 后端：FastAPI + 原 Python subtitle pipeline

## 核心用户流程
1. 上传单个视频文件（mp4 / mov / mkv / avi / webm）
2. 选择：
   - 输出静音（remove_audio）
   - 模型大小（tiny / base / small / medium）
3. 提交任务
4. 前端轮询任务进度
5. 完成后下载：
   - `subtitles.srt`
   - `output.mp4`

## 功能约束
### 1. 上传与校验
- 最大文件大小默认 500MB，可通过环境变量覆盖
- 每个任务都有独立工作目录，避免并发冲突

### 2. 中文 ASR
- 使用 `faster-whisper`
- 输出带 start / end / text 的 segments

### 3. 字幕格式与排版
- 输出标准 `.srt`
- 每条字幕最多 2 行
- 每行默认 18 个字符
- 优先按中文标点或空格断行，否则硬切

### 4. 字幕样式自适应
- `fontsize = clamp(round(height * 0.05), 18, 56)`
- `margin_v = clamp(round(height * 0.06), 24, 80)`
- `Alignment=2, Outline=2, Shadow=1`

### 5. 视频输出
- 烧录字幕到 MP4
- 静音输出时使用 `-an`
- 否则保留原音轨

### 6. 前端体验
- 保留 Stitch UI 的玻璃态、暗黑模式、渐变背景、按钮语义
- 将原 demo 的静态状态改为真实状态机：idle / uploading / processing / success / error

### 7. 自动化测试
- backend 单测：字幕换行、SRT 评测、API 契约
- smoke test：若存在样例视频，跑完整 pipeline
