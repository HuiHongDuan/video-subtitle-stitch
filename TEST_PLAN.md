# TEST PLAN

## Backend
1. 配置与导入
   - FastAPI app 可导入
   - settings 默认值可加载
2. API 合约
   - `GET /healthz` 返回 `{"ok": true}`
   - `GET /api/v1/models` 返回可选模型与默认模型
   - `GET /api/v1/jobs/{missing}` 返回统一错误结构
   - `POST /api/v1/jobs` 参数校验（非法 model_size）
3. 领域单元测试
   - 字幕换行/生成 SRT
   - 评测指标计算
4. Smoke test
   - 若 `tests/assets/sample_3min.mp4` 存在，执行 pipeline 全链路

## Frontend
1. `npm run lint` (TypeScript noEmit)
2. `npm run build` (Vite build)
3. 人工验证状态流转：上传、处理中、完成、失败

## 手工验收清单
- 上传限制与文件类型提示正确
- 模型列表来自后端接口
- 长任务可轮询
- 结果下载按钮仅在可用时可点
- 错误消息对用户可读


## Docker 验证
1. `docker compose config`
2. `docker compose up -d --build`
3. `curl http://127.0.0.1:8000/healthz`
4. 打开 `http://127.0.0.1:3000`
5. `docker compose down`
