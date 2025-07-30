# 🚀 直接使用Gunicorn命令启动 - 最佳方案

## ✅ **推荐启动命令**

### 基本启动
```bash
python -m gunicorn --config gunicorn.conf.py app_server:app
```

### 指定GPU启动
```bash
CUDA_VISIBLE_DEVICES=0 python -m gunicorn --config gunicorn.conf.py app_server:app
```

### 后台运行
```bash
nohup python -m gunicorn --config gunicorn.conf.py app_server:app > server.log 2>&1 &
```

## 🎛️ **环境变量配置**

可以通过环境变量调整配置：

```bash
export CUDA_VISIBLE_DEVICES=0           # GPU设备
export GUNICORN_THREADS=8               # 线程数
export GUNICORN_TIMEOUT=600             # 超时时间
export GUNICORN_MAX_MEMORY=8192         # 最大内存(MB)

python -m gunicorn --config gunicorn.conf.py app_server:app
```

## 🔧 **一键启动脚本**

创建 `start_gunicorn.sh`：
```bash
#!/bin/bash
export CUDA_VISIBLE_DEVICES=0
export GUNICORN_THREADS=8
export GUNICORN_TIMEOUT=600

echo "🚀 启动HeyGem AI服务..."
python -m gunicorn --config gunicorn.conf.py app_server:app
```

然后执行：
```bash
chmod +x start_gunicorn.sh
./start_gunicorn.sh
```

## 📋 **当前配置说明**

- **单进程模式** (`workers = 1`) - 避免GPU共享问题
- **同步工作** (`worker_class = 'sync'`) - 最稳定
- **预加载应用** (`preload_app = True`) - 提高性能
- **GPU自动配置** - 自动设置CUDA环境

## 🎯 **为什么这是最佳方案**

1. ✅ **最简单** - 直接命令，无需Python包装脚本
2. ✅ **最稳定** - 避免进程隔离和复杂性
3. ✅ **最灵活** - 支持环境变量配置
4. ✅ **最高效** - 无额外Python层开销
5. ✅ **易调试** - 直接看到gunicorn日志

## 🚨 **故障排除**

如果启动失败，检查：
1. 是否在正确目录：`cd /code`
2. GPU是否可用：`nvidia-smi`
3. 依赖是否安装：`pip list | grep gunicorn`
4. 端口是否被占用：`netstat -tlnp | grep 8383`

**总结：直接用gunicorn命令是最好的选择！** 🎉 