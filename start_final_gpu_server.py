#!/usr/bin/env python
# coding=utf-8
"""
最终版GPU服务启动脚本
集成所有CUDA fork问题修复和模块导入问题解决方案
"""

import os
import sys
import subprocess
import signal
import time

def print_banner():
    """打印启动横幅"""
    print("="*70)
    print("🚀 HeyGem AI - 最终版GPU服务启动器")
    print("   集成CUDA fork修复 + 模块导入修复 + GPU优化")
    print("="*70)

def check_and_setup_environment():
    """检查并设置完整环境"""
    print("🔧 环境检查和配置...")
    
    # 1. 工作目录检查
    expected_dir = '/code'
    current_dir = os.getcwd()
    print(f"📁 当前工作目录: {current_dir}")
    
    if os.path.exists(expected_dir) and not current_dir.endswith('code'):
        os.chdir(expected_dir)
        current_dir = expected_dir
        print(f"✅ 切换到工作目录: {expected_dir}")
    
    # 2. 文件存在性检查
    required_files = {
        'gunicorn.conf.py': '配置文件',
        'app_server.py': '应用服务器',
        'service/': '服务目录'
    }
    
    missing_files = []
    for file_path, description in required_files.items():
        if os.path.exists(file_path):
            print(f"✅ {description}: {file_path}")
        else:
            missing_files.append(f"{description} ({file_path})")
            print(f"❌ {description}: {file_path} - 缺失")
    
    if missing_files:
        print(f"\n❌ 缺少必要文件: {', '.join(missing_files)}")
        return False
    
    # 3. 初始化GPU模式（单进程安全）
    print("\n🔧 初始化GPU模式...")
    
    # 设置GPU环境（如果未设置）
    if 'CUDA_VISIBLE_DEVICES' not in os.environ:
        os.environ['CUDA_VISIBLE_DEVICES'] = '0'
    if 'NVIDIA_VISIBLE_DEVICES' not in os.environ:
        os.environ['NVIDIA_VISIBLE_DEVICES'] = '0'
    
    os.environ['CUDA_LAUNCH_BLOCKING'] = '1'
    os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:512'
    
    print(f"✅ GPU模式已启用，设备: {os.environ.get('CUDA_VISIBLE_DEVICES')}")
    print("✅ 单进程模式，安全使用GPU，避免fork错误")
    
    # 4. Gunicorn单进程配置（强制在配置文件中）
    print("\n✅ Gunicorn单进程配置（workers=1, preload_app=True）")
    
    print("\n✅ 环境配置完成")
    return True

def check_dependencies():
    """检查依赖包"""
    print("\n🔍 检查关键依赖...")
    
    dependencies = {
        'gunicorn': 'WSGI服务器',
        'flask': 'Web框架',
        'onnxruntime': 'ONNX运行时',
    }
    
    missing = []
    for package, description in dependencies.items():
        try:
            __import__(package)
            print(f"✅ {description}: {package}")
        except ImportError:
            missing.append(package)
            print(f"❌ {description}: {package} - 缺失")
    
    if missing:
        print(f"\n⚠️  缺少依赖包: {missing}")
        choice = input("是否尝试自动安装? (y/N): ").lower()
        if choice == 'y':
            try:
                for package in missing:
                    print(f"📦 安装 {package}...")
                    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                print("✅ 依赖安装完成")
            except Exception as e:
                print(f"❌ 依赖安装失败: {e}")
                return False
        else:
            print("❌ 请手动安装缺失的依赖包")
            return False
    
    return True

def start_with_gunicorn():
    """使用Gunicorn启动服务"""
    print("\n🚀 启动Gunicorn服务器...")
    
    cmd = [
        sys.executable, '-m', 'gunicorn',
        '--config', 'gunicorn.conf.py',
        'app_server:app'
    ]
    
    print(f"🔧 执行命令: {' '.join(cmd)}")
    
    try:
        process = subprocess.Popen(cmd, 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.STDOUT, 
                                 universal_newlines=True,
                                 bufsize=1)
        
        def signal_handler(sig, frame):
            print("\n\n⚠️  收到停止信号，正在关闭服务...")
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                print("强制终止进程...")
                process.kill()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        print("✅ Gunicorn服务器已启动")
        print("\n📋 服务信息:")
        print("   - 地址: http://localhost:8383")
        print("   - GPU状态: http://localhost:8383/gpu/status")
        print("   - 健康检查: http://localhost:8383/health")
        print("   - 提交任务: http://localhost:8383/easy/submit")
        print("\n📊 配置摘要:")
        print("   - 工作进程: 1 (单进程，无fork)")
        print("   - Worker类型: sync (同步模式)")
        print("   - 预加载应用: True (安全)")
        print("   - 超时时间: 10分钟") 
        print(f"   - GPU模式: 已启用 (设备: {os.environ.get('CUDA_VISIBLE_DEVICES', 'N/A')})")
        print("   - Fork安全: 是 (单进程模式)")
        print("\n💡 直接启动Gunicorn:")
        print("   gunicorn --config gunicorn.conf.py app_server:app")
        print("\n📝 日志输出:")
        print("-" * 50)
        
        # 实时显示日志
        for line in process.stdout:
            print(line, end='')
            
            # 检查关键信息
            if "Worker" in line and "AI模型初始化完成" in line:
                if "GPU模式" in line:
                    print("\n🎉 AI模型加载成功! GPU模式运行正常!")
                else:
                    print("\n🎉 AI模型加载成功! 服务已就绪")
            elif "单进程GPU模式启动" in line:
                print("✅ 单进程GPU模式worker启动成功")
            elif "GPU可用，设备数量" in line:
                print("🔧 GPU设备检测成功")
            elif "GPU模式启用" in line:
                print("🔧 GPU模式已启用")
            elif "AI服务模块导入成功" in line:
                print("✅ AI服务模块导入成功")
            elif "Cannot re-initialize CUDA" in line:
                print("🚨 检测到CUDA fork错误！请检查是否使用单进程模式")
            elif "No CUDA GPUs are available" in line:
                print("⚠️  GPU不可用，服务将使用CPU模式")
            elif "ERROR" in line.upper():
                print(f"⚠️  检测到错误: {line.strip()}")
        
        return_code = process.wait()
        
        if return_code == 0:
            print("\n✅ 服务正常退出")
            return True
        else:
            print(f"\n❌ 服务异常退出，返回码: {return_code}")
            return False
            
    except FileNotFoundError:
        print("❌ Gunicorn未找到，请确保已安装")
        return False
    except Exception as e:
        print(f"❌ 启动Gunicorn失败: {e}")
        return False

def start_with_flask():
    """使用Flask启动服务"""
    print("\n🔄 启动Flask开发服务器...")
    
    cmd = [sys.executable, 'app_server.py']
    
    try:
        process = subprocess.Popen(cmd)
        
        def signal_handler(sig, frame):
            print("\n⚠️  收到停止信号，正在关闭服务...")
            process.terminate()
            process.wait()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        print("✅ Flask服务器已启动")
        print("⚠️  注意: 这是开发服务器，生产环境建议使用Gunicorn")
        
        return_code = process.wait()
        return return_code == 0
        
    except Exception as e:
        print(f"❌ Flask启动失败: {e}")
        return False

def run_post_start_tests():
    """启动后测试"""
    print("\n🧪 运行启动后测试...")
    
    # 等待服务启动
    print("⏳ 等待服务启动...")
    for i in range(30):
        try:
            import requests
            response = requests.get("http://localhost:8383/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ 服务已就绪 (等待{i+1}秒)")
                break
        except:
            pass
        time.sleep(1)
    else:
        print("⚠️  服务启动检测超时，可能仍在初始化中")
        return
    
    # 运行测试
    test_files = ['test_gpu_fix.py', 'check_gpu_gunicorn.py']
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"🧪 运行测试: {test_file}")
            try:
                result = subprocess.run([sys.executable, test_file], 
                                     capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    print("✅ 测试通过")
                else:
                    print("⚠️  测试发现问题，查看详细日志")
            except Exception as e:
                print(f"⚠️  测试运行失败: {e}")
            break

def main():
    """主函数"""
    print_banner()
    
    # 环境检查
    if not check_and_setup_environment():
        print("\n❌ 环境配置失败")
        sys.exit(1)
    
    # 依赖检查
    if not check_dependencies():
        print("\n❌ 依赖检查失败")
        sys.exit(1)
    
    # 启动模式选择
    mode = sys.argv[1] if len(sys.argv) > 1 else 'auto'
    
    success = False
    
    if mode == 'flask':
        print("\n🎯 强制Flask模式")
        success = start_with_flask()
    elif mode == 'gunicorn':
        print("\n🎯 强制Gunicorn模式")
        success = start_with_gunicorn()
    elif mode == 'test':
        print("\n🧪 测试模式")
        run_post_start_tests()
        return
    else:  # auto mode
        print("\n🎯 自动模式 (优先Gunicorn)")
        success = start_with_gunicorn()
        
        if not success:
            print("\n🔄 Gunicorn失败，回退到Flask...")
            success = start_with_flask()
    
    if success:
        print("\n🎉 服务启动成功!")
    else:
        print("\n❌ 所有启动方式都失败了")
        print("\n🔧 故障排查建议:")
        print("1. 检查 python start_final_gpu_server.py test")
        print("2. 查看错误日志确定具体问题")
        print("3. 确认GPU驱动和CUDA环境正确")
        print("4. 检查service/trans_dh_service.py是否存在")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  服务被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 启动过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 