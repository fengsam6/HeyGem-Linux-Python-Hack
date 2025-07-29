#!/usr/bin/env python
# coding=utf-8
"""
生产环境启动文件 - 使用Gunicorn替代Flask开发服务器
避免 "This is a development server" 警告
"""
import os
import sys
import time
import subprocess
import signal
from service.self_logger import logger

# 确保工作目录正确
os.chdir('/code')

def start_with_gunicorn():
    """使用Gunicorn启动生产服务器"""
    try:
        # 读取配置
        from service.config import server_ip, server_port
        
        # 初始化服务
        from service.trans_dh_service import a, init_p
        from service.config import temp_dir, result_dir
        
        # 执行初始化
        a()
        init_p()
        time.sleep(15)
        
        # 创建必要目录
        if not os.path.exists(temp_dir):
            logger.info("创建临时目录")
            os.makedirs(temp_dir)
        if not os.path.exists(result_dir):
            logger.info("创建结果目录")
            os.makedirs(result_dir)
        
        logger.info("******************* TransDhServer服务启动（生产模式）*******************")
        
        # 检查gunicorn命令是否可用
        gunicorn_available = False
        gunicorn_cmd = None
        
        # 尝试直接使用gunicorn命令
        try:
            subprocess.check_output(['gunicorn', '--version'], stderr=subprocess.STDOUT)
            gunicorn_cmd = ['gunicorn', '--config', 'gunicorn.conf.py', 'app_server:app']
            gunicorn_available = True
            logger.info("使用gunicorn命令启动")
        except (subprocess.CalledProcessError, FileNotFoundError):
            # 尝试使用python -m gunicorn
            try:
                subprocess.check_output([sys.executable, '-m', 'gunicorn', '--version'], stderr=subprocess.STDOUT)
                gunicorn_cmd = [sys.executable, '-m', 'gunicorn', '--config', 'gunicorn.conf.py', 'app_server:app']
                gunicorn_available = True
                logger.info("使用python -m gunicorn启动")
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.warning("gunicorn命令不可用，将回退到Flask服务器")
        
        if not gunicorn_available or not gunicorn_cmd:
            raise ImportError("Gunicorn命令不可用")
        
        logger.info(f"启动Gunicorn服务器: {' '.join(gunicorn_cmd)}")
        
        # 启动Gunicorn
        process = subprocess.Popen(gunicorn_cmd)
        
        # 处理信号
        def signal_handler(sig, frame):
            logger.info("接收到停止信号，正在关闭服务...")
            process.terminate()
            process.wait()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # 等待进程结束
        process.wait()
        
    except ImportError:
        logger.warning("Gunicorn未安装，尝试安装...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'gunicorn'])
        # 重新启动
        start_with_gunicorn()
    except Exception as e:
        logger.error(f"启动服务失败: {e}")
        # 如果Gunicorn启动失败，回退到Flask开发服务器
        logger.warning("回退到Flask开发服务器（会有警告提示）")
        fallback_to_flask()

def fallback_to_flask():
    """回退到Flask开发服务器"""
    try:
        from app_server import app
        from service.config import server_ip, server_port
        from service.trans_dh_service import a, init_p
        from service.config import temp_dir, result_dir
        
        a()
        init_p()
        time.sleep(15)
        
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        if not os.path.exists(result_dir):
            os.makedirs(result_dir)
            
        logger.warning("使用Flask开发服务器启动（生产环境建议使用Gunicorn）")
        app.run(
            host=str(server_ip),
            port=int(server_port),
            debug=False,
            threaded=True
        )
    except Exception as e:
        logger.error(f"启动Flask服务器失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    start_with_gunicorn() 