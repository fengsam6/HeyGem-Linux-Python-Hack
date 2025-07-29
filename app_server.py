#!/user/bin/env python
# coding=utf-8
"""
@project : face2face_train
@author  : huyi
@file   : app.py
@ide    : PyCharm
@time   : 2023-12-06 19:04:21
"""
import os

os.chdir('/code')
import time
import traceback
from enum import Enum
import configparser
import queue
from threading import Lock

from service.self_logger import logger
from flask import Flask, request
from service.config import *
from service.trans_dh_service import TransDhTask, Status,a, init_p, task_dic

import json
import threading
import gc
import cv2


class ConcurrencyManager:
    """并发管理器，支持可配置的并发数和队列等待"""

    def __init__(self, max_concurrent_tasks=4):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.current_tasks = 0
        self.task_queue = queue.Queue()
        self.lock = Lock()
        self.worker_thread = None
        self._start_worker()
        logger.info(f"并发管理器初始化完成，最大并发数: {max_concurrent_tasks}")

    def _start_worker(self):
        """启动工作线程来处理队列中的任务"""
        def worker():
            while True:
                try:
                    # 从队列中获取任务
                    task_info = self.task_queue.get(timeout=1)
                    if task_info is None:  # 停止信号
                        break

                    # 检查任务信息格式
                    if len(task_info) != 3:
                        logger.error(f"任务信息格式错误: {task_info}")
                        continue

                    # 等待可用的并发槽位
                    while True:
                        with self.lock:
                            if self.current_tasks < self.max_concurrent_tasks:
                                self.current_tasks += 1
                                break
                        time.sleep(0.1)

                    # 执行任务
                    task, args, task_id = task_info
                    try:
                        logger.info(f"开始执行任务: {task_id}, 当前并发数: {self.current_tasks}")
                        task(*args)
                    except Exception as e:
                        logger.error(f"任务执行异常 {task_id}: {e}")
                        traceback.print_exc()
                    finally:
                        # 释放并发槽位
                        with self.lock:
                            self.current_tasks -= 1
                        logger.info(f"任务完成: {task_id}, 当前并发数: {self.current_tasks}")

                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"工作线程异常: {e}")
                    traceback.print_exc()

        self.worker_thread = threading.Thread(target=worker, daemon=True)
        self.worker_thread.start()

    def submit_task(self, task, task_id, *args):
        """提交任务到队列"""
        self.task_queue.put((task, args, task_id))
        queue_size = self.task_queue.qsize()
        logger.info(f"任务已提交到队列: {task_id}, 队列长度: {queue_size}")
        return True

    def get_queue_size(self):
        """获取队列长度"""
        return self.task_queue.qsize()

    def get_current_tasks(self):
        """获取当前运行的任务数"""
        with self.lock:
            return self.current_tasks


def load_concurrent_config():
    """从配置文件加载并发配置"""
    try:
        config = configparser.ConfigParser()
        config.read('config/config.ini')
        batch_size = config.getint('digital', 'batch_size', fallback=4)
        logger.info(f"从配置文件读取并发数: {batch_size}")
        return batch_size
    except Exception as e:
        logger.warning(f"读取配置失败，使用默认并发数4: {e}")
        return 4


# 创建全局并发管理器
concurrent_tasks = load_concurrent_config()
concurrency_manager = ConcurrencyManager(concurrent_tasks)

app = Flask(__name__)


class EasyResponse:
    def __init__(
            self,
            code,
            success,
            msg, data: dict):
        self.code = code
        self.success = success
        self.msg = msg
        self.data = data


class ResponseCode(Enum):
    system_error = [9999, '系统异常']
    success = [10000, '成功']
    busy = [10001, '忙碌中']
    error1 = [10002, '参数异常']
    error2 = [10003, '获取锁异常']
    error3 = [10004, '任务不存在']
    duplicate_task = [10005, '任务已存在，正在执行中']

@app.route('/easy/submit', methods=['POST'])
def easy_submit():
    # 确保模型已初始化（Gunicorn环境下的安全措施）
    ensure_models_initialized()
    
    request_data = json.loads(request.data)
    _code = request_data['code']

    try:
        # 参数验证
        if 'audio_url' not in request_data or request_data['audio_url'] == '':
            return json.dumps(
                EasyResponse(ResponseCode.error1.value[0], False, 'audio_url参数缺失', {}),
                default=lambda obj: obj.__dict__,
                sort_keys=True, ensure_ascii=False,
                indent=4)
        if 'video_url' not in request_data or request_data['video_url'] == '':
            return json.dumps(
                EasyResponse(ResponseCode.error1.value[0], False, 'video_url参数缺失', {}),
                default=lambda obj: obj.__dict__,
                sort_keys=True, ensure_ascii=False,
                indent=4)
        if 'code' not in request_data or request_data['code'] == '':
            return json.dumps(
                EasyResponse(ResponseCode.error1.value[0], False, 'code参数缺失', {}),
                default=lambda obj: obj.__dict__,
                sort_keys=True, ensure_ascii=False,
                indent=4)

        # 检查任务是否已存在
        existing_task = task_dic.get(_code, None)
        if existing_task is not None:
            existing_status = existing_task[0]
            if existing_status == Status.run:
                # 任务正在执行中，返回重复任务提示
                logger.info(f"任务代码 {_code} 已存在且正在执行中，拒绝重复提交")
                return json.dumps(
                    EasyResponse(ResponseCode.duplicate_task.value[0], False, ResponseCode.duplicate_task.value[1],
                               {'code': _code, 'current_status': existing_status.value}),
                    default=lambda obj: obj.__dict__,
                    sort_keys=True, ensure_ascii=False,
                    indent=4)
            elif existing_status == Status.success or existing_status == Status.error:
                # 任务已完成或失败，清除旧记录，允许重新执行
                logger.info(f"任务代码 {_code} 已完成（状态：{existing_status.value}），清除旧记录并重新执行")
                try:
                    del task_dic[_code]
                except Exception as e:
                    logger.warning(f"清除旧任务记录失败: {e}")

        # 获取其他参数
        _audio_url = request_data['audio_url']
        _video_url = request_data['video_url']

        if 'watermark_switch' not in request_data or request_data['watermark_switch'] == '':
            _watermark_switch = 0
        else:
            if str(request_data['watermark_switch']) == '1':
                _watermark_switch = 1
            else:
                _watermark_switch = 0
        if 'digital_auth' not in request_data or request_data['digital_auth'] == '':
            _digital_auth = 0
        else:
            if str(request_data['digital_auth']) == '1':
                _digital_auth = 1
            else:
                _digital_auth = 0
        if 'chaofen' not in request_data or request_data['chaofen'] == '':
            _chaofen = 0
        else:
            if str(request_data['chaofen']) == '1':
                _chaofen = 1
            else:
                _chaofen = 0

        if 'pn' not in request_data or request_data['pn'] == '':
            _pn = 1
        else:
            if str(request_data['pn']) == '1':
                _pn = 1
            else:
                _pn = 0

        # 创建并提交任务
        task = TransDhTask(_code, _audio_url, _video_url, _watermark_switch, _digital_auth, _chaofen, _pn,)
        # 使用并发管理器提交任务到队列
        concurrency_manager.submit_task(task.work, _code)
        logger.info(f"新任务已提交: {_code}")

        return json.dumps(
            EasyResponse(ResponseCode.success.value[0], True, ResponseCode.success.value[1], {'code': _code}),
            default=lambda obj: obj.__dict__,
            sort_keys=True, ensure_ascii=False,
            indent=4)
    except Exception as e:
        logger.error(f"提交任务异常 {request_data}: {e}")
        traceback.print_exc()
        return json.dumps(
            EasyResponse(ResponseCode.system_error.value[0], False, ResponseCode.system_error.value[1], {}),
            default=lambda obj: obj.__dict__,
            sort_keys=True, ensure_ascii=False,
            indent=4)
    finally:
        gc.collect()


@app.route('/easy/query', methods=['GET'])
def easy_query():
    del_flag = False
    get_data = request.args.to_dict()
    try:
        _code = get_data.get('code', '-1')
        if _code == '-1':
            return json.dumps(
                EasyResponse(ResponseCode.error1.value[0], False, 'code参数缺失', {}),
                default=lambda obj: obj.__dict__,
                sort_keys=True, ensure_ascii=False,
                indent=4)
        task_progress = task_dic.get(_code, '-1')
        if task_progress != '-1':
            d = task_progress
            _status = d[0]
            _progress = d[1]
            _result = d[2]
            _msg = d[3]
            if _status == Status.run:
                return json.dumps(
                    EasyResponse(ResponseCode.success.value[0], True, '', {
                        'code': _code,
                        'status': _status.value,
                        'progress': _progress,
                        'result': _result,
                        'msg': _msg
                    }),
                    default=lambda obj: obj.__dict__,
                    sort_keys=True, ensure_ascii=False,
                    indent=4)
            elif _status == Status.success:
                del_flag = True
                return json.dumps(
                    EasyResponse(ResponseCode.success.value[0], True, '', {
                        'code': _code,
                        'status': _status.value,
                        'progress': _progress,
                        'result': _result,
                        'msg': _msg,
                        'cost': d[4],
                        "video_duration": d[5],
                        "width": d[6],
                        "height": d[7]
                    }),
                    default=lambda obj: obj.__dict__,
                    sort_keys=True, ensure_ascii=False,
                    indent=4)
            elif _status == Status.error:
                del_flag = True
                return json.dumps(
                    EasyResponse(ResponseCode.success.value[0], True, '', {
                        'code': _code,
                        'status': _status.value,
                        'progress': _progress,
                        'result': _result,
                        'msg': _msg
                    }),
                    default=lambda obj: obj.__dict__,
                    sort_keys=True, ensure_ascii=False, indent=4)
        else:
            return json.dumps(
                EasyResponse(ResponseCode.error3.value[0], True, ResponseCode.error3.value[1], {}),
                default=lambda obj: obj.__dict__,
                sort_keys=True, ensure_ascii=False,
                indent=4)
    except Exception as e:
        traceback.print_exc()
        return json.dumps(
            EasyResponse(ResponseCode.system_error.value[0], False, ResponseCode.system_error.value[1], {}),
            default=lambda obj: obj.__dict__,
            sort_keys=True, ensure_ascii=False,
            indent=4)
    finally:
        if del_flag:
            try:
                del task_dic[_code]
            except Exception as e:
                traceback.print_exc()
                return json.dumps(
                    EasyResponse(ResponseCode.error3.value[0], True, ResponseCode.error3.value[1], {}),
                    default=lambda obj: obj.__dict__,
                    sort_keys=True, ensure_ascii=False,
                    indent=4)


def init_models():
    """模型初始化函数 - 必须在worker进程中调用"""
    logger.info("开始初始化AI模型...")
    a()
    init_p()
    time.sleep(15)
    logger.info("AI模型初始化完成")

# 标记模型是否已初始化
_models_initialized = False

def ensure_models_initialized():
    """确保模型已初始化（用于Gunicorn环境）"""
    global _models_initialized
    if not _models_initialized:
        init_models()
        _models_initialized = True

# Flask应用上下文中的模型初始化（兼容新版本Flask）
def initialize_models_on_first_request():
    """Flask首次请求前初始化模型"""
    ensure_models_initialized()

# 尝试使用before_first_request（如果支持）
try:
    # Flask 2.2之前的版本
    app.before_first_request(initialize_models_on_first_request)
except AttributeError:
    # Flask 2.2+版本，我们将在路由中手动调用
    pass


@app.route('/gpu/status', methods=['GET'])
def gpu_status():
    """GPU状态检查接口"""
    try:
        import os
        status_info = {
            'worker_pid': os.getpid(),
            'models_initialized': _models_initialized,
            'cuda_visible_devices': os.environ.get('CUDA_VISIBLE_DEVICES', 'not_set'),
            'nvidia_visible_devices': os.environ.get('NVIDIA_VISIBLE_DEVICES', 'not_set'),
        }
        
        # 检查ONNX Runtime GPU
        try:
            import onnxruntime
            providers = onnxruntime.get_available_providers()
            status_info['onnx_providers'] = providers
            status_info['onnx_cuda_available'] = 'CUDAExecutionProvider' in providers
        except ImportError:
            status_info['onnx_runtime'] = 'not_installed'
        
        # 检查PyTorch CUDA
        try:
            import torch
            status_info['pytorch_cuda_available'] = torch.cuda.is_available()
            if torch.cuda.is_available():
                status_info['pytorch_gpu_count'] = torch.cuda.device_count()
                status_info['pytorch_current_device'] = torch.cuda.current_device()
                status_info['pytorch_gpu_name'] = torch.cuda.get_device_name(0)
                memory_allocated = torch.cuda.memory_allocated() / 1024**3
                memory_reserved = torch.cuda.memory_reserved() / 1024**3
                status_info['pytorch_memory'] = {
                    'allocated_gb': round(memory_allocated, 2),
                    'reserved_gb': round(memory_reserved, 2)
                }
        except ImportError:
            status_info['pytorch'] = 'not_installed'
        except Exception as e:
            status_info['pytorch_error'] = str(e)
        
        return json.dumps(
            EasyResponse(ResponseCode.success.value[0], True, 'GPU状态检查完成', status_info),
            default=lambda obj: obj.__dict__,
            sort_keys=True, ensure_ascii=False, indent=2)
            
    except Exception as e:
        logger.error(f"GPU状态检查异常: {e}")
        import traceback
        traceback.print_exc()
        return json.dumps(
            EasyResponse(ResponseCode.system_error.value[0], False, f'GPU状态检查失败: {str(e)}', {}),
            default=lambda obj: obj.__dict__,
            sort_keys=True, ensure_ascii=False, indent=2)


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    try:
        # 确保模型已初始化
        ensure_models_initialized()
        
        return json.dumps(
            EasyResponse(ResponseCode.success.value[0], True, '服务正常', {
                'status': 'healthy',
                'models_initialized': _models_initialized,
                'worker_pid': os.getpid(),
                'queue_size': concurrency_manager.get_queue_size(),
                'current_tasks': concurrency_manager.get_current_tasks()
            }),
            default=lambda obj: obj.__dict__,
            sort_keys=True, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps(
            EasyResponse(ResponseCode.system_error.value[0], False, f'健康检查失败: {str(e)}', {}),
            default=lambda obj: obj.__dict__,
            sort_keys=True, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    # Flask直接运行时才初始化模型
    init_models()
    logger.info("******************* TransDhServer服务启动 *******************")
    logger.info(f"并发控制配置 - 最大并发数: {concurrency_manager.max_concurrent_tasks}")
    logger.info("任务队列机制已启用，超出并发数的任务将排队等待")
    if not os.path.exists(temp_dir):
        logger.info("创建临时目录")
        os.makedirs(temp_dir)
    if not os.path.exists(result_dir):
        logger.info("创建结果目录")
        os.makedirs(result_dir)

    # 生产环境建议使用Gunicorn:
    # gunicorn -w 4 -b 0.0.0.0:8000 --timeout 300 app_server:app
    # 或者使用uWSGI:
    # uwsgi --http :8000 --module app_server:app --processes 4 --threads 2
    
    logger.info("使用Flask开发服务器启动（生产环境建议使用Gunicorn或uWSGI）")
    app.run(
        host=str(server_ip),
        port=int(server_port),
        debug=False,
        threaded=True)  # 启用多线程处理HTTP请求
