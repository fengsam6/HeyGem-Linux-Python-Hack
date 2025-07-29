#!/bin/bash

# HeyGem AI GPU服务启动脚本
# 专门针对GPU大模型服务优化

set -e  # 遇到错误立即退出

echo "=========================================="
echo "HeyGem AI GPU服务启动脚本"
echo "=========================================="

# 检查GPU环境
echo "🔍 检查GPU环境..."

if ! command -v nvidia-smi &> /dev/null; then
    echo "⚠️  nvidia-smi未找到，确保在GPU环境中运行"
else
    echo "✅ GPU环境检测："
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader,nounits | while IFS=',' read -r name memory_total memory_free; do
        echo "   GPU: $name"
        echo "   显存: ${memory_free}MB 可用 / ${memory_total}MB 总计"
    done
fi

# 设置GPU环境变量
echo ""
echo "🔧 配置GPU环境变量..."

export CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-0}
export NVIDIA_VISIBLE_DEVICES=${NVIDIA_VISIBLE_DEVICES:-0}
export PYTORCH_CUDA_ALLOC_CONF=${PYTORCH_CUDA_ALLOC_CONF:-max_split_size_mb:512}

echo "✅ CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"
echo "✅ NVIDIA_VISIBLE_DEVICES=$NVIDIA_VISIBLE_DEVICES"
echo "✅ PYTORCH_CUDA_ALLOC_CONF=$PYTORCH_CUDA_ALLOC_CONF"

# 设置Gunicorn配置 - GPU优化
echo ""
echo "🔧 配置Gunicorn参数（GPU优化）..."

export GUNICORN_WORKERS=1              # GPU应用必须单进程
export GUNICORN_WORKER_CLASS=gthread   # 稳定的线程模式
export GUNICORN_THREADS=8              # 8个线程处理并发
export GUNICORN_TIMEOUT=600            # 10分钟超时（AI推理需要时间）
export GUNICORN_MAX_MEMORY=8192        # 8GB内存限制
export GUNICORN_MAX_REQUESTS=50        # 50个请求后重启（避免内存泄漏）

echo "✅ Workers: $GUNICORN_WORKERS (单进程模式)"
echo "✅ Worker Class: $GUNICORN_WORKER_CLASS"
echo "✅ Threads: $GUNICORN_THREADS"
echo "✅ Timeout: $GUNICORN_TIMEOUT seconds"
echo "✅ Max Memory: $GUNICORN_MAX_MEMORY MB"

# 检查依赖
echo ""
echo "🔍 检查关键依赖..."

python -c "
import sys
print('✅ Python版本:', sys.version.split()[0])

try:
    import onnxruntime
    providers = onnxruntime.get_available_providers()
    if 'CUDAExecutionProvider' in providers:
        print('✅ ONNX Runtime GPU: 可用')
    else:
        print('⚠️  ONNX Runtime GPU: 不可用')
except ImportError:
    print('❌ ONNX Runtime: 未安装')

try:
    import torch
    if torch.cuda.is_available():
        print(f'✅ PyTorch CUDA: 可用 ({torch.cuda.get_device_name(0)})')
    else:
        print('⚠️  PyTorch CUDA: 不可用')
except ImportError:
    print('⚠️  PyTorch: 未安装')

try:
    import gunicorn
    print('✅ Gunicorn: 可用')
except ImportError:
    print('❌ Gunicorn: 未安装')
"

echo ""

# 可选的详细诊断
if [ "$1" == "--diagnose" ] || [ "$1" == "-d" ]; then
    echo "🔬 运行详细GPU诊断..."
    if [ -f "check_gpu_gunicorn.py" ]; then
        python check_gpu_gunicorn.py
    else
        echo "⚠️  GPU诊断脚本不存在，跳过详细检查"
    fi
    echo ""
fi

# 检查配置文件
if [ ! -f "gunicorn.conf.py" ]; then
    echo "❌ gunicorn.conf.py配置文件不存在"
    exit 1
fi

if [ ! -f "app_production.py" ]; then
    echo "❌ app_production.py启动文件不存在"
    exit 1
fi

echo "✅ 配置文件检查通过"

# 启动服务
echo ""
echo "🚀 启动HeyGem AI GPU服务..."
echo "配置摘要:"
echo "  - 单GPU进程模式 (避免显存冲突)"
echo "  - 预加载禁用 (GPU模型在worker中初始化)"
echo "  - 8线程并发处理"
echo "  - 10分钟超时 (适配AI推理)"
echo ""

# 启动方式选择
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo "📋 HeyGem AI GPU服务启动选项:"
    echo ""
    echo "启动模式:"
    echo "  --production, -p    生产模式启动 (推荐，使用app_production.py)"
    echo "  --gunicorn, -g      直接Gunicorn启动"
    echo "  --flask, -f         Flask开发模式 (仅调试用)"
    echo "  (无参数)            默认生产模式"
    echo ""
    echo "诊断选项:"
    echo "  --diagnose, -d      运行详细GPU环境诊断"
    echo "  --help, -h          显示此帮助信息"
    echo ""
    echo "环境变量 (可选):"
    echo "  CUDA_VISIBLE_DEVICES=0          # 指定GPU设备"
    echo "  GUNICORN_WORKERS=1               # worker进程数"
    echo "  GUNICORN_THREADS=8               # 线程数"
    echo ""
    echo "使用示例:"
    echo "  ./start_gpu_server.sh -p          # 生产模式"
    echo "  ./start_gpu_server.sh -d          # 先诊断再启动"
    echo "  CUDA_VISIBLE_DEVICES=1 ./start_gpu_server.sh  # 使用GPU1"
    exit 0
elif [ "$1" == "--production" ] || [ "$1" == "-p" ]; then
    echo "🎯 生产模式启动 (推荐)"
    exec python app_production.py
elif [ "$1" == "--gunicorn" ] || [ "$1" == "-g" ]; then
    echo "🎯 直接Gunicorn启动"
    exec gunicorn --config gunicorn.conf.py app_server:app
elif [ "$1" == "--flask" ] || [ "$1" == "-f" ]; then
    echo "🎯 Flask开发模式启动 (调试用)"
    echo "⚠️  注意: Flask模式仅用于调试，生产环境请使用 -p 选项"
    exec python app_server.py
else
    echo "🎯 默认生产模式启动"
    echo "提示: 使用 $0 --help 查看更多选项"
    exec python app_production.py
fi 