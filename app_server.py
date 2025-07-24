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

@app.route('/easy/submit', methods=['POST'])
def easy_submit():
    request_data = json.loads(request.data)
    _code = request_data['code']
    
    try:
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
        _audio_url = request_data['audio_url']
        _video_url = request_data['video_url']
        _code = request_data['code']

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
        task = TransDhTask(_code, _audio_url, _video_url, _watermark_switch, _digital_auth, _chaofen, _pn,)
        # 使用并发管理器提交任务到队列
        concurrency_manager.submit_task(task.work, _code)
        return json.dumps(
            EasyResponse(ResponseCode.success.value[0], True, ResponseCode.success.value[0], {}),
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


if __name__ == '__main__':
    a()
    init_p()
    time.sleep(15)
    logger.info("******************* TransDhServer服务启动 *******************")
    logger.info(f"并发控制配置 - 最大并发数: {concurrency_manager.max_concurrent_tasks}")
    logger.info("任务队列机制已启用，超出并发数的任务将排队等待")
    if not os.path.exists(temp_dir):
        logger.info("创建临时目录")
        os.makedirs(temp_dir)
    if not os.path.exists(result_dir):
        logger.info("创建结果目录")
        os.makedirs(result_dir)

    app.run(
        host=str(server_ip),
        port=int(server_port),
        debug=False,
        threaded=False)
