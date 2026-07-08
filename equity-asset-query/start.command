#!/bin/bash
# 股权资产管理查询工具 - 一键启动脚本（双击运行）
# 功能：进入项目目录 -> 安装依赖(首次) -> 启动服务 -> 自动打开浏览器

# 切到脚本所在目录（无论从哪里双击都正确）
cd "$(dirname "$0")" || exit 1

PORT=5001
URL="http://127.0.0.1:${PORT}"

echo "=============================================="
echo "  股权资产管理 · 台账查询工具"
echo "  目录: $(pwd)"
echo "=============================================="

# 选择可用的 python
PY="$(command -v python3 || command -v python)"
if [ -z "$PY" ]; then
  echo "[错误] 未找到 python3，请先安装 Python 3。"
  read -n 1 -s -r -p "按任意键关闭..."
  exit 1
fi
echo "[1/3] 使用 Python: $PY"

# 安装依赖（缺失才装）
if ! "$PY" -c "import flask, requests" >/dev/null 2>&1; then
  echo "[2/3] 首次运行，正在安装依赖 (flask, requests)..."
  "$PY" -m pip install -r requirements.txt --quiet --break-system-packages 2>/dev/null \
    || "$PY" -m pip install -r requirements.txt --quiet
else
  echo "[2/3] 依赖已就绪，跳过安装。"
fi

# 3 秒后自动打开浏览器（等服务起来）
( sleep 3; open "$URL" ) &

echo "[3/3] 启动服务: ${URL}"
echo "----------------------------------------------"
echo "  浏览器会自动打开；如未打开请手动访问上面地址。"
echo "  停止服务：在本窗口按 Control + C"
echo "----------------------------------------------"

# 前台启动（关掉窗口或 Ctrl+C 即停止）
exec "$PY" app.py
