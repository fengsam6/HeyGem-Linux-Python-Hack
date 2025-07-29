#!/bin/bash

# Docker容器启动脚本
# 处理依赖安装、路径问题和错误回退

set -e  # 遇到错误立即退出

echo "=========================================="
echo "HeyGem AI Docker Container Starting..."
echo "=========================================="

# 设置工作目录
cd /code

# 显示Python和pip信息
echo "🐍 Python版本："
python --version

echo "📦 当前pip版本："
pip --version

# 升级pip
echo "⬆️ 升级pip..."
python -m pip install --upgrade pip
echo "✅ pip升级完成"

# 安装gunicorn
echo "📥 安装Gunicorn..."
python -m pip install gunicorn>=21.2.0
echo "✅ Gunicorn安装完成"

# 验证gunicorn安装
echo "🔍 验证Gunicorn安装..."
if python -c "import gunicorn; print(f'Gunicorn version: {gunicorn.__version__}')" 2>/dev/null; then
    echo "✅ Gunicorn导入成功"
else
    echo "❌ Gunicorn导入失败"
    exit 1
fi

# 查找gunicorn命令路径
GUNICORN_PATH=$(python -c "import gunicorn; import os; print(os.path.dirname(gunicorn.__file__) + '/../../../bin/gunicorn')" 2>/dev/null || echo "")
if [ -z "$GUNICORN_PATH" ] || [ ! -f "$GUNICORN_PATH" ]; then
    # 尝试其他可能的路径
    POSSIBLE_PATHS=(
        "/usr/local/bin/gunicorn"
        "/opt/conda/bin/gunicorn"
        "/root/.local/bin/gunicorn"
        "$(python -m site --user-base)/bin/gunicorn"
    )
    
    for path in "${POSSIBLE_PATHS[@]}"; do
        if [ -f "$path" ]; then
            GUNICORN_PATH="$path"
            break
        fi
    done
fi

if [ -n "$GUNICORN_PATH" ] && [ -f "$GUNICORN_PATH" ]; then
    echo "✅ 找到Gunicorn命令: $GUNICORN_PATH"
    # 确保gunicorn在PATH中
    export PATH="$(dirname $GUNICORN_PATH):$PATH"
else
    echo "⚠️  未找到gunicorn命令，将使用python -m gunicorn"
fi

# 测试gunicorn命令
echo "🧪 测试Gunicorn命令..."
if command -v gunicorn >/dev/null 2>&1; then
    echo "✅ gunicorn命令可用"
    gunicorn --version
elif python -m gunicorn --version >/dev/null 2>&1; then
    echo "✅ python -m gunicorn可用"
    python -m gunicorn --version
    # 创建gunicorn别名
    alias gunicorn="python -m gunicorn"
else
    echo "❌ Gunicorn命令不可用，回退到Flask服务器"
    echo "🚀 启动Flask开发服务器..."
    exec python app_server.py
fi

# 检查服务配置
echo "🔧 检查服务配置..."
if [ ! -f "app_server.py" ]; then
    echo "❌ app_server.py文件不存在"
    exit 1
fi

if [ ! -f "app_production.py" ]; then
    echo "❌ app_production.py文件不存在"
    exit 1
fi

# 启动生产服务器
echo "🚀 启动生产服务器..."
echo "使用app_production.py启动（自动选择最佳服务器）"
exec python app_production.py 