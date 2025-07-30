# 🚀 HeyGem AI - 快速开始指南

## 📋 解决的问题

✅ **已解决**: `RuntimeError: Cannot re-initialize CUDA in forked subprocess`

✅ **已解决**: Fork错误问题，现在可以安全使用GPU！

现在使用单进程GPU模式，既能使用GPU加速，又避免fork错误！

## ✅ 解决方案

**一行命令解决所有问题**：

```bash
python start_final_gpu_server.py
```

## 📊 这个脚本会自动：

- 🔧 **检查环境**：工作目录、文件、依赖
- 🚫 **单进程模式**：workers=1，完全避免fork操作
- 🛠️ **GPU模式**：安全启用GPU，单进程避免fork错误
- 🔄 **预加载应用**：preload_app=True，模型只初始化一次
- 📝 **实时监控**：显示启动和GPU状态信息

## 📱 其他启动方式

```bash
# 1. 脚本启动（推荐）
python start_final_gpu_server.py

# 2. 直接使用Gunicorn
gunicorn --config gunicorn.conf.py app_server:app

# 3. 自定义GPU设备
CUDA_VISIBLE_DEVICES=1 gunicorn --config gunicorn.conf.py app_server:app

# 4. Flask开发模式
python app_server.py
```

## 🎯 预期结果

**成功的话你会看到**：
```
🔧 Gunicorn配置：GPU模式，单进程安全
🔧 GPU模式启用，单进程安全
🔧 检查GPU环境...
✅ GPU可用: 1个设备, 当前设备: 0
✅ AI服务模块导入成功
✅ 环境配置完成
🚀 启动Gunicorn服务器...
=== 单进程GPU模式配置信息 ===
Worker [PID]: 单进程GPU模式启动
Worker [PID]: ✅ GPU可用，设备数量: 1
🎉 AI模型加载成功! GPU模式运行正常!
```

## 🔧 环境变量配置

```bash
# GPU设备选择
export CUDA_VISIBLE_DEVICES=0

# 线程数调整
export GUNICORN_THREADS=16

# 超时时间设置
export GUNICORN_TIMEOUT=1200

# 内存限制（可选）
export GUNICORN_MAX_MEMORY=16384
```

## 📚 更多文档

- **Gunicorn使用**: `GUNICORN_USAGE.md`
- **GPU状态检查**: `curl http://localhost:8383/gpu/status`

---

**单进程GPU模式！既能使用GPU加速，又避免fork错误** 🚀🎉 