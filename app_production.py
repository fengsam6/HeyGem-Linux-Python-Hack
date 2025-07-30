#!/usr/bin/env python
# coding=utf-8
"""
生产环境启动文件 - 使用Gunicorn替代Flask开发服务器
避免 "This is a development server" 警告
"""
import os
import sys
from service.self_logger import logger

# GPU配置
os.environ['CUDA_VISIBLE_DEVICES'] = os.environ.get('CUDA_VISIBLE_DEVICES', '0')

# 确保工作目录正确
os.chdir('/code')

def start_with_gunicorn():
    """使用Gunicorn启动生产服务器"""
    try:
        logger.info("******************* TransDhServer服务启动（生产模式）*******************")
        
        # 直接在当前进程中使用gunicorn，避免进程隔离问题
        try:
            from gunicorn.app.base import BaseApplication
            logger.info("使用Gunicorn BaseApplication启动")
            
            class ProductionApplication(BaseApplication):
                def __init__(self):
                    self.options = {
                        'bind': self.get_bind_address(),
                        'workers': 1,
                        'worker_class': 'sync', 
                        'timeout': 600,
                        'preload_app': True,
                        'proc_name': 'heygem-ai-server'
                    }
                    super().__init__()
                
                def get_bind_address(self):
                    try:
                        from service.config import server_ip, server_port
                        return f"{server_ip}:{server_port}"
                    except:
                        return "0.0.0.0:8383"
                
                def load_config(self):
                    for key, value in self.options.items():
                        if key in self.cfg.settings and value is not None:
                            self.cfg.set(key.lower(), value)
                
                def load(self):
                    # 直接导入app，确保在同一进程中
                    from app_server import app
                    return app
            
            # 启动应用
            ProductionApplication().run()
            
        except ImportError as e:
            logger.error(f"Gunicorn导入失败: {e}")
            raise Exception("Gunicorn not available")
                
    except Exception as e:
        logger.error(f"启动Gunicorn失败: {e}")
        logger.warning("回退到Flask开发服务器")
        fallback_to_flask()

def fallback_to_flask():
    """回退到直接运行app_server"""
    try:
        logger.warning("回退到直接运行app_server.py")
        logger.info("这将使用Flask开发服务器，但模型能正常工作")
        
        # 直接运行app_server的主逻辑
        import app_server
        # app_server.py的主逻辑会自动执行
        
    except Exception as e:
        logger.error(f"启动app_server失败: {e}")
        logger.error("尝试最简单的启动方式...")
        
        # 最后的备用方案：直接使用exec
        try:
            exec(open('app_server.py').read())
        except Exception as e2:
            logger.error(f"最后的启动方式也失败: {e2}")
            sys.exit(1)

if __name__ == '__main__':
    start_with_gunicorn()
