#!/usr/bin/env python
# coding=utf-8
"""
简化版GPU服务启动脚本
专注解决模块导入问题，避免复杂的multiprocessing设置
"""

import os
import sys
import subprocess
import signal

def setup_environment():
    """设置基础环境"""
    print("🔧 配置环境...")
    
    # 确保工作目录正确
    expected_dir = '/code'
    current_dir = os.getcwd()
    
    print(f"当前工作目录: {current_dir}")
    
    if os.path.exists(expected_dir) and not current_dir.endswith('code'):
        os.chdir(expected_dir)
        print(f"✅ 切换工作目录到: {expected_dir}")
        current_dir = expected_dir
    
    # 初始化CUDA安全环境
    try:
        from cuda_fork_fix import init_cuda_safe_environment
        init_cuda_safe_environment()
        print("✅ CUDA fork修复模块已加载")
    except ImportError:
        print("⚠️  CUDA fork修复模块不可用，使用传统方法")
        
        # 设置GPU环境变量
        os.environ['CUDA_VISIBLE_DEVICES'] = os.environ.get('CUDA_VISIBLE_DEVICES', '0')
        os.environ['NVIDIA_VISIBLE_DEVICES'] = os.environ.get('NVIDIA_VISIBLE_DEVICES', '0')
        os.environ['PYTORCH_CUDA_ALLOC_CONF'] = os.environ.get('PYTORCH_CUDA_ALLOC_CONF', 'max_split_size_mb:512')
        os.environ['CUDA_LAUNCH_BLOCKING'] = '1'
    
    # 设置Gunicorn环境变量
    os.environ['GUNICORN_WORKERS'] = '1'  # 强制单进程
    os.environ['GUNICORN_WORKER_CLASS'] = 'gthread'
    os.environ['GUNICORN_THREADS'] = '8'
    os.environ['GUNICORN_TIMEOUT'] = '600'
    os.environ['GUNICORN_MAX_MEMORY'] = '8192'
    
    print("✅ 环境配置完成")
    
    # 检查关键文件
    required_files = ['gunicorn.conf.py', 'app_server.py']
    missing_files = []
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}: 存在")
        else:
            missing_files.append(file)
            print(f"❌ {file}: 缺失")
    
    if missing_files:
        print(f"❌ 缺少必要文件: {missing_files}")
        return False
    
    # 检查service目录
    if os.path.exists('service'):
        print("✅ service目录: 存在")
    else:
        print("❌ service目录: 缺失")
        return False
    
    return True

def start_gunicorn():
    """启动Gunicorn服务"""
    print("🚀 启动Gunicorn服务器...")
    
    cmd = [
        sys.executable, '-m', 'gunicorn',
        '--config', 'gunicorn.conf.py',
        'app_server:app'
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    
    try:
        process = subprocess.Popen(cmd)
        
        def signal_handler(sig, frame):
            print("\n⚠️  收到停止信号，正在关闭服务...")
            process.terminate()
            process.wait()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        print("✅ 服务器已启动")
        print("📋 API地址:")
        print("   - GPU状态: http://localhost:8383/gpu/status")
        print("   - 健康检查: http://localhost:8383/health")
        print("   - 提交任务: http://localhost:8383/easy/submit")
        print("\n按 Ctrl+C 停止服务")
        
        return_code = process.wait()
        
        if return_code == 0:
            print("✅ 服务正常退出")
            return True
        else:
            print(f"❌ 服务异常退出，返回码: {return_code}")
            return False
            
    except FileNotFoundError:
        print("❌ Gunicorn未找到，请确保已安装")
        return False
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return False

def start_flask_fallback():
    """回退到Flask"""
    print("🔄 尝试Flask开发服务器...")
    
    try:
        # 直接执行Python文件
        cmd = [sys.executable, 'app_server.py']
        
        print(f"执行命令: {' '.join(cmd)}")
        
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

def main():
    """主函数"""
    print("="*60)
    print("HeyGem AI - 简化版GPU服务启动器")
    print("解决模块导入问题的专用版本")
    print("="*60)
    
    # 设置环境
    if not setup_environment():
        print("❌ 环境设置失败")
        sys.exit(1)
    
    # 选择启动模式
    mode = sys.argv[1] if len(sys.argv) > 1 else 'auto'
    
    success = False
    
    if mode == 'flask':
        success = start_flask_fallback()
    elif mode == 'gunicorn':
        success = start_gunicorn()
    else:  # auto mode
        # 先尝试Gunicorn，失败则回退到Flask
        print("📋 自动模式：先尝试Gunicorn，失败则回退到Flask")
        success = start_gunicorn()
        
        if not success:
            print("\n🔄 Gunicorn启动失败，回退到Flask...")
            success = start_flask_fallback()
    
    if success:
        print("\n✅ 服务启动成功")
    else:
        print("\n❌ 所有启动方式都失败了")
        print("\n🔧 故障排查建议:")
        print("1. 检查当前工作目录是否为项目根目录")
        print("2. 确认service/trans_dh_service.py文件存在")
        print("3. 运行诊断: python check_gpu_gunicorn.py")
        print("4. 查看详细日志确定具体错误")
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