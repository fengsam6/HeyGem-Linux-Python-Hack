#!/bin/bash

# uWSGI生产环境启动脚本
# 企业级WSGI服务器，性能最高

# 检查uWSGI是否安装
if ! command -v uwsgi &> /dev/null; then
    echo "uWSGI未安装，正在安装..."
    pip install uwsgi
fi

# 读取配置
source config/config.ini 2>/dev/null || true

# 设置默认值
HOST=${server_ip:-"0.0.0.0"}
PORT=${server_port:-"8000"}
PROCESSES=${uwsgi_processes:-4}
THREADS=${uwsgi_threads:-2}
TIMEOUT=${uwsgi_timeout:-300}

echo "启动TransDhServer服务（uWSGI）..."
echo "Host: $HOST"
echo "Port: $PORT" 
echo "Processes: $PROCESSES"
echo "Threads: $THREADS"
echo "Timeout: $TIMEOUT"

# 启动uWSGI服务器
exec uwsgi \
    --http $HOST:$PORT \
    --module app_server:app \
    --processes $PROCESSES \
    --threads $THREADS \
    --harakiri $TIMEOUT \
    --max-requests 1000 \
    --max-requests-delta 50 \
    --master \
    --enable-threads \
    --single-interpreter \
    --need-app \
    --disable-logging \
    --log-4xx \
    --log-5xx \
    --vacuum \
    --die-on-term 