# 性能测试脚本说明

本目录包含 tgState 项目的性能测试脚本和配置。

## 目录结构

```
scripts/
├── benchmark.sh      # 使用 hey 的基准测试脚本
├── locustfile.py     # Locust 压测配置文件
└── README.md         # 本文件
```

## 前置要求

### 1. 使用 hey 进行压测

**安装 hey**:

**macOS**:
```bash
brew install hey
```

**Linux (Ubuntu/Debian)**:
```bash
# 先安装 Go
sudo apt update
sudo apt install golang-go

# 安装 hey
go install github.com/rakyll/hey@latest

# 添加到 PATH
export PATH=$PATH:~/go/bin
```

**Windows**:
- 下载预编译二进制文件: https://github.com/rakyll/hey/releases
- 解压并将 hey.exe 添加到 PATH

### 2. 使用 Locust 进行压测

**安装 Locust**:
```bash
pip install locust
```

## 使用方法

### 方法一：使用 hey (推荐用于快速测试)

```bash
# 进入 scripts 目录
cd scripts

# 赋予执行权限 (Linux/macOS)
chmod +x benchmark.sh

# 运行基准测试
./benchmark.sh

# 自定义参数
BASE_URL=http://localhost:8000 CONCURRENCY=20 REQUESTS=200 ./benchmark.sh
```

**环境变量**:
- `BASE_URL`: 服务 URL (默认: http://127.0.0.1:8000)
- `CONCURRENCY`: 并发数 (默认: 10)
- `REQUESTS`: 请求数 (默认: 100)
- `OUTPUT_DIR`: 输出目录 (默认: ./benchmark-results)

**输出**:
- 测试结果会保存到 `benchmark-results/` 目录
- 包含摘要文件和详细日志

**注意事项**:
- 脚本会在以下情况下友好提示并正常退出（退出码 0）:
  - 服务未启动
  - hey 未安装
  - 无可下载文件
  - 无测试文件
- 上传/下载测试使用 curl 进行最小可复现测试
- GET /api/files 测试使用 hey 进行压测

### 方法二：使用 Locust (推荐用于复杂场景)

```bash
# 方式 1: Web UI 模式
locust -f scripts/locustfile.py --host http://127.0.0.1:8000

# 然后访问 http://127.0.0.1:8089 进行控制

# 方式 2: 命令行模式
locust -f scripts/locustfile.py --headless \
  --host http://127.0.0.1:8000 \
  -u 100 \           # 用户数
  -r 10 \             # 每秒启动用户数
  -t 1m \             # 运行时长
  --html report.html  # 生成 HTML 报告
```

**Locust 参数**:
- `-u, --users`: 并发用户数
- `-r, --spawn-rate`: 每秒启动用户数
- `-t, --run-time`: 运行时长 (如 1m, 10s, 1h)
- `--headless`: 无头模式，不启动 Web UI
- `--html`: 生成 HTML 报告

**注意事项**:
- 上传测试使用内存随机 bytes 生成，不依赖外部文件
- 下载测试会先请求 `/api/files` 获取可下载文件，没有文件时跳过且不报错
- 失败请求会在 Locust UI 统计中可见

## 测试场景

### 1. 文件列表接口 (GET /api/files)
- 测试目的: 评估文件列表查询性能
- 测试方法: 并发请求文件列表
- 关键指标: QPS、P95/P99 延迟

### 2. 文件上传接口 (POST /api/upload)
- 测试目的: 评估文件上传性能
- 测试方法: 单次上传测试 (hey 不支持文件上传)
- 关键指标: 上传时间

### 3. 文件下载接口 (GET /d/{file_id}/{filename})
- 测试目的: 评估文件下载性能
- 测试方法: 并发下载已上传的文件
- 关键指标: QPS、P95/P99 延迟

## 性能指标说明

| 指标 | 说明 |
|------|------|
| QPS (Requests/sec) | 每秒请求数 |
| Average | 平均响应时间 |
| Median | 中位数响应时间 |
| P95 | 95% 的请求响应时间低于此值 |
| P99 | 99% 的请求响应时间低于此值 |
| Min/Max | 最小/最大响应时间 |

## 常见问题

### 问题: hey 命令未找到

**解决方案**:

**macOS**:
```bash
brew install hey
```

**Linux (Ubuntu/Debian)**:
```bash
# 安装 Go
sudo apt update
sudo apt install golang-go

# 安装 hey
go install github.com/rakyll/hey@latest

# 添加到 PATH
export PATH=$PATH:~/go/bin
```

**Windows**:
- 下载预编译二进制文件: https://github.com/rakyll/hey/releases
- 解压并将 hey.exe 添加到 PATH

### 问题: locust 命令未找到

**解决方案**:
```bash
pip install locust
```

### 问题: 服务无法访问

**解决方案**:
1. 检查服务是否启动: `curl http://127.0.0.1:8000/api/files`
2. 检查防火墙设置
3. 检查 BASE_URL 配置

### 问题: 上传测试失败

**解决方案**:
1. 检查 Telegram Bot 配置
2. 检查 CHANNEL_NAME 配置
3. 查看服务日志获取详细错误信息

### 问题: benchmark.sh 提示服务未启动

**解决方案**:
1. 确保服务已启动: `uvicorn app.main:app --reload`
2. 检查 BASE_URL 配置是否正确
3. 使用 curl 测试: `curl http://127.0.0.1:8000/api/files`

### 问题: Locust 下载任务失败

**解决方案**:
1. 确保数据库中有文件数据
2. 检查文件 ID 格式是否正确
3. 查看服务日志获取详细错误信息

## 扩展测试

如需添加更多测试场景，可以修改 `locustfile.py` 文件：

```python
@task(1)
def custom_test(self):
    # 自定义测试逻辑
    with self.client.get("/your/endpoint", catch_response=True) as response:
        if response.status_code == 200:
            response.success()
        else:
            response.failure(f"Got status code {response.status_code}")
```

## 参考文档

- [hey GitHub](https://github.com/rakyll/hey)
- [Locust 官方文档](https://docs.locust.io/)
- [FastAPI 性能优化](https://fastapi.tiangolo.com/advanced/)
