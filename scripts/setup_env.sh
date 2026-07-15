#!/bin/bash
# 名创优品 AI 决策引擎 — 环境安装脚本 (Linux/macOS)
# 用法: chmod +x scripts/setup_env.sh && ./scripts/setup_env.sh

set -e

echo "========================================"
echo " 名创优品 AI 决策引擎 — 环境安装脚本"
echo "========================================"

# 1. 检查 Python
echo ""
echo "[1/4] 检查 Python..."
python3 --version || { echo "请安装 Python 3.10+"; exit 1; }

# 2. 创建虚拟环境
echo ""
echo "[2/4] 创建虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "虚拟环境已创建"
else
    echo "虚拟环境已存在，跳过"
fi

# 3. 安装依赖
echo ""
echo "[3/4] 安装 Python 依赖..."
source venv/bin/activate
pip install -r requirements.txt -q
echo "依赖安装完成"

# 4. Ollama
echo ""
echo "[4/4] 检查 Ollama..."
if command -v ollama &> /dev/null; then
    echo "Ollama: $(ollama --version)"
    echo "请确保已拉取模型: ollama pull qwen2.5:14b && ollama pull bge-m3"
else
    echo "请安装 Ollama: curl -fsSL https://ollama.com/install.sh | sh"
    echo "然后拉取模型: ollama pull qwen2.5:14b"
fi

# 5. 运行回测
echo ""
echo "运行回测测试..."
python scripts/run_backtest.py

echo ""
echo "========================================"
echo " 环境安装完成！"
echo " 运行完整管线: python src/pipeline/run_all.py"
echo "========================================"
