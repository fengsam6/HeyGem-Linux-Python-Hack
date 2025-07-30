#!/usr/bin/env python
# coding=utf-8
"""
最简单的生产模式启动 - 直接使用gunicorn.run()
"""
import os
import sys

# GPU配置
os.environ['CUDA_VISIBLE_DEVICES'] = os.environ.get('CUDA_VISIBLE_DEVICES', '0')
os.chdir('/code')

def main():
    """主函数"""
    print("🚀 启动HeyGem AI服务（生产模式）")
    
    try:
        # 方法1: 直接使用gunicorn.run()
        from gunicorn.app.wsgiapp import run
        
        # 设置命令行参数
        sys.argv = [
            'gunicorn',
            '--config', 'gunicorn.conf.py',
            'app_server:app'
        ]
        
        print("✅ 使用gunicorn.app.wsgiapp.run()启动")
        run()
        
    except ImportError:
        print("❌ 方法1失败，尝试方法2...")
        
        try:
            # 方法2: 使用Gunicorn应用类
            from gunicorn.app.base import BaseApplication
            from importlib import import_module
            
            class StandaloneApplication(BaseApplication):
                def __init__(self, app, options=None):
                    self.options = options or {}
                    self.application = app
                    super().__init__()
                
                def load_config(self):
                    # 从gunicorn.conf.py加载配置
                    config_module = import_module('gunicorn.conf')
                    for key, value in vars(config_module).items():
                        if not key.startswith('_') and hasattr(self.cfg, key):
                            self.cfg.set(key, value)
                
                def load(self):
                    return self.application
            
            # 导入app
            from app_server import app
            
            # 启动配置
            options = {
                'bind': '0.0.0.0:8383',
                'workers': 1,
                'worker_class': 'sync',
                'timeout': 600,
                'preload_app': True,
            }
            
            print("✅ 使用StandaloneApplication启动")
            StandaloneApplication(app, options).run()
            
        except Exception as e2:
            print(f"❌ 方法2也失败: {e2}")
            print("🔄 回退到直接运行app_server.py")
            
            # 方法3: 直接导入运行
            import app_server
            # app_server.py的if __name__ == '__main__'会自动执行

if __name__ == '__main__':
    main() 