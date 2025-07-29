#!/bin/bash

# HeyGem AI - Gevent依赖修复脚本
# 解决 "gevent worker requires gevent 1.4 or higher" 错误

echo "=========================================="
echo "HeyGem AI - Gevent依赖修复脚本"
echo "=========================================="

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "❌ Python未安装，请先安装Python"
    exit 1
fi

echo "✅ Python环境检查通过"

# 方法1：尝试安装gevent
echo ""
echo "🔧 方法1：安装gevent依赖"
echo "正在安装gevent>=1.4.0..."

if pip install "gevent>=1.4.0"; then
    echo "✅ gevent安装成功"
    
    # 验证gevent版本
    GEVENT_VERSION=$(python -c "import gevent; print(gevent.__version__)" 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "✅ gevent版本: $GEVENT_VERSION"
        echo ""
        echo "🚀 现在可以使用gevent模式启动服务："
        echo "   python app_production.py"
        echo "   或"
        echo "   gunicorn --config gunicorn.conf.py app_server:app"
        exit 0
    else
        echo "⚠️  gevent安装可能有问题，将使用备选方案"
    fi
else
    echo "⚠️  gevent安装失败，将使用备选方案"
fi

# 方法2：使用gthread模式作为回退
echo ""
echo "🔧 方法2：使用gthread模式（备选方案）"
echo "设置环境变量使用gthread worker..."

export GUNICORN_WORKER_CLASS=gthread
echo "✅ 已设置 GUNICORN_WORKER_CLASS=gthread"

echo ""
echo "🚀 现在可以使用以下命令启动服务："
echo ""
echo "# 方式1：使用环境变量"
echo "export GUNICORN_WORKER_CLASS=gthread"
echo "python app_production.py"
echo ""
echo "# 方式2：直接指定配置"
echo "gunicorn --worker-class gthread --workers 1 --threads 8 --bind 0.0.0.0:8383 app_server:app"
echo ""

# 方法3：Docker重新构建
echo "🔧 方法3：如果使用Docker，请重新构建镜像"
echo "docker-compose down"
echo "docker-compose build --no-cache"
echo "docker-compose up -d"
echo ""

echo "=========================================="
echo "修复完成！选择任一方法启动服务即可。"
echo "==========================================" 