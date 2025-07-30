#!/usr/bin/env python
# coding=utf-8
"""
最简单的生产启动方案 - 直接运行app_server.py但添加生产环境配置
既然直接运行app_server.py能工作，就用这种方式，只是添加生产环境的设置
"""
import os
import sys
from service.self_logger import logger

# GPU配置
os.environ['CUDA_VISIBLE_DEVICES'] = os.environ.get('CUDA_VISIBLE_DEVICES', '0')

# 确保工作目录
os.chdir('/code')

# 生产环境设置
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = '0'

def main():
    """主函数"""
    logger.info("🚀 启动HeyGem AI服务（简单生产模式）")
    logger.info("💡 直接使用app_server.py，因为它已经验证可以工作")
    logger.info(f"📋 GPU设备: {os.environ.get('CUDA_VISIBLE_DEVICES')}")
    logger.info(f"📂 工作目录: {os.getcwd()}")
    
    try:
        # 最简单有效的方法：直接运行app_server.py
        logger.info("✅ 直接执行app_server主逻辑")
        
        # 方法1：直接导入执行
        import app_server
        
    except ImportError as e:
        logger.error(f"导入app_server失败: {e}")
        
        # 方法2：用exec执行文件
        try:
            logger.info("🔄 尝试exec方式执行")
            with open('app_server.py', 'r', encoding='utf-8') as f:
                exec(f.read(), {'__name__': '__main__'})
        except Exception as e2:
            logger.error(f"exec方式也失败: {e2}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 