#!/usr/bin/env python
# coding=utf-8
"""
GPU + Gunicorn 环境诊断脚本
用于检查大模型服务在Gunicorn环境下的GPU配置是否正确
"""

import os
import sys
import subprocess
import traceback

def print_section(title):
    """打印分节标题"""
    print(f"\n{'='*50}")
    print(f" {title}")
    print(f"{'='*50}")

def check_basic_environment():
    """检查基础环境"""
    print_section("基础环境检查")
    
    # Python版本
    print(f"✅ Python版本: {sys.version}")
    
    # 环境变量
    cuda_visible = os.environ.get('CUDA_VISIBLE_DEVICES', '未设置')
    nvidia_visible = os.environ.get('NVIDIA_VISIBLE_DEVICES', '未设置')
    pytorch_conf = os.environ.get('PYTORCH_CUDA_ALLOC_CONF', '未设置')
    
    print(f"🔧 CUDA_VISIBLE_DEVICES: {cuda_visible}")
    print(f"🔧 NVIDIA_VISIBLE_DEVICES: {nvidia_visible}")
    print(f"🔧 PYTORCH_CUDA_ALLOC_CONF: {pytorch_conf}")

def check_nvidia_driver():
    """检查NVIDIA驱动"""
    print_section("NVIDIA驱动检查")
    
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ NVIDIA驱动正常")
            lines = result.stdout.split('\n')
            for line in lines:
                if 'Driver Version' in line:
                    print(f"📊 {line.strip()}")
                    break
        else:
            print("❌ nvidia-smi命令失败")
            print(result.stderr)
    except FileNotFoundError:
        print("❌ nvidia-smi命令未找到，请检查NVIDIA驱动安装")
    except Exception as e:
        print(f"❌ 检查NVIDIA驱动时出错: {e}")

def check_onnx_runtime():
    """检查ONNX Runtime GPU支持"""
    print_section("ONNX Runtime GPU检查")
    
    try:
        import onnxruntime
        print(f"✅ ONNX Runtime版本: {onnxruntime.__version__}")
        
        providers = onnxruntime.get_available_providers()
        print(f"📋 可用providers: {providers}")
        
        if 'CUDAExecutionProvider' in providers:
            print("✅ ONNX Runtime CUDA支持: 可用")
            
            # 尝试创建CUDA session
            try:
                session_options = onnxruntime.SessionOptions()
                session_options.log_severity_level = 3
                
                # 使用一个简单的模型测试（如果存在）
                test_model_paths = [
                    "./face_detect_utils/resources/scrfd_500m_bnkps_shape640x640.onnx",
                    "./check_env/test.onnx"  # 如果有测试模型
                ]
                
                model_found = False
                for model_path in test_model_paths:
                    if os.path.exists(model_path):
                        print(f"🧪 测试模型: {model_path}")
                        providers_list = [("CUDAExecutionProvider", {"device_id": 0})]
                        session = onnxruntime.InferenceSession(
                            model_path, 
                            session_options, 
                            providers=providers_list
                        )
                        actual_providers = session.get_providers()
                        print(f"✅ 实际使用的providers: {actual_providers}")
                        model_found = True
                        break
                
                if not model_found:
                    print("⚠️  未找到测试模型，无法验证CUDA功能")
                    
            except Exception as e:
                print(f"❌ CUDA session创建失败: {e}")
        else:
            print("❌ ONNX Runtime CUDA支持: 不可用")
            print("请检查是否安装了onnxruntime-gpu包")
            
    except ImportError:
        print("❌ ONNX Runtime未安装")
    except Exception as e:
        print(f"❌ 检查ONNX Runtime时出错: {e}")

def check_pytorch():
    """检查PyTorch CUDA支持"""
    print_section("PyTorch CUDA检查")
    
    try:
        import torch
        print(f"✅ PyTorch版本: {torch.__version__}")
        print(f"✅ CUDA编译版本: {torch.version.cuda}")
        
        if torch.cuda.is_available():
            print("✅ PyTorch CUDA支持: 可用")
            print(f"📊 GPU数量: {torch.cuda.device_count()}")
            
            for i in range(torch.cuda.device_count()):
                print(f"📊 GPU[{i}]: {torch.cuda.get_device_name(i)}")
                props = torch.cuda.get_device_properties(i)
                print(f"   - 显存: {props.total_memory / 1024**3:.1f}GB")
                print(f"   - 计算能力: {props.major}.{props.minor}")
            
            # 当前设备
            current_device = torch.cuda.current_device()
            print(f"📊 当前设备: GPU[{current_device}]")
            
            # 显存使用情况
            memory_allocated = torch.cuda.memory_allocated() / 1024**3
            memory_reserved = torch.cuda.memory_reserved() / 1024**3
            print(f"📊 显存使用: {memory_allocated:.2f}GB / 保留: {memory_reserved:.2f}GB")
            
        else:
            print("❌ PyTorch CUDA支持: 不可用")
            
    except ImportError:
        print("⚠️  PyTorch未安装")
    except Exception as e:
        print(f"❌ 检查PyTorch时出错: {e}")

def check_gunicorn_config():
    """检查Gunicorn配置"""
    print_section("Gunicorn配置检查")
    
    try:
        # 检查配置文件
        if os.path.exists('gunicorn.conf.py'):
            print("✅ gunicorn.conf.py存在")
            
            # 读取关键配置
            with open('gunicorn.conf.py', 'r', encoding='utf-8') as f:
                content = f.read()
                
                # 检查关键设置
                if 'preload_app = False' in content:
                    print("✅ preload_app = False (GPU应用必须)")
                elif 'preload_app = True' in content:
                    print("❌ preload_app = True (GPU应用应该为False)")
                else:
                    print("⚠️  未找到preload_app设置")
                
                if 'workers = 1' in content or 'workers = int(os.environ.get(\'GUNICORN_WORKERS\', 1))' in content:
                    print("✅ workers = 1 (推荐用于GPU应用)")
                else:
                    print("⚠️  workers > 1 可能导致GPU显存不足")
                
                if 'CUDA_VISIBLE_DEVICES' in content:
                    print("✅ 包含CUDA环境变量设置")
                else:
                    print("⚠️  未找到CUDA环境变量设置")
                    
        else:
            print("❌ gunicorn.conf.py不存在")
            
    except Exception as e:
        print(f"❌ 检查Gunicorn配置时出错: {e}")

def check_service_dependencies():
    """检查服务依赖"""
    print_section("服务依赖检查")
    
    try:
        # 检查关键模块
        modules_to_check = [
            'service.trans_dh_service',
            'cv2',
            'numpy', 
            'flask',
            'gunicorn'
        ]
        
        for module in modules_to_check:
            try:
                __import__(module)
                print(f"✅ {module}: 可用")
            except ImportError as e:
                print(f"❌ {module}: 不可用 - {e}")
                
    except Exception as e:
        print(f"❌ 检查依赖时出错: {e}")

def test_multiprocess_gpu():
    """测试多进程GPU访问"""
    print_section("多进程GPU测试")
    
    try:
        import multiprocessing
        
        def worker_gpu_test(worker_id):
            """Worker进程GPU测试"""
            try:
                # 设置GPU环境变量
                os.environ['CUDA_VISIBLE_DEVICES'] = '0'
                
                # 测试ONNX Runtime
                import onnxruntime
                providers = onnxruntime.get_available_providers()
                onnx_cuda = 'CUDAExecutionProvider' in providers
                
                # 测试PyTorch（如果可用）
                torch_cuda = False
                try:
                    import torch
                    torch_cuda = torch.cuda.is_available()
                except ImportError:
                    pass
                
                return f"Worker[{worker_id}]: ONNX={onnx_cuda}, PyTorch={torch_cuda}"
                
            except Exception as e:
                return f"Worker[{worker_id}]: Error - {e}"
        
        # 启动多个进程测试
        with multiprocessing.Pool(2) as pool:
            results = pool.map(worker_gpu_test, [1, 2])
            
        for result in results:
            print(f"🧪 {result}")
            
    except Exception as e:
        print(f"❌ 多进程GPU测试失败: {e}")

def main():
    """主函数"""
    print("HeyGem AI - GPU + Gunicorn 环境诊断")
    print("=" * 60)
    
    check_basic_environment()
    check_nvidia_driver()
    check_onnx_runtime()
    check_pytorch()
    check_gunicorn_config()
    check_service_dependencies()
    test_multiprocess_gpu()
    
    print_section("诊断完成")
    print("📋 建议检查项目:")
    print("1. 确保 preload_app = False")
    print("2. 建议 workers = 1 (避免GPU显存不足)")
    print("3. 确保CUDA环境变量正确设置")
    print("4. 模型必须在worker进程中初始化，不能在主进程")
    print("\n如果问题仍然存在，请检查日志中的post_fork信息")

if __name__ == "__main__":
    main() 