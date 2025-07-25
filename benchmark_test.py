#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务器性能对比测试脚本
用于测试不同WSGI服务器的并发性能
"""

import requests
import time
import threading
import json
from concurrent.futures import ThreadPoolExecutor, as_completed


def test_endpoint(url, test_data, timeout=30):
    """测试单个请求"""
    try:
        start_time = time.time()
        response = requests.post(
            f"{url}/easy/submit", 
            json=test_data,
            timeout=timeout
        )
        end_time = time.time()
        
        return {
            'success': response.status_code == 200,
            'status_code': response.status_code,
            'response_time': end_time - start_time,
            'response_size': len(response.content)
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'response_time': timeout
        }


def benchmark_server(base_url, concurrent_requests=10, total_requests=100):
    """压力测试服务器"""
    print(f"\n🚀 测试服务器: {base_url}")
    print(f"📊 并发数: {concurrent_requests}, 总请求数: {total_requests}")
    
    # 测试数据
    test_data = {
        "code": f"test_{int(time.time())}",
        "audio_url": "http://example.com/test.wav",
        "video_url": "http://example.com/test.mp4",
        "watermark_switch": "0",
        "digital_auth": "0",
        "chaofen": "0",
        "pn": "1"
    }
    
    results = []
    start_time = time.time()
    
    # 使用线程池进行并发测试
    with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
        # 提交所有任务
        futures = []
        for i in range(total_requests):
            # 每个请求使用不同的code避免重复
            current_data = test_data.copy()
            current_data["code"] = f"test_{int(time.time())}_{i}"
            future = executor.submit(test_endpoint, base_url, current_data)
            futures.append(future)
        
        # 收集结果
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append({'success': False, 'error': str(e)})
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # 统计结果
    successful = [r for r in results if r.get('success', False)]
    failed = [r for r in results if not r.get('success', False)]
    
    if successful:
        avg_response_time = sum(r['response_time'] for r in successful) / len(successful)
        min_response_time = min(r['response_time'] for r in successful)
        max_response_time = max(r['response_time'] for r in successful)
    else:
        avg_response_time = min_response_time = max_response_time = 0
    
    # 输出结果
    print(f"✅ 成功请求: {len(successful)}/{total_requests}")
    print(f"❌ 失败请求: {len(failed)}")
    print(f"⏱️  总耗时: {total_time:.2f}秒")
    print(f"🔥 吞吐量: {len(successful)/total_time:.2f} 请求/秒")
    print(f"📈 平均响应时间: {avg_response_time:.3f}秒")
    print(f"📉 最快响应: {min_response_time:.3f}秒")
    print(f"📊 最慢响应: {max_response_time:.3f}秒")
    
    return {
        'total_requests': total_requests,
        'successful_requests': len(successful),
        'failed_requests': len(failed),
        'total_time': total_time,
        'throughput': len(successful)/total_time if total_time > 0 else 0,
        'avg_response_time': avg_response_time,
        'min_response_time': min_response_time,
        'max_response_time': max_response_time
    }


def main():
    """主测试函数"""
    print("🧪 TransDhServer 性能对比测试")
    print("=" * 50)
    
    # 测试配置
    servers = [
        ("Flask开发服务器", "http://localhost:8000"),
        ("Gunicorn服务器", "http://localhost:8001"),
        ("uWSGI服务器", "http://localhost:8002")
    ]
    
    test_scenarios = [
        {"concurrent": 5, "total": 50, "name": "轻负载测试"},
        {"concurrent": 10, "total": 100, "name": "中等负载测试"},
        {"concurrent": 20, "total": 200, "name": "高负载测试"}
    ]
    
    results = {}
    
    for scenario in test_scenarios:
        print(f"\n🎯 {scenario['name']}")
        print("=" * 30)
        
        for server_name, server_url in servers:
            try:
                result = benchmark_server(
                    server_url, 
                    scenario['concurrent'], 
                    scenario['total']
                )
                results[f"{server_name}_{scenario['name']}"] = result
            except Exception as e:
                print(f"❌ {server_name} 测试失败: {e}")
    
    # 保存结果
    with open('benchmark_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📋 测试结果已保存到 benchmark_results.json")


if __name__ == "__main__":
    main() 