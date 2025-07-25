#!/bin/bash

# 生产环境启动脚本 - 使用Gunicorn
# 更好的并发性能和稳定性

# 检查Gunicorn是否安装
if ! command -v gunicorn &> /dev/null; then
    echo "Gunicorn未安装，正在安装..."
    pip install gunicorn
fi

# 读取配置
source config/config.ini 2>/dev/null || true

# 设置默认值
HOST=${server_ip:-"0.0.0.0"}
PORT=${server_port:-"8000"}
WORKERS=${gunicorn_workers:-4}
THREADS=${gunicorn_threads:-2}
TIMEOUT=${gunicorn_timeout:-300}

echo "启动TransDhServer服务..."
echo "Host: $HOST"
echo "Port: $PORT" 
echo "Workers: $WORKERS"
echo "Threads: $THREADS"
echo "Timeout: $TIMEOUT"

# 启动Gunicorn服务器
exec gunicorn \
    --bind $HOST:$PORT \
    --workers $WORKERS \
    --threads $THREADS \
    --timeout $TIMEOUT \
    --worker-class gthread \
    --worker-connections 1000 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --preload \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    app_server:app 