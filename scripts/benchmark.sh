#!/bin/bash
# tgState 性能基准测试脚本
# 使用 hey 进行 HTTP 压力测试

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 默认配置
BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
CONCURRENCY="${CONCURRENCY:-10}"
REQUESTS="${REQUESTS:-100}"
OUTPUT_DIR="${OUTPUT_DIR:-./benchmark-results}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

# 输出文件
SUMMARY_FILE="$OUTPUT_DIR/summary_$TIMESTAMP.txt"
LIST_LOG="$OUTPUT_DIR/list_$TIMESTAMP.log"
UPLOAD_LOG="$OUTPUT_DIR/upload_$TIMESTAMP.log"
DOWNLOAD_LOG="$OUTPUT_DIR/download_$TIMESTAMP.log"

# 检查 hey 是否安装
if ! command -v hey > /dev/null 2>&1; then
    echo -e "${YELLOW}警告: hey 未安装${NC}"
    echo "请安装 hey:"
    echo "  macOS:   brew install hey"
    echo "  Linux:   go install github.com/rakyll/hey@latest"
    echo "  Windows:  下载预编译二进制文件: https://github.com/rakyll/hey/releases"
    echo ""
    echo -e "${GREEN}跳过 hey 压测，继续使用 curl 进行最小测试...${NC}"
    HEY_AVAILABLE=false
else
    HEY_AVAILABLE=true
fi

# 检查服务是否运行
echo -e "${YELLOW}检查服务状态...${NC}"
if ! curl -s -f "$BASE_URL/api/files" > /dev/null 2>&1; then
    echo -e "${YELLOW}警告: 服务未运行或无法访问 $BASE_URL${NC}"
    echo "请先启动服务: uvicorn app.main:app --reload"
    echo ""
    echo -e "${GREEN}测试已跳过（服务未启动）${NC}"
    exit 0
fi
echo -e "${GREEN}✓ 服务运行正常${NC}"
echo "" | tee "$SUMMARY_FILE"

echo "========================================" | tee "$SUMMARY_FILE"
echo "tgState 性能基准测试" | tee -a "$SUMMARY_FILE"
echo "========================================" | tee -a "$SUMMARY_FILE"
echo "时间: $(date)" | tee -a "$SUMMARY_FILE"
echo "目标 URL: $BASE_URL" | tee -a "$SUMMARY_FILE"
echo "并发数: $CONCURRENCY" | tee -a "$SUMMARY_FILE"
echo "请求数: $REQUESTS" | tee -a "$SUMMARY_FILE"
echo "========================================" | tee -a "$SUMMARY_FILE"
echo "" | tee -a "$SUMMARY_FILE"

# 测试 1: 文件列表接口 (使用 hey)
echo -e "${YELLOW}测试 1/3: 文件列表接口 (GET /api/files)${NC}"
echo "----------------------------------------" | tee -a "$SUMMARY_FILE"
echo "测试: GET /api/files" | tee -a "$SUMMARY_FILE"
echo "----------------------------------------" | tee -a "$SUMMARY_FILE"

if [ "$HEY_AVAILABLE" = true ]; then
    hey -n "$REQUESTS" -c "$CONCURRENCY" -m GET "$BASE_URL/api/files" | tee "$LIST_LOG" | tee -a "$SUMMARY_FILE"
else
    echo -e "${YELLOW}使用 curl 进行单次测试...${NC}"
    curl -s -w "\nHTTP Status: %{http_code}\nTime: %{time_total}s\n" "$BASE_URL/api/files" | tee -a "$SUMMARY_FILE"
fi

echo "" | tee -a "$SUMMARY_FILE"

# 测试 2: 文件上传接口 (使用 curl)
echo -e "${YELLOW}测试 2/3: 文件上传接口 (POST /api/upload)${NC}"
echo "----------------------------------------" | tee -a "$SUMMARY_FILE"
echo "测试: POST /api/upload (小文件)" | tee -a "$SUMMARY_FILE"
echo "----------------------------------------" | tee -a "$SUMMARY_FILE"

# 创建测试文件
TEST_FILE="$OUTPUT_DIR/test_file_$TIMESTAMP.txt"
echo "This is a test file for benchmarking." > "$TEST_FILE"
echo "Timestamp: $(date)" >> "$TEST_FILE"

UPLOAD_START=$(date +%s%N)
UPLOAD_RESPONSE=$(curl -s -w "\n%{http_code}\n%{time_total}\n" -X POST \
    -F "file=@$TEST_FILE" \
    "$BASE_URL/api/upload")
UPLOAD_END=$(date +%s%N)
UPLOAD_TIME=$(( (UPLOAD_END - UPLOAD_START) / 1000000 )) # 转换为毫秒

echo "上传响应:" | tee -a "$SUMMARY_FILE"
echo "$UPLOAD_RESPONSE" | tee -a "$SUMMARY_FILE"
echo "上传耗时: ${UPLOAD_TIME}ms" | tee -a "$SUMMARY_FILE"
echo "" | tee -a "$SUMMARY_FILE"

# 提取上传的文件 ID 用于下载测试
FILE_ID=$(echo "$UPLOAD_RESPONSE" | grep -oP '(?<="path":")[^"]*' | head -1)

if [ -z "$FILE_ID" ]; then
    echo -e "${YELLOW}警告: 无法获取文件 ID，跳过下载测试${NC}"
else
    # 测试 3: 文件下载接口 (使用 hey)
    echo -e "${YELLOW}测试 3/3: 文件下载接口 (GET /d/{file_id}/{filename})${NC}"
    echo "----------------------------------------" | tee -a "$SUMMARY_FILE"
    echo "测试: GET $BASE_URL$FILE_ID" | tee -a "$SUMMARY_FILE"
    echo "----------------------------------------" | tee -a "$SUMMARY_FILE"

    if [ "$HEY_AVAILABLE" = true ]; then
        hey -n "$REQUESTS" -c "$CONCURRENCY" -m GET "$BASE_URL$FILE_ID" | tee "$DOWNLOAD_LOG" | tee -a "$SUMMARY_FILE"
    else
        echo -e "${YELLOW}使用 curl 进行单次测试...${NC}"
        curl -s -w "\nHTTP Status: %{http_code}\nTime: %{time_total}s\n" "$BASE_URL$FILE_ID" | tee -a "$SUMMARY_FILE"
    fi

    echo "" | tee -a "$SUMMARY_FILE"
fi

# 测试 4: CPU 和内存监控
echo -e "${YELLOW}系统资源监控${NC}"
echo "----------------------------------------" | tee -a "$SUMMARY_FILE"

if command -v ps > /dev/null 2>&1; then
    echo "CPU 和内存使用情况:" | tee -a "$SUMMARY_FILE"
    ps aux | grep -E "(uvicorn|python)" | grep -v grep | tee -a "$SUMMARY_FILE" || echo "未找到进程"
fi

echo "" | tee -a "$SUMMARY_FILE"

# 清理测试文件
rm -f "$TEST_FILE"

echo "========================================" | tee -a "$SUMMARY_FILE"
echo -e "${GREEN}测试完成！${NC}" | tee -a "$SUMMARY_FILE"
echo "详细日志保存在: $OUTPUT_DIR" | tee -a "$SUMMARY_FILE"
echo "========================================" | tee -a "$SUMMARY_FILE"

# 生成简短摘要
echo ""
echo "========================================"
echo "快速摘要"
echo "========================================"

if [ "$HEY_AVAILABLE" = true ] && [ -f "$LIST_LOG" ]; then
    echo -e "${GREEN}文件列表接口:${NC}"
    grep -E "(Requests/sec|Average|P95|P99)" "$LIST_LOG" | head -4
fi

if [ "$HEY_AVAILABLE" = true ] && [ -f "$DOWNLOAD_LOG" ]; then
    echo -e "${GREEN}文件下载接口:${NC}"
    grep -E "(Requests/sec|Average|P95|P99)" "$DOWNLOAD_LOG" | head -4
fi

echo ""
echo "完整报告: $SUMMARY_FILE"
