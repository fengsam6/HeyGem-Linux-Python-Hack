# Gunicorn配置文件
# 适用于数字人视频生成服务的生产环境配置
# 针对大模型AI服务进行优化

import multiprocessing
import os

# 从配置文件中读取设置
try:
    from service.config import server_ip, server_port
    bind_host = server_ip
    bind_port = server_port
except ImportError:
    # 如果无法导入配置，使用默认值
    bind_host = "0.0.0.0"
    bind_port = 8383

# 服务器地址绑定
bind = f"{bind_host}:{bind_port}"

# ===============================
# 大模型服务进程配置
# ===============================

# 工作进程数量 - 对于大模型服务建议使用单进程
# 原因：避免每个进程都加载一份模型，节省内存和GPU显存
workers = int(os.environ.get('GUNICORN_WORKERS', 1))

# 每个工作进程的线程数 - 增加线程数以提高并发处理能力
threads = int(os.environ.get('GUNICORN_THREADS', 8))

# 工作进程类型 - 使用异步工作进程提高并发能力
# 'sync' - 同步工作进程（默认，适合CPU密集型）
# 'gthread' - 线程工作进程（推荐用于I/O密集型应用）
# 'gevent' - 异步工作进程（推荐用于大模型AI服务）
# 'eventlet' - 异步工作进程（备选）

# 自动检测和回退机制
def get_worker_class():
    """智能选择worker类型，支持自动回退"""
    preferred_class = os.environ.get('GUNICORN_WORKER_CLASS', 'gevent')
    
    # 尝试gevent
    if preferred_class == 'gevent':
        try:
            import gevent
            # 检查gevent版本
            if hasattr(gevent, '__version__'):
                from packaging import version
                if version.parse(gevent.__version__) >= version.parse('1.4.0'):
                    return 'gevent'
            print("⚠️  gevent版本不符合要求或不可用，回退到gthread")
        except ImportError:
            print("⚠️  gevent未安装，回退到gthread")
        return 'gthread'
    
    return preferred_class

worker_class = get_worker_class()

# 工作进程连接数（仅用于gthread和gevent）
# 对于AI服务，适当提高连接数以支持更多并发请求
worker_connections = int(os.environ.get('GUNICORN_CONNECTIONS', 500))

# ===============================
# 请求处理配置
# ===============================

# 最大请求数（工作进程处理max_requests个请求后重启）
# 对于大模型服务，适当降低重启频率以避免频繁重新加载模型
max_requests = int(os.environ.get('GUNICORN_MAX_REQUESTS', 50))
max_requests_jitter = int(max_requests * 0.1)  # 10%随机因子

# 超时设置 - AI推理可能需要较长时间
timeout = int(os.environ.get('GUNICORN_TIMEOUT', 600))  # 请求超时时间（秒）
keepalive = int(os.environ.get('GUNICORN_KEEPALIVE', 300))  # Keep-Alive连接超时时间

# ===============================
# 内存和进程管理
# ===============================

# 预加载应用配置 - 对于GPU应用需要特殊处理
# GPU/CUDA应用不能使用preload_app=True，因为CUDA上下文不能跨进程共享
# 每个worker进程必须独立初始化GPU模型
preload_app = False  # 重要：GPU应用必须设置为False

# 工作进程最大内存 - 根据模型大小调整
# 大模型服务通常需要几GB到几十GB内存
max_worker_memory = int(os.environ.get('GUNICORN_MAX_MEMORY', 8192))  # 8GB

# ===============================
# 日志配置
# ===============================

loglevel = os.environ.get('GUNICORN_LOG_LEVEL', 'info')
access_logfile = '-'  # 访问日志输出到stdout
error_logfile = '-'   # 错误日志输出到stderr
access_logformat = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# ===============================
# 服务配置
# ===============================

# 进程名称
proc_name = 'heygem-ai-server'

# 临时目录
tmp_upload_dir = '/tmp'

# 安全配置
limit_request_line = 8192  # 增加请求行长度限制
limit_request_fields = 200  # 增加请求字段数量限制
limit_request_field_size = 16384  # 增加请求字段大小限制

# 用户权限（如果需要）
# user = 'www-data'
# group = 'www-data'

# SSL配置（如果需要HTTPS）
# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile'

# ===============================
# GPU/CUDA配置
# ===============================

# GPU相关环境变量
os.environ.setdefault('CUDA_VISIBLE_DEVICES', '0')  # 默认使用第一个GPU
os.environ.setdefault('NVIDIA_VISIBLE_DEVICES', '0')
os.environ.setdefault('PYTORCH_CUDA_ALLOC_CONF', 'max_split_size_mb:512')

# ===============================
# 性能调优
# ===============================

# 使用内存作为临时目录（如果可用）
worker_tmp_dir = '/dev/shm'

# 启用SO_REUSEPORT（如果支持）
reuse_port = True

# 启用TCP_NODELAY
tcp_nodelay = True

# ===============================
# 钩子函数
# ===============================

def on_starting(server):
    """服务器启动时调用"""
    server.log.info("HeyGem AI Server is starting...")
    server.log.info(f"配置信息:")
    server.log.info(f"  - Workers: {workers}")
    server.log.info(f"  - Worker Class: {worker_class}")
    if worker_class == 'gthread':
        server.log.info("  - 注意：使用gthread模式，如需更高并发请安装gevent>=1.4.0")
    elif worker_class == 'gevent':
        server.log.info("  - 注意：使用gevent异步模式，支持高并发")
    server.log.info(f"  - Threads per Worker: {threads}")
    server.log.info(f"  - Worker Connections: {worker_connections}")
    server.log.info(f"  - Max Worker Memory: {max_worker_memory}MB")
    server.log.info(f"  - Timeout: {timeout}s")

def on_reload(server):
    """重新加载配置时调用"""
    server.log.info("HeyGem AI Server configuration reloaded...")

def when_ready(server):
    """服务器准备就绪时调用"""
    server.log.info(f"HeyGem AI Server is ready. Listening on {bind}")
    server.log.info("=== GPU大模型服务配置信息 ===")
    server.log.info(f"预加载应用: {preload_app} (GPU应用必须为False)")
    server.log.info(f"GPU设备: CUDA_VISIBLE_DEVICES={os.environ.get('CUDA_VISIBLE_DEVICES', '未设置')}")
    server.log.info("注意: GPU模型将在每个worker进程中独立初始化")
    server.log.info("注意: 请确保有足够的GPU显存支持worker进程数量")

def on_exit(server):
    """服务器退出时调用"""
    server.log.info("HeyGem AI Server is shutting down...")

# 工作进程钩子
def worker_int(worker):
    """工作进程收到SIGINT信号时调用"""
    worker.log.info(f"Worker {worker.pid} received SIGINT")

def pre_fork(server, worker):
    """工作进程创建前调用"""
    server.log.info(f"Pre-fork worker {worker.pid}")

def post_fork(server, worker):
    """工作进程创建后调用 - 关键：GPU模型必须在这里初始化"""
    server.log.info(f"Post-fork worker {worker.pid} - 开始初始化GPU和AI模型")
    
    # 确保GPU环境变量在worker进程中正确设置
    os.environ['CUDA_VISIBLE_DEVICES'] = os.environ.get('CUDA_VISIBLE_DEVICES', '0')
    os.environ['NVIDIA_VISIBLE_DEVICES'] = os.environ.get('NVIDIA_VISIBLE_DEVICES', '0')
    
    # GPU可用性检查
    try:
        # 检查ONNX Runtime GPU
        import onnxruntime
        providers = onnxruntime.get_available_providers()
        if 'CUDAExecutionProvider' in providers:
            server.log.info(f"Worker {worker.pid}: ONNX Runtime CUDA可用")
        else:
            server.log.warning(f"Worker {worker.pid}: ONNX Runtime CUDA不可用，将使用CPU")
        
        # 检查PyTorch CUDA（如果使用）
        try:
            import torch
            if torch.cuda.is_available():
                gpu_count = torch.cuda.device_count()
                current_device = torch.cuda.current_device()
                gpu_name = torch.cuda.get_device_name(current_device)
                server.log.info(f"Worker {worker.pid}: PyTorch CUDA可用，使用GPU[{current_device}]: {gpu_name}")
                server.log.info(f"Worker {worker.pid}: 总共有 {gpu_count} 个GPU可用")
            else:
                server.log.warning(f"Worker {worker.pid}: PyTorch CUDA不可用")
        except ImportError:
            server.log.info(f"Worker {worker.pid}: PyTorch未安装")
    except Exception as e:
        server.log.error(f"Worker {worker.pid}: GPU检查失败: {e}")
    
    # 关键：在worker进程中初始化AI模型
    try:
        server.log.info(f"Worker {worker.pid}: 开始加载AI模型...")
        
        # 导入并调用模型初始化函数
        from app_server import ensure_models_initialized
        ensure_models_initialized()
        
        server.log.info(f"Worker {worker.pid}: AI模型加载完成")
    except Exception as e:
        server.log.error(f"Worker {worker.pid}: AI模型加载失败: {e}")
        import traceback
        server.log.error(traceback.format_exc())
    
    server.log.info(f"Worker {worker.pid}: Worker进程初始化完成")

def worker_abort(worker):
    """工作进程异常终止时调用"""
    worker.log.error(f"Worker {worker.pid} aborted - 可能是内存不足或模型加载失败")

# ===============================
# 环境变量配置说明
# ===============================
"""
可通过以下环境变量覆盖默认配置：

=== Gunicorn 基础配置 ===
GUNICORN_WORKERS=1              # 工作进程数（GPU应用强烈建议1）
GUNICORN_THREADS=8              # 每进程线程数
GUNICORN_WORKER_CLASS=gthread   # 工作进程类型（GPU建议gthread，如有gevent则gevent）
GUNICORN_CONNECTIONS=500        # 最大连接数
GUNICORN_MAX_REQUESTS=50        # 最大请求数后重启
GUNICORN_TIMEOUT=600            # 请求超时时间（秒）
GUNICORN_KEEPALIVE=300          # Keep-Alive超时时间
GUNICORN_MAX_MEMORY=8192        # 最大内存（MB）
GUNICORN_LOG_LEVEL=info         # 日志级别

=== GPU/CUDA 专用配置 ===
CUDA_VISIBLE_DEVICES=0          # 指定使用的GPU设备
NVIDIA_VISIBLE_DEVICES=0        # NVIDIA容器运行时GPU设备
PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512  # PyTorch CUDA内存配置

=== GPU应用最佳实践 ===
1. 必须设置: preload_app = False (已在配置中设置)
2. 推荐设置: workers = 1 (避免GPU显存重复占用)
3. 模型初始化: 必须在worker进程的post_fork钩子中进行
4. 显存管理: 每个worker独立管理GPU资源

使用示例：
# GPU单进程模式（推荐）
export GUNICORN_WORKERS=1 CUDA_VISIBLE_DEVICES=0
python app_production.py

# 检查GPU环境
python check_gpu_gunicorn.py

# 启动服务
gunicorn --config gunicorn.conf.py app_server:app
"""
