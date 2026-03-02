#!/bin/bash

# ==========================================
# 自动化启动脚本：Compliance Reasoning Agent
# ==========================================

# 输出带颜色的日志
green() { echo -e "\033[32m$1\033[0m"; }
yellow() { echo -e "\033[33m$1\033[0m"; }
red() { echo -e "\033[31m$1\033[0m"; }

green "🚀 开始启动 Compliance Reasoning Agent..."

# 检查 .env 文件是否存在
if [ ! -f .env ]; then
    yellow "⚠️ 未找到 .env 文件，如果需要设置环境变量请先配置。"
fi

# 1. 启动 FastAPI 后端
green "启动 FastAPI 后端服务..."
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
yellow "👉 后端服务正在启动 (PID: $BACKEND_PID)..."

# 稍作等待以确保后端先跑起来
sleep 2

# 2. 启动 Streamlit 前端
green "启动 Streamlit 前端界面..."
uv run streamlit run frontend/app.py --server.port 8501 &
FRONTEND_PID=$!
yellow "👉 前端服务正在启动 (PID: $FRONTEND_PID)..."

green "✨ 启动指令已下发！"
echo "=========================================="
echo "后端 API: http://localhost:8000/docs (Swagger)"
echo "前端面板: http://localhost:8501"
echo "=========================================="
yellow "提示：按 Ctrl+C 即可同时停止两个服务运行。"

# 3. 拦截 Ctrl+C 进行清理
cleanup() {
    red "接收到终止信号，正在关闭服务..."
    kill $BACKEND_PID
    kill $FRONTEND_PID
    green "👋 服务已完全关闭"
    exit 0
}

# 捕获 SIGINT (Ctrl+C) 和 SIGTERM
trap cleanup SIGINT SIGTERM

# 等待后台进程
wait
