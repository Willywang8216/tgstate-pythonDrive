#!/usr/bin/env bash
set -euo pipefail

# --- 兜底初始化（防止 unbound variable） ---
: "${PORT:=}"
: "${BASE_URL:=}"
: "${NAME:=tgstate}"
: "${VOL:=tgstate-data}"
: "${IMG:=ghcr.io/buyi06/tgstate-python@sha256:e897ce4c2b61e48a13ef0ec025dfd80148ed8669d75f688a1a8d81036fe116e5}"
: "${RESET_WIPE:=}"

# --- 端口交互逻辑 ---
if [ -z "${PORT:-}" ]; then
  if [ -t 0 ]; then
    read -r -p "请输入端口(回车默认8000): " PORT < /dev/tty || true
  fi
fi
PORT="${PORT:-8000}"

case "$PORT" in
  ''|*[!0-9]* ) PORT=8000 ;;
  * ) if [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then PORT=8000; fi ;;
esac

# --- BASE_URL 自动推导 ---
if [ -z "${BASE_URL:-}" ]; then
  PUB="$(curl -fsS --max-time 5 https://api.ipify.org || true)"
  BASE_URL="http://${PUB:-127.0.0.1}:${PORT}"
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "docker 未安装或不可用" >&2
  exit 1
fi

docker rm -f "${NAME}" >/dev/null 2>&1 || true

if [ "${RESET_WIPE:-}" = "1" ]; then
  echo "警告：RESET_WIPE=1，正在删除数据卷 ${VOL}..."
  docker volume rm "${VOL}" >/dev/null 2>&1 || true
  docker volume create "${VOL}" >/dev/null
else
  echo "提示：默认重置保留数据。若需清空数据请 export RESET_WIPE=1"
  docker volume inspect "${VOL}" >/dev/null 2>&1 || docker volume create "${VOL}" >/dev/null
fi

docker pull "${IMG}"

docker run -d --name "${NAME}" --restart unless-stopped \
  -p "${PORT}:8000" \
  -v "${VOL}:/app/data" \
  -e "BASE_URL=${BASE_URL}" \
  "${IMG}" >/dev/null

echo "tgState 已重置并启动"
echo "访问地址：${BASE_URL}"

