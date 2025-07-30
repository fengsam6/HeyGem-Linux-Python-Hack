#!/usr/bin/env python
# coding=utf-8
"""
GPU修复测试脚本
验证Gunicorn + GPU环境是否正常工作
"""

import requests
import json
import time
import subprocess
import sys
import os

def test_gpu_status(base_url="http://localhost:8383"):
    """测试GPU状态接口"""
    print("🔍 测试GPU状态接口...")
    try:
        response = requests.get(f"{base_url}/gpu/status", timeout=30)
        if response.status_code == 200:
            data = response.json()
            print("✅ GPU状态接口响应正常")
            
            # 解析响应
            if data.get('success'):
                gpu_info = data.get('data', {})
                print(f"📊 Worker PID: {gpu_info.get('worker_pid')}")
                print(f"🤖 模型已初始化: {gpu_info.get('models_initialized')}")
                print(f"🔧 CUDA设备: {gpu_info.get('cuda_visible_devices')}")
                
                # 检查ONNX Runtime
                if gpu_info.get('onnx_cuda_available'):
                    print("✅ ONNX Runtime CUDA: 可用")
                else:
                    print("❌ ONNX Runtime CUDA: 不可用")
                    print(f"   可用providers: {gpu_info.get('onnx_providers', [])}")
                
                # 检查PyTorch
                if gpu_info.get('pytorch_cuda_available'):
                    print("✅ PyTorch CUDA: 可用")
                    print(f"   GPU数量: {gpu_info.get('pytorch_gpu_count')}")
                    print(f"   GPU名称: {gpu_info.get('pytorch_gpu_name')}")
                    memory = gpu_info.get('pytorch_memory', {})
                    print(f"   显存使用: {memory.get('allocated_gb', 0):.2f}GB")
                else:
                    print("❌ PyTorch CUDA: 不可用")
                
                return gpu_info.get('onnx_cuda_available', False)
            else:
                print(f"❌ GPU状态检查失败: {data.get('msg')}")
                return False
        else:
            print(f"❌ HTTP请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 测试GPU状态时出错: {e}")
        return False

def test_health_check(base_url="http://localhost:8383"):
    """测试健康检查接口"""
    print("\n💊 测试健康检查接口...")
    try:
        response = requests.get(f"{base_url}/health", timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                health_info = data.get('data', {})
                print("✅ 服务健康检查通过")
                print(f"📊 Worker PID: {health_info.get('worker_pid')}")
                print(f"🤖 模型已初始化: {health_info.get('models_initialized')}")
                print(f"📋 队列长度: {health_info.get('queue_size')}")
                print(f"🏃 当前任务数: {health_info.get('current_tasks')}")
                return True
            else:
                print(f"❌ 健康检查失败: {data.get('msg')}")
                return False
        else:
            print(f"❌ HTTP请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查时出错: {e}")
        return False

def wait_for_service(base_url="http://localhost:8383", max_wait=60):
    """等待服务启动"""
    print(f"⏳ 等待服务启动 (最多{max_wait}秒)...")
    
    for i in range(max_wait):
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ 服务已启动 (等待了{i+1}秒)")
                return True
        except:
            pass
        
        if i % 10 == 0 and i > 0:
            print(f"   仍在等待... ({i}秒)")
        time.sleep(1)
    
    print(f"❌ 服务在{max_wait}秒内未启动")
    return False

def check_gunicorn_config():
    """检查Gunicorn配置"""
    print("\n🔧 检查Gunicorn配置...")
    
    if not os.path.exists('gunicorn.conf.py'):
        print("❌ gunicorn.conf.py不存在")
        return False
    
    with open('gunicorn.conf.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
        checks = {
            'preload_app = False': '✅' if 'preload_app = False' in content else '❌',
            'workers = 1': '✅' if ('workers = 1' in content or 'workers = int(os.environ.get(\'GUNICORN_WORKERS\', 1))' in content) else '⚠️',
            'CUDA环境变量': '✅' if 'CUDA_VISIBLE_DEVICES' in content else '⚠️',
            'post_fork钩子': '✅' if 'def post_fork' in content else '❌',
        }
        
        print("配置检查结果:")
        for check, status in checks.items():
            print(f"  {status} {check}")
        
        return all(status == '✅' for status in checks.values())

def run_quick_test():
    """运行快速测试"""
    print("="*60)
    print("HeyGem AI - GPU修复验证测试")
    print("CUDA多进程兼容性检查")
    print("="*60)
    
    # 检查配置
    config_ok = check_gunicorn_config()
    if not config_ok:
        print("\n⚠️  配置检查发现问题，建议检查gunicorn.conf.py")
    
    # 等待服务
    if not wait_for_service():
        print("\n❌ 无法连接到服务，请确保服务已启动")
        print("\n📋 启动建议:")
        print("1. 简化版启动器（推荐）: python start_simple_gpu_server.py")
        print("2. CUDA兼容启动器: python start_cuda_fixed_server.py")
        print("3. GPU优化脚本: ./start_gpu_server.sh")
        print("4. 手动启动: python app_production.py")
        print("5. 直接Gunicorn: gunicorn --config gunicorn.conf.py app_server:app")
        return False
    
    # 测试GPU状态
    gpu_ok = test_gpu_status()
    
    # 测试健康检查
    health_ok = test_health_check()
    
    print("\n" + "="*60)
    print("测试结果总结:")
    print("="*60)
    
    if gpu_ok and health_ok:
        print("🎉 恭喜！GPU修复成功!")
        print("✅ ONNX Runtime GPU可用")
        print("✅ 模型已在worker进程中正确初始化")
        print("✅ Gunicorn + GPU环境正常工作")
        print("\n🚀 现在可以正常使用GPU加速的AI服务了！")
        return True
    else:
        print("❌ GPU修复验证失败")
        if not gpu_ok:
            print("❌ GPU不可用或未正确初始化")
        if not health_ok:
            print("❌ 服务健康检查失败")
        
        print("\n🔧 故障排查建议:")
        print("1. 运行详细诊断: python check_gpu_gunicorn.py")
        print("2. 检查服务日志中的post_fork信息")
        print("3. 确认GPU环境变量设置正确")
        print("4. 验证CUDA驱动和onnxruntime-gpu安装")
        print("5. 如果遇到CUDA多进程错误，使用: python start_cuda_fixed_server.py")
        return False

def run_stress_test():
    """运行压力测试（可选）"""
    print("\n" + "="*60)
    print("GPU压力测试 (可选)")
    print("="*60)
    
    choice = input("是否运行GPU压力测试? (y/N): ").lower()
    if choice != 'y':
        print("跳过压力测试")
        return
    
    print("🔥 开始GPU压力测试...")
    
    # 发送多个并发请求测试GPU稳定性
    for i in range(5):
        print(f"测试轮次 {i+1}/5...")
        gpu_ok = test_gpu_status()
        if not gpu_ok:
            print(f"❌ 第{i+1}轮测试失败")
            break
        time.sleep(2)
    else:
        print("✅ GPU压力测试通过！")

if __name__ == "__main__":
    try:
        # 运行主测试
        success = run_quick_test()
        
        if success:
            # 可选的压力测试
            run_stress_test()
        
        # 退出码
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 