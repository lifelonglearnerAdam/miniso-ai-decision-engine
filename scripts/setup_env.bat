@echo off
chcp 65001 >nul
echo ========================================
echo  名创优品 AI 决策引擎 — 环境安装脚本
echo  适用于 Windows + RTX 4090
echo ========================================
echo.

:: 1. 检查 Python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python 未安装，请先安装 Python 3.10+
    pause
    exit /b 1
)
echo [OK] Python: 
python --version

:: 2. 创建虚拟环境
echo.
echo [1/4] 创建虚拟环境...
if not exist venv (
    python -m venv venv
    echo [OK] 虚拟环境已创建
) else (
    echo [SKIP] 虚拟环境已存在
)

:: 3. 激活虚拟环境并安装依赖
echo.
echo [2/4] 安装 Python 依赖...
call venv\Scripts\activate.bat
pip install -r requirements.txt -q
echo [OK] 依赖安装完成

:: 4. 检查 Ollama
echo.
echo [3/4] 检查 Ollama...
where ollama >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [WARN] Ollama 未安装
    echo   请访问 https://ollama.com/download 下载安装
    echo   安装后在终端运行:
    echo     ollama pull qwen2.5:14b
    echo     ollama pull bge-m3
) else (
    echo [OK] Ollama: 
    ollama --version
    echo   请确保已拉取模型:
    echo     ollama pull qwen2.5:14b
    echo     ollama pull bge-m3
)

:: 5. 运行回测
echo.
echo [4/4] 运行回测测试...
python scripts/run_backtest.py

echo.
echo ========================================
echo  环境安装完成！
echo  运行完整管线: python src/pipeline/run_all.py
echo ========================================
pause
