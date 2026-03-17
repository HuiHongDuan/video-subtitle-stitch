# Self-Hosted Backend Security Guide

这份文档面向当前项目的“前端放云上，后端放自己平台”的部署方式，尤其适用于：

- Cloudflare Pages + Tunnel + 自托管后端
- Cloudflare Pages + 自有服务器 / VPS 后端

目标不是追求“绝对安全”，而是先把最关键、最容易出问题的地方收紧，避免把一个重 CPU / 重内存 / 可上传文件的后端直接暴露在公网。

## 推荐架构

```text
Browser
  -> Cloudflare Pages
  -> Pages Functions (/api/*)
  -> Cloudflare Tunnel
  -> Self-hosted FastAPI backend
```

安全原则：

- 不直接暴露后端公网端口
- 先在 Cloudflare 边缘做入口控制
- 后端自己也做鉴权、限流和资源保护

## 0. 先理解边界

你这个项目的风险点主要有 4 类：

1. 别人直接打你的后端入口
2. 别人滥用上传和任务接口，消耗你的 CPU / 内存 / 磁盘
3. 你的服务器本身被弱 SSH、弱密码或公网端口暴露带来风险
4. 错误日志、路径、密钥或文件泄露

所以最小安全目标应该是：

- 后端不裸露到公网
- 只有你授权的人或系统能访问 API
- 上传和 job 创建不能无限制打资源
- 服务器自身不因为 SSH 或系统配置过弱被拿下

## 1. 必做项

### 1.1 不要把后端裸露到公网

#### 要达到的状态

外部用户无法直接访问你机器的 `8000` 端口，只能通过 Cloudflare 入口访问。

#### 不要这样做

- 路由器端口映射 `8000 -> 8000`
- 云主机安全组直接放行 `0.0.0.0/0` 访问 `8000`
- 用公网 IP + `:8000` 直接暴露 FastAPI

#### 推荐做法

后端只监听本机或内网，例如：

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

如果你用 Docker：

- 容器内部监听 `0.0.0.0:8000`
- 宿主机不要开放公网访问
- 最稳妥的是只让 `cloudflared` 去访问它

#### 具体如何设置

##### 家庭网络 / 本地机器

1. 不做任何路由器端口映射。
2. 后端继续只在本机或局域网可达。
3. 通过 `cloudflared tunnel` 暴露服务，而不是暴露路由器公网端口。

##### 云主机 / VPS

1. 进入云平台安全组或防火墙规则页面。
2. 删除或禁用对公网开放的 `8000/tcp`。
3. 保留：
- `22/tcp`，并且最好限制为你的固定 IP
- `80/443` 如果你还跑其他公开 Web 服务
4. 确认后端只通过 Tunnel 或反向代理入口暴露。

#### 你可以怎么验证

从一台公网机器上执行：

```bash
curl http://<your-public-ip>:8000/healthz
```

预期应该是：

- 连接失败
- 超时
- 被拒绝

而不是返回 `200 OK`。

### 1.2 用 Cloudflare Tunnel 暴露服务

Cloudflare 官方对自托管 Web 应用的推荐路径，就是先建 Access，再通过 Tunnel 发布。官方文档：

- Self-hosted app 发布：<https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/self-hosted-public-app/>
- Self-hosted app 配置：<https://developers.cloudflare.com/cloudflare-one/applications/configure-apps/self-hosted-apps/>

#### 最小做法

1. 在 Cloudflare Zero Trust 创建一个 named tunnel。
2. 给 tunnel 绑定一个你自己的子域名，例如：

```text
api.example.com
```

3. 把这个 hostname 指向你本机后端：

```text
http://127.0.0.1:8000
```

#### 典型本机配置

`~/.cloudflared/config.yml`

```yaml
tunnel: <TUNNEL_ID>
credentials-file: /Users/<you>/.cloudflared/<TUNNEL_ID>.json

ingress:
  - hostname: api.example.com
    service: http://127.0.0.1:8000
  - service: http_status:404
```

#### 启动方式

先前台测试：

```bash
cloudflared tunnel run <TUNNEL_NAME>
```

确认通了之后，再装成后台服务。

#### 你可以怎么验证

```bash
curl https://api.example.com/healthz
curl https://api.example.com/api/v1/models
```

如果这两条通，但公网 IP 的 `:8000` 不通，就说明入口边界是对的。

### 1.3 给后端入口加 Cloudflare Access

这一层的作用是：即使别人知道你的后端域名，也不能直接访问。

Cloudflare 官方建议是先配 Access，再配 tunnel route。官方文档：

- Access controls：<https://developers.cloudflare.com/cloudflare-one/access-controls/>
- Self-hosted app：<https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/self-hosted-public-app/>

#### 最简单的配置方式

如果后端只给你自己或少数内部用户用：

- Access policy 里只放你的邮箱
- 或只放你自己的邮箱域名

#### 具体如何设置

1. 打开 Cloudflare Zero Trust。
2. 进入：

```text
Access controls -> Applications
```

3. 点击：

```text
Add an application
```

4. 选择：

```text
Self-hosted
```

5. 填：
- `Application name`: 自定义，例如 `video-subtitle-stitch-backend`
- `Session duration`: 先用 `24 hours`

6. 点击 `Add public hostname`
7. 填你的后端域名，例如：
- `Subdomain`: `api`
- `Domain`: `example.com`
- `Path`: `*`

8. 创建访问策略：
- `Action`: `Allow`
- `Include`: `Emails`
- 填你的登录邮箱

9. 保存。

#### 最重要的一步：Protect with Access

Cloudflare 官方特别强调，如果你要保护 origin，最好启用 token 验证。最简单的做法是让 `cloudflared` 代你验证，也就是开启 tunnel 里的：

```text
Protect with Access
```

这样即使有人绕开正常路径，origin 也不会轻易信任。

#### 你可以怎么验证

1. 用无痕窗口打开 `https://api.example.com/api/v1/models`
2. 预期先看到 Cloudflare Access 登录页
3. 未授权邮箱不能进入
4. 授权邮箱登录后才能拿到响应

### 1.4 给上传接口做限流

你的 `/api/v1/uploads` 是最危险的入口，因为它最消耗：

- 带宽
- 磁盘
- CPU
- 内存

Cloudflare 官方的 Rate limiting rules 文档：

- <https://developers.cloudflare.com/waf/rate-limiting-rules/>

#### 最简单的起步规则

先做两条规则就够：

1. 规则 1：上传接口限流
- 路径：`/api/v1/uploads`
- 速率：同一 IP 每分钟最多 `5` 次
- 动作：`Block`

2. 规则 2：job 创建接口限流
- 路径：`/api/v1/jobs`
- 速率：同一 IP 每分钟最多 `20` 次
- 动作：`Managed Challenge` 或 `Block`

#### 在 Cloudflare 里怎么配

1. 打开 Cloudflare Dashboard。
2. 进入你的站点或相应 account。
3. 找到：

```text
Security -> WAF -> Rate limiting rules
```

4. 新建规则。
5. 先选匹配路径。
6. 设置速率窗口和阈值。
7. 动作先用 `Block` 或 `Managed Challenge`。

#### 先不要追求完美值

先用保守值，后面根据实际访问调整。

如果你是自己和少数人使用，这类初始值通常够用：

- 上传：`5 req / 1 min / IP`
- 创建 job：`20 req / 1 min / IP`
- 其他 `/api/*`：`60 req / 1 min / IP`

#### 你可以怎么验证

用脚本短时间反复请求上传接口，确认 Cloudflare 会开始拦截，而不是把所有请求都放到你的 origin。

### 1.5 限制上传大小

必须同时在前后两层限制：

- Cloudflare / 边缘层
- 后端应用层

#### 后端层

你这个项目已经有：

- `MAX_UPLOAD_MB`

这就是应用层的主限制项。生产环境建议明确设值，例如：

```env
MAX_UPLOAD_MB=500
```

如果你想更保守，可以先从：

```env
MAX_UPLOAD_MB=200
```

开始。

#### 边缘层

Cloudflare 本身也有上传大小和计划相关限制。你不应该完全依赖前端提示，而应该明确：

- 允许的最大文件体积
- 超限后前端显示可读错误

#### 你可以怎么验证

1. 上传一个小于上限的文件，确认能成功。
2. 上传一个明显超限的文件，确认：
- 不会进入后端处理
- 会得到清晰错误提示

### 1.6 后端要有鉴权

就算你已经用了 Cloudflare Access，后端最好仍保留一层最小鉴权。

最简单可行方案：

- `X-API-Key`

更完整方案：

- JWT / 登录态

#### 最小可执行方案

1. 生成一串高强度随机字符串，例如：

```text
VIDEO_SUBTITLE_API_KEY=<long-random-secret>
```

2. 把它配置到：
- Cloudflare Pages / Functions 环境变量
- 后端环境变量

3. 前端或 Functions 调用后端时，带上：

```http
X-API-Key: <your-secret>
```

4. 后端只允许带正确 key 的请求访问：
- `/api/v1/uploads`
- `/api/v1/jobs`

#### 如何安全保存这个 key

不要写进 Git，不要写死在代码里。只放到：

- Cloudflare 环境变量
- Render / Koyeb / VPS secret
- 本机私有 `.env.local`

#### 你可以怎么验证

1. 不带 `X-API-Key` 请求 `/api/v1/jobs`，应被拒绝。
2. 带错误 key，请求也应被拒绝。
3. 只有正确 key 才能继续。

### 1.7 保证 SSH 入口安全

如果后端跑在你自己的 Linux 服务器或 VPS 上：

- SSH 只允许密钥登录
- 禁用密码登录
- 禁用 root 远程登录

#### 具体怎么做

编辑：

```text
/etc/ssh/sshd_config
```

确保有这些设置：

```text
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
```

如果你有固定用户，例如 `deploy`，那就用这个用户登录，不要用 root。

修改后：

```bash
sudo systemctl restart ssh
```

有些发行版服务名是 `sshd`：

```bash
sudo systemctl restart sshd
```

#### 非常重要

在你关闭密码登录之前，先确认：

- 你自己的 SSH key 已经能正常登录

先测试能用 key 登录，再关密码，不然会把自己锁在门外。

#### 你可以怎么验证

1. 用 key 正常登录。
2. 尝试密码登录，应失败。
3. 尝试 root 登录，应失败。

## 2. 强烈建议做

### 2.1 只开放最少的网络入口

如果是云主机：

- 安全组只开放 `22`（如必须）和必要 Web 入口
- 不对公网直接开放 `8000`

如果是家庭网络：

- 不做路由器端口映射
- 后端通过 Tunnel 暴露，不通过公网 NAT 暴露

#### 具体怎么做

##### 云主机

在安全组或防火墙中，建议保留：

- `22/tcp`，最好只允许你的办公 IP 或家庭 IP
- `80/443`，如果你自己还运行其他公开 Web 服务

不要保留：

- `8000/tcp` 对全网开放

##### Linux 机器本地防火墙

如果你用 UFW，可以做成：

```bash
sudo ufw default deny incoming
sudo ufw allow from <your-ip> to any port 22 proto tcp
sudo ufw enable
```

如果你的机器只是 Tunnel origin，很多情况下你甚至不需要开放 `80/443`。

### 2.2 定期更新系统和依赖

至少要覆盖：

- 操作系统安全更新
- Docker / container runtime
- Python 依赖
- `ffmpeg`
- `cloudflared`

#### 具体怎么做

##### Debian / Ubuntu

```bash
sudo apt update
sudo apt upgrade -y
```

##### Docker 镜像

定期重建：

```bash
docker compose build --no-cache backend
docker compose up -d
```

##### Python 依赖

定期检查：

```bash
pip list --outdated
```

##### cloudflared

至少每隔一段时间检查版本，避免 tunnel 组件过旧。

### 2.3 清理工作目录

你这个项目会持续产生：

- 上传原文件
- 音频中间文件
- SRT
- 输出视频

如果不清理，磁盘迟早被打满。

#### 最简单的清理策略

只保留最近 3 到 7 天的任务目录。

假设你的工作目录是：

```text
/data/workdir
```

可以每天执行一次：

```bash
find /data/workdir -mindepth 1 -maxdepth 1 -type d -mtime +7 -exec rm -rf {} +
```

#### 怎么安全一点

先只打印，不删除：

```bash
find /data/workdir -mindepth 1 -maxdepth 1 -type d -mtime +7
```

确认没问题，再做删除。

#### 更推荐的做法

用定时任务：

```bash
crontab -e
```

例如每天凌晨 3 点清理：

```cron
0 3 * * * find /data/workdir -mindepth 1 -maxdepth 1 -type d -mtime +7 -exec rm -rf {} +
```

### 2.4 控制并发任务数

视频转写和烧录属于重任务，不能无限并发。

#### 最小策略

先定一个简单规则：

- 同一用户最多 1 到 2 个处理中任务
- 全局最多 1 到 3 个处理中任务

#### 当前阶段怎么落地

如果你还没做用户系统，至少可以先：

- 用 API key 维度限制
- 或者仅允许你自己使用

即使暂时不改代码，也要把这条视为下一步必须补的能力，因为它直接影响可用性和成本。

### 2.5 记录基础审计日志

至少记录：

- 请求时间
- 来源 IP
- 用户或 key 标识
- 上传文件大小
- job 创建时间
- job 成功/失败状态

#### 当前项目最小做法

如果你暂时不接日志平台，至少保留：

- 应用 stdout/stderr 日志
- 反向代理或 tunnel 日志
- 任务状态日志

并确保这些日志至少能回答：

- 是谁在什么时间上传了文件
- 是谁创建了 job
- 哪个 job 失败了

## 3. 建议尽快补

### 3.1 文件类型校验

不要只信前端传来的文件名。

#### 最小做法

至少同时检查：

- 文件扩展名
- MIME type
- `ffprobe` 能否正常识别

#### 验证思路

如果用户上传一个假装成 `.mp4` 的非视频文件，后端应该：

- 直接拒绝
- 返回明确错误

而不是继续进入 ASR 和 ffmpeg 流程。

### 3.2 错误信息不要泄露内部细节

生产环境不要把这些直接暴露给用户：

- 本机绝对路径
- 内部容器路径
- 完整堆栈
- 密钥信息

#### 如何判断自己有没有泄露

你可以故意制造一个失败请求，然后看前端拿到的报错里是否出现：

- `/data/workdir/...`
- `/app/...`
- `Traceback (most recent call last)`
- 具体 token 值

如果有，就说明还需要收口。

### 3.3 给服务设置资源监控

至少关注：

- CPU
- 内存
- 磁盘使用率
- 任务执行时长

#### 最简单的起步方式

在服务器上定期看：

```bash
top
htop
df -h
free -h
docker stats
```

如果你跑在 Docker 里，`docker stats` 特别有用。

#### 你为什么现在就要关心它

因为你这个服务不是“普通 CRUD API”，而是：

- ffmpeg
- whisper
- 文件上传
- 磁盘写入

很多失败不是代码 bug，而是资源被打满。

## 4. 以后再做

### 4.1 更细粒度权限模型

如果以后要给多人使用，再考虑：

- 用户体系
- 配额系统
- 角色权限
- 每日用量限制

### 4.2 WAF / Bot 防护

如果以后公网开放给更多人：

- Cloudflare WAF
- Bot 防护
- Managed Challenge

### 4.3 对象存储替代本地落盘

如果以后文件量变大，可以考虑：

- 上传到对象存储
- 结果文件也放对象存储
- 本机只做临时处理

这样能减轻磁盘风险，但不是当前阶段必须项。

## 5. 按当前项目的推荐优先级

### 先做

- [ ] 后端只通过 Cloudflare Tunnel 暴露
- [ ] 后端入口启用 Cloudflare Access
- [ ] 开启 Protect with Access
- [ ] 上传接口限流
- [ ] 上传大小限制
- [ ] `/uploads` 和 `/jobs` 加鉴权
- [ ] 服务器 SSH 只允许密钥登录
- [ ] `WORKDIR_ROOT` 建立清理策略

### 再做

- [ ] 并发任务限制
- [ ] 基础审计日志
- [ ] 文件类型校验
- [ ] 资源监控

### 以后再做

- [ ] 用户配额系统
- [ ] WAF / Bot 防护
- [ ] 对象存储分层

## 6. 最小落地版本

如果你现在只想先做一个“够安全、又不太重”的版本，建议按这个顺序：

1. 后端不开放公网 `8000`
2. 后端只通过 Cloudflare Tunnel 暴露
3. 后端域名加 Cloudflare Access
4. 开 `Protect with Access`
5. 给 `/api/v1/uploads` 和 `/api/v1/jobs` 配 Cloudflare 限流
6. 给后端加一层 `X-API-Key`
7. SSH 禁 root、禁密码登录
8. 每天清理旧的 `WORKDIR_ROOT`

做到这 8 条，你这套“Cloudflare 前端 + 自托管重计算后端”的安全基线就已经比绝大多数裸露公网端口的做法稳很多了。

## 7. 参考资料

- Cloudflare Access controls: <https://developers.cloudflare.com/cloudflare-one/access-controls/>
- Publish a self-hosted application to the Internet: <https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/self-hosted-public-app/>
- Configure self-hosted apps: <https://developers.cloudflare.com/cloudflare-one/applications/configure-apps/self-hosted-apps/>
- Cloudflare rate limiting rules: <https://developers.cloudflare.com/waf/rate-limiting-rules/>
