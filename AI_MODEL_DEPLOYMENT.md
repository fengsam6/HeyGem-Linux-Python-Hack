# HeyGem AI大模型服务部署指南

## 🎯 概述

本文档专门针对HeyGem数字人视频生成服务的大模型部署进行说明。该服务包含多个AI模型（面部检测、语音处理、视频生成等），需要特殊的部署配置以优化资源使用。

## 🔧 核心配置原则

### 1. 单进程 vs 多进程选择

#### ✅ **推荐：单进程部署**
```bash
# 环境变量配置
export GUNICORN_WORKERS=1
export GUNICORN_WORKER_CLASS=gevent
export GUNICORN_THREADS=8
```

**原因：**
- **避免模型重复加载**：每个worker进程都会加载一套完整的AI模型
- **节省GPU显存**：多进程会导致显存被重复占用
- **减少内存消耗**：大模型通常需要几GB到几十GB内存
- **降低启动时间**：避免多次初始化模型（每次15秒+）

#### ❌ **不推荐：多进程部署**
```bash
# 避免这种配置
export GUNICORN_WORKERS=4  # 会导致模型加载4次
```

**问题：**
- 4个进程 × 8GB模型 = 32GB内存占用
- GPU显存不足，可能导致OOM错误
- 启动时间延长（4 × 15秒 = 60秒+）

### 2. 工作进程类型选择

#### ✅ **推荐：异步进程（gevent）**
```python
worker_class = 'gevent'
worker_connections = 500
```

**优势：**
- **高并发能力**：单进程处理多个并发请求
- **资源效率**：适合I/O密集型的AI推理
- **响应性好**：避免阻塞其他请求

#### 🔄 **备选：线程进程（gthread）**
```python
worker_class = 'gthread'
threads = 8
```

**适用场景：**
- 某些AI模型不支持异步调用
- 需要更稳定的线程隔离

#### ❌ **不推荐：同步进程（sync）**
```python
worker_class = 'sync'  # 避免使用
```

**问题：**
- 并发能力差，一次只能处理一个请求
- 用户体验差，响应时间长

## 📊 配置参数详解

### 内存配置
```python
# 工作进程最大内存（根据模型大小调整）
max_worker_memory = 8192  # 8GB，可根据实际模型大小调整

# 可选值参考：
# - 小型模型：2048MB (2GB)
# - 中型模型：4096MB (4GB)  
# - 大型模型：8192MB (8GB)
# - 超大型模型：16384MB (16GB)
```

### 超时配置
```python
# AI推理可能需要较长时间
timeout = 600  # 10分钟，视频生成可能需要更长时间
keepalive = 300  # 5分钟，保持连接以避免频繁建连

# 调整建议：
# - 图像处理：300-600秒
# - 视频生成：600-1200秒
# - 大型语言模型：120-300秒
```

### 请求处理配置
```python
# 降低重启频率，避免频繁重新加载模型
max_requests = 50  # 处理50个请求后重启worker

# 连接数配置
worker_connections = 500  # 异步模式下的最大并发连接
```

## 🚀 部署方式

### 方式一：使用环境变量（推荐）
```bash
# 设置环境变量
export GUNICORN_WORKERS=1
export GUNICORN_WORKER_CLASS=gevent
export GUNICORN_THREADS=8
export GUNICORN_CONNECTIONS=500
export GUNICORN_TIMEOUT=600
export GUNICORN_MAX_MEMORY=8192

# 启动服务
python app_production.py
```

### 方式二：直接使用Gunicorn
```bash
gunicorn --config gunicorn.conf.py app_server:app
```

### 方式三：Docker部署（最简单）
```bash
# 环境变量会自动应用到容器中
docker-compose -f deploy/docker-compose-linux.yml up -d
```

## 📈 性能调优

### 1. 根据硬件配置调整

#### GPU服务器配置
```bash
# 高端GPU服务器（如RTX 4090, A100）
export GUNICORN_WORKERS=1
export GUNICORN_THREADS=16
export GUNICORN_CONNECTIONS=1000
export GUNICORN_MAX_MEMORY=16384
```

#### 中端GPU配置
```bash
# 中端GPU（如RTX 3080, RTX 4070）
export GUNICORN_WORKERS=1
export GUNICORN_THREADS=8
export GUNICORN_CONNECTIONS=500
export GUNICORN_MAX_MEMORY=8192
```

#### CPU-only配置
```bash
# 仅使用CPU（不推荐用于生产）
export GUNICORN_WORKERS=2
export GUNICORN_WORKER_CLASS=gthread
export GUNICORN_THREADS=4
export GUNICORN_MAX_MEMORY=4096
```

### 2. 监控指标

#### 关键监控项
- **GPU显存使用率**：应保持在80%以下
- **内存使用率**：避免超过max_worker_memory设置
- **请求响应时间**：正常应在timeout设置范围内
- **并发连接数**：不应超过worker_connections设置

#### 性能测试命令
```bash
# 使用ab进行压力测试
ab -n 100 -c 10 http://localhost:8383/api/test

# 监控GPU使用情况
nvidia-smi -l 1

# 监控内存使用
htop
```

## 🔍 故障排查

### 常见问题和解决方案

#### 1. 内存不足（OOM）
**症状：**
```
Worker {pid} aborted - 可能是内存不足或模型加载失败
```

**解决方案：**
```bash
# 减少进程数或增加内存限制
export GUNICORN_WORKERS=1
export GUNICORN_MAX_MEMORY=16384

# 或者使用更小的模型
```

#### 2. GPU显存不足
**症状：**
```
CUDA out of memory
RuntimeError: CUDA error: out of memory
```

**解决方案：**
```bash
# 确保使用单进程
export GUNICORN_WORKERS=1

# 在代码中添加显存清理
import torch
torch.cuda.empty_cache()
```

#### 3. 启动时间过长
**症状：**
- 服务启动超过2分钟
- 模型加载timeout

**解决方案：**
```bash
# 增加启动超时时间
export GUNICORN_TIMEOUT=1200  # 20分钟

# 确保预加载应用
preload_app = True
```

#### 4. 请求响应慢
**症状：**
- 单个请求处理时间过长
- 并发能力差

**解决方案：**
```bash
# 使用异步模式
export GUNICORN_WORKER_CLASS=gevent
export GUNICORN_CONNECTIONS=1000

# 增加线程数
export GUNICORN_THREADS=16
```

## 📋 配置检查清单

### 部署前检查
- [ ] GPU驱动和CUDA版本兼容
- [ ] 足够的GPU显存（建议至少12GB）
- [ ] 足够的系统内存（建议至少16GB）
- [ ] Docker容器共享内存配置（shm_size: 8g）

### 配置检查
- [ ] 工作进程数设置为1（大模型服务）
- [ ] 使用异步工作进程类型（gevent）
- [ ] 内存限制适配模型大小
- [ ] 超时时间适配推理耗时
- [ ] 启用预加载应用（preload_app = True）

### 启动后验证
- [ ] 服务正常启动，无OOM错误
- [ ] GPU显存使用合理（<80%）
- [ ] API响应正常
- [ ] 并发处理能力符合预期

## 🎛️ 高级配置

### 自动扩缩容（实验性）
```python
# 基于负载自动调整连接数
import psutil

def dynamic_worker_connections():
    cpu_usage = psutil.cpu_percent(interval=1)
    if cpu_usage > 80:
        return 300  # 降低并发
    elif cpu_usage < 30:
        return 800  # 提高并发
    return 500  # 默认值
```

### 健康检查配置
```python
# 添加健康检查端点
def health_check():
    try:
        # 检查模型是否正常加载
        # 检查GPU显存是否充足
        # 检查内存使用情况
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

## 📞 技术支持

如遇到部署问题，请提供以下信息：
1. 硬件配置（GPU型号、内存大小）
2. 错误日志
3. 当前配置参数
4. 性能监控数据

---

**注意：** 本配置针对HeyGem数字人视频生成服务优化，其他AI服务可能需要不同的配置策略。 