#!/usr/bin/env python
# coding=utf-8
"""
Gunicorn启动问题诊断脚本
"""
import os
import sys
import subprocess
from service.self_logger import logger

def check_environment():
    """检查环境"""
    print("🔍 环境检查")
    print(f"Python版本: {sys.version}")
    print(f"工作目录: {os.getcwd()}")
    print(f"CUDA_VISIBLE_DEVICES: {os.environ.get('CUDA_VISIBLE_DEVICES', '未设置')}")
    
    # 检查文件是否存在
    files_to_check = ['app_server.py', 'gunicorn.conf.py', 'service/__init__.py']
    for file in files_to_check:
        exists = os.path.exists(file)
        print(f"文件 {file}: {'✅存在' if exists else '❌不存在'}")

def check_imports():
    """检查关键模块导入"""
    print("\n📦 模块导入检查")
    
    modules = [
        'gunicorn',
        'flask', 
        'service.trans_dh_service',
        'torch'
    ]
    
    for module in modules:
        try:
            __import__(module)
            print(f"模块 {module}: ✅可导入")
        except ImportError as e:
            print(f"模块 {module}: ❌导入失败 - {e}")

def test_app_server_import():
    """测试app_server导入"""
    print("\n🎯 测试app_server导入")
    try:
        import app_server
        print("✅ app_server导入成功")
        
        # 检查app对象
        if hasattr(app_server, 'app'):
            print("✅ Flask app对象存在")
        else:
            print("❌ Flask app对象不存在")
            
    except Exception as e:
        print(f"❌ app_server导入失败: {e}")
        import traceback
        traceback.print_exc()

def test_gunicorn_command():
    """测试gunicorn命令"""
    print("\n🚀 测试gunicorn命令")
    
    # 设置环境变量
    env = os.environ.copy()
    env['CUDA_VISIBLE_DEVICES'] = '0'
    
    cmd = [sys.executable, '-m', 'gunicorn', '--version']
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        print(f"gunicorn版本: {result.stdout.strip()}")
        
        # 测试配置文件
        cmd2 = [sys.executable, '-m', 'gunicorn', '--check-config', '--config', 'gunicorn.conf.py', 'app_server:app']
        result2 = subprocess.run(cmd2, capture_output=True, text=True, env=env)
        
        if result2.returncode == 0:
            print("✅ gunicorn配置检查通过")
        else:
            print(f"❌ gunicorn配置检查失败:")
            print(f"STDOUT: {result2.stdout}")
            print(f"STDERR: {result2.stderr}")
            
    except Exception as e:
        print(f"❌ gunicorn命令测试失败: {e}")

def test_minimal_flask():
    """测试最小Flask应用"""
    print("\n🧪 测试最小Flask应用")
    try:
        from flask import Flask
        test_app = Flask(__name__)
        
        @test_app.route('/')
        def hello():
            return "Hello World"
            
        print("✅ 基本Flask应用可以创建")
        
        # 测试是否可以运行
        with test_app.test_client() as client:
            response = client.get('/')
            print(f"✅ Flask测试请求成功: {response.data}")
            
    except Exception as e:
        print(f"❌ Flask基本测试失败: {e}")

def main():
    print("🔧 Gunicorn启动问题诊断")
    print("=" * 50)
    
    check_environment()
    check_imports()
    test_app_server_import()
    test_gunicorn_command()
    test_minimal_flask()
    
    print("\n" + "=" * 50)
    print("📋 诊断完成")
    print("\n💡 请把诊断结果发给我，我来分析具体问题")

if __name__ == '__main__':
    main() 