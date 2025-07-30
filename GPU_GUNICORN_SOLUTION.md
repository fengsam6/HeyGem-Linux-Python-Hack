# HeyGem AI - GPU + Gunicorn 问题解决方案

## 🎯 问题描述

**现象**：使用Gunicorn启动服务时，GPU模型无法正常工作，但直接用Flask运行时GPU工作正常。

**根本原因**：CUDA上下文不能在进程间共享，Gunicorn的多进程架构导致GPU资源冲突。

## 🔧 核心解决方案

### 1. 关键配置修改

#### ❌ 问题配置
```python
# 错误的配置 - 会导致GPU不工作
preload_app = True   # 模型在主进程初始化，worker无法访问GPU
workers = 2          # 多进程导致GPU资源冲突
worker_class = 'sync'  # 同步模式，并发能力差
```

#### ✅ 正确配置
```python
# GPU优化配置 - 确保GPU正常工作
preload_app = False  # 关键：每个worker独立初始化模型
workers = 1          # 单进程避免GPU显存冲突
worker_class = 'gthread'  # 线程模式，支持并发
threads = 8          # 8线程处理并发请求
```

### 2. GPU环境变量设置

```bash
# 必须的GPU环境变量
export CUDA_VISIBLE_DEVICES=0
export NVIDIA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
```

### 3. Worker进程GPU初始化

在`post_fork`钩子中确保GPU在worker进程中正确初始化：

```python
def post_fork(server, worker):
    """GPU模型必须在这里初始化"""
    # 重新设置GPU环境变量
    os.environ['CUDA_VISIBLE_DEVICES'] = '0'
    
    # 检查GPU可用性
    import onnxruntime
    if 'CUDAExecutionProvider' in onnxruntime.get_available_providers():
        server.log.info(f"Worker {worker.pid}: GPU初始化成功")
    else:
        server.log.warning(f"Worker {worker.pid}: GPU不可用")
```

## 🚀 快速解决步骤

### 步骤1：运行诊断脚本
```bash
# 给脚本添加执行权限
chmod +x check_gpu_gunicorn.py start_gpu_server.sh

# 运行GPU环境诊断
python check_gpu_gunicorn.py
```

### 步骤2：选择合适的启动方式

#### 方式A：简化版GPU启动器（推荐）
```bash
# 解决模块导入问题的简化版启动器
python start_simple_gpu_server.py

# 自动模式（先试Gunicorn，失败则用Flask）
python start_simple_gpu_server.py auto

# 强制使用Flask模式
python start_simple_gpu_server.py flask
```

#### 方式B：CUDA多进程兼容启动器
```bash
# 解决CUDA多进程问题的专用启动器
python start_cuda_fixed_server.py

# 或使用Flask模式（如果Gunicorn有问题）
python start_cuda_fixed_server.py flask
```

#### 方式B：GPU优化启动脚本
```bash
# 默认生产模式启动
./start_gpu_server.sh

# 或指定启动模式
./start_gpu_server.sh --production    # 推荐
./start_gpu_server.sh --diagnose      # 先诊断再启动
./start_gpu_server.sh --help          # 查看所有选项
```

### 步骤3：验证GPU工作状态
```bash
# 监控GPU使用情况
nvidia-smi -l 1

# 检查服务日志
tail -f log/dh.log
```

## 📊 配置对比表

| 配置项 | GPU应用 | 普通应用 | 说明 |
|--------|---------|----------|------|
| `preload_app` | **False** | True | GPU应用必须False |
| `workers` | **1** | CPU核心数 | 避免GPU显存冲突 |
| `worker_class` | **gthread** | sync | 支持并发但避免进程冲突 |
| `threads` | **8** | 1 | 提高单进程并发能力 |
| `timeout` | **600s** | 30s | AI推理需要更长时间 |
| `max_worker_memory` | **8192MB** | 128MB | 大模型需要更多内存 |

## 🔍 故障排查指南

### 问题1：GPU仍然不工作
**检查项**：
- [ ] `preload_app = False` 是否正确设置
- [ ] 环境变量 `CUDA_VISIBLE_DEVICES` 是否设置
- [ ] 查看post_fork日志中的GPU检查信息
- [ ] 确认模型在worker进程中初始化，而非主进程

**解决方案**：
```bash
# 重新运行诊断
python check_gpu_gunicorn.py

# 检查配置
grep -n "preload_app\|workers\|CUDA" gunicorn.conf.py
```

### 问题2：显存不足 (OOM)
**现象**：
```
RuntimeError: CUDA out of memory
Worker {pid} aborted
```

**解决方案**：
```bash
# 确保单进程模式
export GUNICORN_WORKERS=1

# 优化PyTorch内存分配
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:256

# 监控显存使用
nvidia-smi
```

### 问题3：模块导入错误
**现象**：
```
ModuleNotFoundError: No module named 'trans_dh_service'
ModuleNotFoundError: No module named 'ai_service'
Worker exited with code 1
```

**解决方案**：
```bash
# 使用简化版启动器（解决模块导入问题）
python start_simple_gpu_server.py

# 或手动设置工作目录和Python路径
export PYTHONPATH=/code:$PYTHONPATH
cd /code
python app_production.py
```

### 问题4：CUDA多进程错误
**现象**：
```
RuntimeError: Cannot re-initialize CUDA in forked subprocess. To use CUDA with multiprocessing, you must use the 'spawn' start method
```

**解决方案**：
```bash
# 使用专门的CUDA兼容启动器
python start_cuda_fixed_server.py

# 或设置环境变量
export CUDA_LAUNCH_BLOCKING=1
export TORCH_USE_CUDA_DSA=1
python app_production.py
```

### 问题4：启动超时
**现象**：服务启动时间过长或超时

**解决方案**：
```bash
# 增加启动超时时间
export GUNICORN_TIMEOUT=1200  # 20分钟

# 检查模型文件是否存在
ls -la face_detect_utils/resources/
```

### 问题4：并发能力不足
**现象**：单进程模式下请求处理慢

**解决方案**：
```bash
# 增加线程数
export GUNICORN_THREADS=16

# 使用异步模式（需要gevent）
export GUNICORN_WORKER_CLASS=gevent
pip install "gevent>=1.4.0"
```

## 📈 性能优化建议

### 1. 根据GPU显存调整配置

#### 12GB GPU (RTX 3060, RTX 4070等)
```bash
export GUNICORN_WORKERS=1
export GUNICORN_THREADS=8
export GUNICORN_MAX_MEMORY=6144  # 6GB
```

#### 24GB GPU (RTX 3090, RTX 4090等)
```bash
export GUNICORN_WORKERS=1
export GUNICORN_THREADS=16
export GUNICORN_MAX_MEMORY=12288  # 12GB
```

#### 48GB+ GPU (A100, H100等)
```bash
export GUNICORN_WORKERS=1
export GUNICORN_THREADS=32
export GUNICORN_MAX_MEMORY=20480  # 20GB
```

### 2. 监控和告警设置

```bash
# GPU使用率监控
nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv -l 1

# 内存使用监控
watch -n 1 'ps aux | grep gunicorn'

# 服务健康检查
curl http://localhost:8383/health
```

## 🔗 相关文件

- `gunicorn.conf.py` - 主配置文件（已优化）
- `app_server.py` - 应用服务器（已修复CUDA多进程问题）
- `start_simple_gpu_server.py` - 简化版GPU启动器（推荐，解决模块导入问题）
- `start_cuda_fixed_server.py` - CUDA多进程兼容启动器
- `check_gpu_gunicorn.py` - GPU诊断脚本
- `test_gpu_fix.py` - GPU修复验证测试
- `start_gpu_server.sh` - GPU启动脚本
- `AI_MODEL_DEPLOYMENT.md` - 详细部署指南

## 📞 技术支持

如果问题仍然存在，请提供以下信息：

1. **GPU信息**：`nvidia-smi` 输出
2. **诊断结果**：`python check_gpu_gunicorn.py` 输出
3. **错误日志**：Gunicorn和应用的完整错误日志
4. **配置信息**：当前的环境变量和配置文件

---

**重要提醒**：GPU应用在Gunicorn中最关键的是 `preload_app = False`，这是解决GPU不工作问题的核心。 