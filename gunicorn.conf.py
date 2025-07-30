# Gunicorn配置文件 - HeyGem AI服务
import os

# GPU配置
os.environ['CUDA_VISIBLE_DEVICES'] = os.environ.get('CUDA_VISIBLE_DEVICES', '0')

# 服务器绑定
try:
    from service.config import server_ip, server_port
    bind = f"{server_ip}:{server_port}"
except ImportError:
    bind = "0.0.0.0:8383"

# 核心配置
workers = 1                                    # 单进程模式
worker_class = 'sync'                         # 同步工作模式
threads = int(os.environ.get('GUNICORN_THREADS', 8))
timeout = int(os.environ.get('GUNICORN_TIMEOUT', 600))
preload_app = True                            # 预加载应用

# 内存配置（不写死，支持环境变量）
if 'GUNICORN_MAX_MEMORY' in os.environ:
    max_worker_memory = int(os.environ['GUNICORN_MAX_MEMORY'])

# 日志配置
loglevel = 'info'
access_logfile = '-'
error_logfile = '-'

# 进程名称
proc_name = 'heygem-ai-server'

# 钩子函数
def when_ready(server):
    server.log.info(f"HeyGem AI Server ready on {bind}")
    server.log.info(f"GPU: {os.environ.get('CUDA_VISIBLE_DEVICES', 'not set')}")

def post_fork(server, worker):
    server.log.info(f"Worker {worker.pid} started")
