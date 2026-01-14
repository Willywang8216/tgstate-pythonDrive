# 开发环境配置指南

本文档说明如何配置 tgState 项目的开发环境。

## 前置要求

- Python 3.11 或更高版本
- Git

## 安装步骤

### 1. 克隆项目

```bash
git clone <repository-url>
cd tgstate-python-main
```

### 2. 创建虚拟环境

**Windows**:
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/macOS**:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填写以下必需的配置：

```env
# 必填：你的 Telegram Bot 的 API Token（从 @BotFather 获取）
BOT_TOKEN=your_bot_token_here

# 必填：文件存储的目标，可以是公开频道的 @username 或你自己的用户 ID
CHANNEL_NAME=@your_channel_name

# 可选：访问 Web 界面的密码。如果留空，则无需密码
PASS_WORD=your_secret_password

# 可选：PicGo 上传接口的 API 密钥。如果留空，则无需密钥
PICGO_API_KEY=your_picgo_api_key

# 可选：你的服务的公开访问 URL，用于生成完整的文件下载链接
# 默认值: http://127.0.0.1:8000
BASE_URL=http://127.0.0.1:8000
```

### 5. 启动服务

```bash
uvicorn app.main:app --reload
```

服务将在 `http://127.0.0.1:8000` 上运行。

**注意**:
- 首次运行时，数据库会自动初始化
- 确保在 `.env` 中正确配置了 `BOT_TOKEN` 和 `CHANNEL_NAME`

## API 路由说明

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/upload` | 上传文件，返回 `{"path": "/d/{file_id}/{filename}", "url": "full_url"}` |
| GET | `/api/files` | 获取文件列表，返回文件数组 |
| GET | `/d/{file_id}/{filename}` | 下载文件 |
| GET | `/api/file-updates` | SSE 实时推送文件更新 |
| DELETE | `/api/files/{file_id}` | 删除文件 |

## 代码质量工具

### Ruff

Ruff 是一个快速的 Python 代码检查器和格式化工具。

**安装**:
```bash
pip install ruff
```

**使用**:
```bash
# 检查代码
ruff check app/

# 自动修复问题
ruff check --fix app/

# 格式化代码
ruff format app/
```

**配置**: 详见 [`pyproject.toml`](../pyproject.toml)

## 性能测试工具

### Locust

Locust 是一个用于负载测试的开源工具。

**安装**:
```bash
pip install locust
```

**使用**:
```bash
# Web UI 模式
locust -f scripts/locustfile.py --host http://127.0.0.1:8000

# 然后访问 http://127.0.0.1:8089 进行控制

# 命令行模式
locust -f scripts/locustfile.py --headless \
  --host http://127.0.0.1:8000 \
  -u 100 \           # 用户数
  -r 10 \             # 每秒启动用户数
  -t 1m \             # 运行时长
  --html report.html  # 生成 HTML 报告
```

**注意事项**:
- 确保服务已启动
- 确保 Telegram Bot 配置正确
- 上传测试会生成随机内存数据，不依赖外部文件
- 下载测试会先请求 `/api/files` 获取可下载文件，没有文件时跳过

### Hey

Hey 是一个简单的 HTTP 负载生成器（需要 Go 环境）。

**安装**:
```bash
# macOS
brew install hey

# Linux
go install github.com/rakyll/hey@latest

# Windows
# 下载预编译二进制文件: https://github.com/rakyll/hey/releases
```

**使用**:
```bash
cd scripts
chmod +x benchmark.sh
./benchmark.sh
```

**环境变量**:
- `BASE_URL`: 服务 URL (默认: http://127.0.0.1:8000)
- `CONCURRENCY`: 并发数 (默认: 10)
- `REQUESTS`: 请求数 (默认: 100)
- `OUTPUT_DIR`: 输出目录 (默认: ./benchmark-results)

**注意事项**:
- 脚本会在以下情况下友好提示并正常退出（退出码 0）:
  - 服务未启动
  - hey 未安装
  - 无可下载文件
  - 无测试文件
- 上传/下载测试使用 curl 进行最小可复现测试
- GET /api/files 测试使用 hey 进行压测

## 开发工作流

### 1. 代码检查

在提交代码前，运行以下命令：

```bash
# 检查代码
ruff check app/

# 格式化代码
ruff format app/
```

### 2. 运行测试

```bash
# 运行单元测试（如果有）
pytest

# 运行性能测试
locust -f scripts/locustfile.py --host http://127.0.0.1:8000
```

### 3. 提交代码

```bash
git add .
git commit -m "feat: 添加新功能"
git push
```

## 常见问题

### 问题: Python 命令未找到

**解决方案**:
- Windows: 从 [Python 官网](https://www.python.org/downloads/) 下载安装
- Linux/macOS: 使用包管理器安装

### 问题: 虚拟环境激活失败

**解决方案**:
- Windows: 确保使用 `venv\Scripts\activate`
- Linux/macOS: 确保使用 `source venv/bin/activate`

### 问题: 依赖安装失败

**解决方案**:
```bash
# 升级 pip
pip install --upgrade pip

# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题: 服务启动失败

**解决方案**:
1. 检查 `.env` 文件配置是否正确
2. 确保 `BOT_TOKEN` 和 `CHANNEL_NAME` 已填写
3. 检查端口 8000 是否被占用
4. 查看错误日志

### 问题: Telegram Bot 无法连接

**解决方案**:
1. 检查 `BOT_TOKEN` 是否正确
2. 检查 `CHANNEL_NAME` 是否正确
3. 确保 Bot 有权限访问频道

### 问题: hey 命令未找到

**解决方案**:
```bash
# macOS
brew install hey

# Linux
go install github.com/rakyll/hey@latest
export PATH=$PATH:~/go/bin
```

### 问题: benchmark.sh 提示服务未启动

**解决方案**:
1. 确保服务已启动: `uvicorn app.main:app --reload`
2. 检查 BASE_URL 配置是否正确
3. 使用 curl 测试: `curl http://127.0.0.1:8000/api/files`

## 目录结构

```
tgstate-python-main/
├── app/                    # 应用代码
│   ├── api/               # API 路由
│   ├── core/              # 核心配置
│   ├── services/          # 业务服务
│   ├── static/            # 静态文件
│   ├── templates/         # 模板文件
│   ├── bot_handler.py     # Bot 处理器
│   ├── database.py        # 数据库
│   ├── events.py          # 事件处理
│   ├── main.py            # 应用入口
│   └── pages.py           # 页面路由
├── docs/                  # 文档
├── scripts/               # 脚本
├── .env.example          # 环境变量示例
├── requirements.txt      # Python 依赖
├── pyproject.toml       # 项目配置
└── README.md            # 项目说明
```

## 下一步

- 阅读项目 [`README.md`](../README.md)
- 查看 [`性能评估报告`](perf-assessment.md)
- 了解 [`性能测试指南`](perf.md)
