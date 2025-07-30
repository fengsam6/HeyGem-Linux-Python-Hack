#!/usr/bin/env python
# coding=utf-8
"""
测试生产模式启动，帮助调试问题
"""
import os
import sys

# GPU配置
os.environ['CUDA_VISIBLE_DEVICES'] = os.environ.get('CUDA_VISIBLE_DEVICES', '0')
os.chdir('/code')

print("🔍 调试信息:")
print(f"  Python版本: {sys.version}")
print(f"  工作目录: {os.getcwd()}")
print(f"  CUDA_VISIBLE_DEVICES: {os.environ.get('CUDA_VISIBLE_DEVICES')}")
print(f"  Python路径: {sys.path[:3]}...")

# 测试1: 检查能否导入模块
print("\n🔍 测试模块导入:")
try:
    from service.trans_dh_service import TransDhTask, Status, task_dic, a, init_p
    print("  ✅ AI服务模块导入成功")
except Exception as e:
    print(f"  ❌ AI服务模块导入失败: {e}")
    import traceback
    traceback.print_exc()

# 测试2: 检查Gunicorn
print("\n🔍 测试Gunicorn:")
try:
    import gunicorn
    print(f"  ✅ Gunicorn版本: {gunicorn.__version__}")
except ImportError:
    print("  ❌ Gunicorn未安装")

# 测试3: 检查PyTorch GPU
print("\n🔍 测试PyTorch GPU:")
try:
    import torch
    print(f"  PyTorch版本: {torch.__version__}")
    print(f"  CUDA可用: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"  GPU数量: {torch.cuda.device_count()}")
        print(f"  当前设备: {torch.cuda.current_device()}")
except Exception as e:
    print(f"  ❌ PyTorch检查失败: {e}")

# 测试4: 直接测试Gunicorn命令
print("\n🔍 测试Gunicorn命令:")
import subprocess
try:
    result = subprocess.run([sys.executable, '-m', 'gunicorn', '--version'], 
                          capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        print(f"  ✅ Gunicorn命令可用: {result.stdout.strip()}")
    else:
        print(f"  ❌ Gunicorn命令失败: {result.stderr}")
except Exception as e:
    print(f"  ❌ Gunicorn命令测试失败: {e}")

# 测试5: 尝试启动Gunicorn（短时间）
print("\n🔍 测试Gunicorn启动:")
try:
    # 尝试启动gunicorn但立即停止
    print("  准备启动gunicorn进行测试...")
    cmd = f"{sys.executable} -m gunicorn --config gunicorn.conf.py app_server:app --timeout 5 --preload"
    print(f"  命令: {cmd}")
    
    # 注意：这里不实际启动，只是验证命令
    print("  提示：如要实际测试，请手动运行上述命令")
    
except Exception as e:
    print(f"  ❌ Gunicorn启动测试失败: {e}")

print("\n✅ 测试完成")
print("💡 建议:")
print("   1. 如果模块导入失败，检查Python路径")
print("   2. 如果GPU不可用，检查CUDA环境")
print("   3. 如果Gunicorn启动失败，查看详细错误日志")
print("   4. 尝试手动运行: python -m gunicorn --config gunicorn.conf.py app_server:app") 