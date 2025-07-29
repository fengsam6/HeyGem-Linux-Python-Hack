#!/bin/bash

# HeyGem AI 生产环境启动脚本
# 支持多种启动方式和自动依赖检查

set -e  # 遇到错误立即退出

echo "=========================================="
echo "HeyGem AI 生产环境启动脚本"
echo "=========================================="

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "❌ Python未安装，请先安装Python"
    exit 1
fi

echo "✅ Python环境检查通过"

# 检查并安装Gunicorn
if ! python -c "import gunicorn" &> /dev/null; then
    echo "⚠️  Gunicorn未安装，正在安装..."
    pip install gunicorn>=21.2.0
    if [ $? -eq 0 ]; then
        echo "✅ Gunicorn安装成功"
    else
        echo "❌ Gunicorn安装失败，将使用Flask开发服务器"
        python app_server.py
        exit 1
    fi
else
    echo "✅ Gunicorn已安装"
fi

# 检查配置文件
if [ ! -f "gunicorn.conf.py" ]; then
    echo "⚠️  gunicorn.conf.py配置文件不存在"
    echo "使用默认配置启动..."
    GUNICORN_CMD="gunicorn --bind 0.0.0.0:8383 --workers 4 --threads 2 --timeout 300 --worker-class gthread app_server:app"
else
    echo "✅ 使用gunicorn.conf.py配置文件"
    GUNICORN_CMD="gunicorn --config gunicorn.conf.py app_server:app"
fi

# 检查应用文件
if [ ! -f "app_server.py" ]; then
    echo "❌ app_server.py文件不存在"
    exit 1
fi

echo "✅ 应用文件检查通过"

# 启动选项
if [ "$1" == "production" ]; then
    echo "🚀 使用app_production.py启动（推荐）"
    python app_production.py
elif [ "$1" == "gunicorn" ]; then
    echo "🚀 直接使用Gunicorn启动"
    exec $GUNICORN_CMD
elif [ "$1" == "flask" ]; then
    echo "🚀 使用Flask开发服务器启动"
    python app_server.py
else
    echo ""
    echo "启动选项："
    echo "  production  - 使用app_production.py启动（推荐，自动回退）"
    echo "  gunicorn    - 直接使用Gunicorn启动"
    echo "  flask       - 使用Flask开发服务器启动"
    echo ""
    echo "默认使用production模式启动..."
    python app_production.py
fi 