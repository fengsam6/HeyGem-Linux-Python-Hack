# Gunicorn启动说明

## 🚀 直接使用Gunicorn启动

```bash
# 基本启动
gunicorn --config gunicorn.conf.py app_server:app

# 指定GPU设备
CUDA_VISIBLE_DEVICES=0 gunicorn --config gunicorn.conf.py app_server:app

# 自定义线程数
GUNICORN_THREADS=16 gunicorn --config gunicorn.conf.py app_server:app

# 自定义超时时间（秒）
GUNICORN_TIMEOUT=1200 gunicorn --config gunicorn.conf.py app_server:app

# 设置内存限制（MB）
GUNICORN_MAX_MEMORY=16384 gunicorn --config gunicorn.conf.py app_server:app
```

## 📋 环境变量配置

| 环境变量 | 默认值 | 说明 |
|---------|-------|------|
| `CUDA_VISIBLE_DEVICES` | `0` | GPU设备号 |
| `GUNICORN_THREADS` | `8` | 线程数 |
| `GUNICORN_TIMEOUT` | `600` | 超时时间(秒) |
| `GUNICORN_MAX_MEMORY` | 无限制 | 内存限制(MB) |

## 🛠️ 推荐配置

```bash
# 生产环境启动
export CUDA_VISIBLE_DEVICES=0
export GUNICORN_THREADS=8
export GUNICORN_TIMEOUT=600
gunicorn --config gunicorn.conf.py app_server:app
```

## 📊 检查服务状态

```bash
# 检查GPU状态
curl http://localhost:8383/gpu/status

# 健康检查
curl http://localhost:8383/health
``` 