# TEST PLAN

## 1. 单元测试
### backend
- `test_subtitles.py`
  - 中文换行不超过最大行数
  - 每行长度不超过 `max_chars_per_line`
- `test_eval.py`
  - SRT 解析正确
  - 时间重叠与文本相似度计算正确
- `test_api_contract.py`
  - 创建任务接口返回 `job_id`
  - 查询状态接口返回标准字段

## 2. Smoke Test
当 `backend/tests/assets/sample_3min.mp4` 存在时：
1. 调用 pipeline 生成 `audio.wav`
2. 调用 ASR 生成 segments
3. 生成 `subtitles.srt`
4. 烧录为 `output.mp4`
5. 可选地与 `golden.srt` 比较

## 3. 前端人工验证
- 上传文件后文件名显示正确
- 选择静音/模型参数后发起请求
- 处理中显示阶段与进度
- 完成后两个下载按钮可用
- 错误状态下显示错误信息
- 亮/暗主题切换不影响布局
