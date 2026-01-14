# tgState V2 - Python 版

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)[![Framework](https://img.shields.io/badge/Framework-FastAPI-green.svg)](https://fastapi.tiangolo.com/)[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

`tgState` 原项目链接[csznet/tgState](https://github.com/csznet/tgState)，使用fastapi重构。

##### 增加前端网盘页面管理文件。

##### 增加前端图床页面方便复制。

##### 增加自动识别群组内文件添加至前端网盘显示。

## 功能特性

*   **无限存储**: 利用 Telegram 的云服务作为您的私人文件仓库。
*   **永久图床**：只要服务还在运行，图床永不失效。
*   **现代化 UI**: 一个简洁、响应式且用户友好的网页界面，用于上传和管理文件。
*   **轻松部署**: 只需几分钟即可使用 Docker 完成部署，或在本地直接运行。
*   **直接链接**: 为每个上传的文件生成一个可直接分享的链接。
*   **大文件支持**: 自动处理大文件分块上传。
*   **密码保护**: 可选的密码保护机制，确保您的 Web 界面安全。

<img src="https://tgstate.justhil.uk/d/410:BQACAgEAAyEGAASW4jjnAAIBmmh3ku0_aJ2x-lqrh7jWkRDzLSIQAAKbBAACKlfBRwdEPuNk9gfKNgQ/%E4%B8%BB%E9%A1%B5.png" style="zoom:50%;" />
<img src="https://tgstate.justhil.uk/d/409:BQACAgEAAyEGAASW4jjnAAIBmWh3kuxPT5LfidK42mn0i8iRhTDiAAKaBAACKlfBR2NtAAFcUYplmDYE/%E5%9B%BE%E5%BA%8A.png" style="zoom:50%;" />







##  快速开始

推荐使用 Docker 来部署 `tgState`，这是最简单快捷的方式。

### 使用 Docker 部署

#### 一键启动（零参数）

```bash
docker build -t tgstate:latest .
docker run -d -p 8000:8000 tgstate:latest
```

启动后打开 `http://127.0.0.1:8000/` 会自动进入 **Setup** 页面（`/settings`），填写 BOT_TOKEN、CHANNEL_NAME、PASS_WORD 等配置后即可启用全部功能（无需重启）。

#### 数据持久化（可选）

默认数据落盘到容器内 `/app/data`（SQLite 等）。可选挂载 volume：

```bash
docker run -d -p 8000:8000 -v tgstate-data:/app/data tgstate:latest
```

```bash
docker run -d \
  --name tgstate \
  -p 8000:8000 \
  -e BOT_TOKEN="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11" \
  -e CHANNEL_NAME="@my_test_channel" \
  -e PASS_WORD="supersecret" \
  -e BASE_URL="https://my-service.com" \
  -e PICGO_API_KEY="supersecret(可选不需要就删除这行)" \
  mitu233/python-tgstate:latest
```


### 本地开发与运行

如果您希望在本地环境直接运行 `tgState`：

1. **克隆项目并进入目录**:

   ```bash
   git clone https://github.com/your-repo/python-tgstate.git
   cd python-tgstate
   ```

2. **创建并激活虚拟环境**:

   ```bash
   # 创建虚拟环境
   python -m venv venv
   # 激活虚拟环境 (Windows)
   venv\Scripts\activate
   # 激活虚拟环境 (Linux/macOS)
   # source venv/bin/activate
   ```

3. **安装依赖**:

   ```bash
   pip install -r requirements.txt
   ```

4. **创建 `.env` 配置文件**: 参照 Docker 部分的说明，在项目根目录创建并配置 `.env` 文件。

5. **启动应用**:

   ```bash
   uvicorn app.main:app --reload
   ```

   如果没有配置域名应用将在 `http://127.0.0.1:8000` 上运行。

##  配置 (环境变量)

`tgState` 通过环境变量进行配置，应用会从根目录的 `.env` 文件中自动加载这些变量。

| 变量            | 描述                                                         | 是否必须 | 默认值                  |
| --------------- | ------------------------------------------------------------ | -------- | ----------------------- |
| `BOT_TOKEN`     | 您的 Telegram Bot API 令牌。可以从 [@BotFather](https://t.me/BotFather) 获取。 | **是**   | `None`                  |
| `CHANNEL_NAME`  | 用于文件存储的目标聊天/频道。可以是公共频道的 `@username` 。 | **是**   | `None`                  |
| `PASS_WORD`     | 用于保护 Web 界面访问的密码。如果留空，则应用将公开访问，无需密码。 | 否       | `None`                  |
| `BASE_URL`      | 您的服务的公共 URL。用于生成完整的下载链接。                 | 否       | `http://127.0.0.1:8000` |
| `PICGO_API_KEY` | 用于 PicGo 上传接口的 API 密钥。                             | 否       | `None`                  |

## 注意密码相关

1. **两个密码都【没有】设置**：
   - **处理方式**：完全开放。
   - **结果**：无论是通过 Picogo/API 还是网页，**均可直接上传**，无需任何凭证。
2. **只设置了【Picogo密码】**：
   - **结果**：来自网页的上传请求会无条件允许。来自 Picogo/API 的请求会验证后允许。
3. **只设置了【登录密码】**：
   - **结果**：来自网页的上传只有**已登录**的网页用户能上传。来自 Picogo/API 的请求会无条件允许。

## 使用方法

1. **访问 Web 界面**: 启动应用后，在浏览器中访问 `http://127.0.0.1:8000` (或您配置的 `BASE_URL`)。

2. **密码验证**: 如果您在 `.env` 文件中设置了 `PASS_WORD`，应用会首先跳转到密码输入页面。输入正确密码后即可访问主界面。

3. **上传文件**: 在主界面，点击上传区域选择文件，或直接将文件拖拽到上传框中。上传成功后，文件会出现在下方的文件列表中。

4. **群组上传**支持转发到群组上传，支持小于20m的文件和照片（tg官方的限制）。

5. **获取链接**: 文件列表中的每个文件都会显示其文件名、大小和上传日期。点击文件名即可复制该文件的直接下载链接。

6. **群组获取链接: **群组中回复文件get获取下载链接

   <img src="https://tgstate.justhil.uk/d/408:BQACAgEAAyEGAASW4jjnAAIBmGh3kuqRumdoYCUgg1KdxhmnU_3xAAKZBAACKlfBR9JpqfvggtR8NgQ/%E7%BE%A4%E7%BB%84%E5%9B%9E%E5%A4%8D.png" style="zoom:50%;" />

## UI 说明

- Files（主页 `/`）：上传区、搜索、批量复制链接/删除、实时列表更新（SSE）
- Images（图床 `/image_hosting`）：图片网格、URL/Markdown/HTML 一键复制、批量删除
- Settings（设置 `/settings`）：设置登录密码
- Share（分享页 `/share/{file_id}`）：多种格式的可分享链接

## SSE 实时更新说明

- 前端通过 `/api/file-updates` 订阅事件；后端采用广播式 pub-sub，多标签页/多客户端会同时收到更新。
- 事件结构为 JSON：`{action, file_id, filename, filesize, upload_date}`，其中 `upload_date` 为 UTC ISO8601。
- 连接会定期发送 keepalive comment，提升在反代/云平台下稳定性。
- 反代建议（Nginx 示例）：关闭缓冲与压缩，避免 SSE 被合并/阻塞。
  - `proxy_buffering off;`
  - `gzip off;`

## 上传鉴权规则（Web vs API）

`/api/upload` 同时服务网页上传与 PicGo/API 上传，依据请求来源与密码组合决定是否放行：

- Web 请求判断：请求头中包含 `Referer` 视为 Web 上传；否则视为 API 调用。
- 密码组合规则：
  1. 两个密码都未设置：Web/API 全开放。
  2. 只设置 PICGO_API_KEY：Web 全开放；API 需提供 `x-api-key` 头或 `key` 表单字段。
  3. 只设置 PASS_WORD：Web 需登录 Cookie；API 全开放。
  4. 两个都设置：Web 需登录 Cookie；API 需提供 API Key。

## PicGo 配置指南

### 前置要求

1. 安装插件web-uploader

### 核心配置

1. **图床配置名**: 随便

2. **api地址**: 填写你的服务提供的上传地址。本地是 `http://<你的服务器IP>:8000/api/upload`。

3. **POST参数名**: `file`。

4. **JSON 参数名**: `url`。

5. **自定义请求头**：{"x-api-key": "PICGO_API_KEY"}（可选推荐）(验证方式二选一)

6. **自定义body**：{"key":"PICGO_API_KEY"}（可选推荐）(验证方式二选一)

   <img src="https://tgstate.justhil.uk/d/407:BQACAgEAAyEGAASW4jjnAAIBl2h3kujY6McRWgIztAAB2mabiph9YgACmAQAAipXwUcH3E_AI0NrhDYE/picgo.png" style="zoom:80%;" />



### 目前缺点

1. 若要同步“群组/频道内删除消息”到前端列表，Bot 需要管理员权限以接收删除相关更新。

## 常见问题

### 1) 浏览器打开多个标签页，为什么只有一个页面会更新？
已修复：后端 SSE 采用广播式 pub-sub，每个连接独立队列，事件会广播到所有订阅者。

### 2) 反代/云平台下 SSE 经常断开或不更新
建议关闭反代缓冲与压缩（例如 Nginx `proxy_buffering off; gzip off;`），并确保响应为 `text/event-stream`。

### 3) Windows 下提示 Python not found（跳微软商店）
关闭 Windows 的 “App execution aliases” 中的 Python 相关开关，或确保 Python 已正确安装并在 PATH 中可用。

### 4) 如何重置配置
- Web：进入 `/settings` 点击“重置配置”
- 文件：删除数据目录中的 SQLite 文件（Docker 默认 `/app/data/file_metadata.db`）

## 开发与测试

### 代码质量检查

项目使用 ruff 进行代码格式化和静态检查：

```bash
# 检查代码
ruff check app/

# 自动修复问题
ruff check --fix app/

# 格式化代码
ruff format app/
```

### 性能测试

项目提供了性能测试脚本，用于评估服务性能：

```bash
# 使用 hey 进行快速基准测试
cd scripts
chmod +x benchmark.sh
./benchmark.sh

# 使用 Locust 进行复杂场景压测
locust -f scripts/locustfile.py --host http://127.0.0.1:8000
```

详细说明请参考 [scripts/README.md](scripts/README.md) 和 [docs/perf.md](docs/perf.md)。

### 性能评估

详细的性能评估报告请参考 [docs/perf-assessment.md](docs/perf-assessment.md)。

用 roocode 和 白嫖的心 制作。****
