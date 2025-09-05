#!/usr/bin/env python3
"""
波测API接口 - 供其他程序调用的波测功能
提供简单的函数接口来执行波测
"""

import sys
from pathlib import Path

# 添加domain_tester模块到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir / "domain_tester"))

from run_boce import run_boce

def test_domain(url: str, verbose: bool = False) -> dict:
    """
    测试域名的可用性和性能
    
    Args:
        url (str): 要测试的URL地址
        verbose (bool): 是否返回详细信息，默认False
    
    Returns:
        dict: 测试结果，包含以下字段：
            - success (bool): 测试是否成功执行
            - available (bool): 域名是否可用 (成功率>=80%)
            - success_rate (float): 成功率百分比
            - avg_response_time (float): 平均响应时间(ms)
            - total_checks (int): 总检测点数量
            - success_checks (int): 成功检测点数量
            - details (dict): 详细信息（仅在verbose=True时返回）
    
    Example:
        >>> result = test_domain("github.com")
        >>> print(f"域名可用: {result['available']}")
        >>> print(f"成功率: {result['success_rate']:.2f}%")
        
        >>> result = test_domain("github.com", verbose=True)
        >>> print(f"最高延迟地区: {result['details']['max_latency_area']}")
    """
    try:
        # 执行波测
        raw_result = run_boce(url)
        
        if raw_result is None:
            return {
                'success': False,
                'available': False,
                'success_rate': 0.0,
                'avg_response_time': 0.0,
                'total_checks': 0,
                'success_checks': 0,
                'error': '波测执行失败'
            }
        
        # 构建基础结果
        result = {
            'success': True,
            'available': raw_result['is_available'],
            'success_rate': round(raw_result['success_rate'], 2),
            'avg_response_time': round(raw_result['average_response_time_ms'], 2),
            'total_checks': raw_result['total_checks'],
            'success_checks': raw_result['success_checks']
        }
        
        # 如果需要详细信息
        if verbose:
            result['details'] = {
                'max_latency_area': raw_result['max_latency_area'],
                'max_latency_value': raw_result['max_latency_value'],
                'min_latency_area': raw_result['min_latency_area'],
                'min_latency_value': raw_result['min_latency_value'],
                'unavailable_areas': raw_result['unavailable_areas'],
                'error_status_distribution': raw_result['error_status_distribution'],
                'isp_analysis': raw_result['isp_analysis']
            }
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'available': False,
            'success_rate': 0.0,
            'avg_response_time': 0.0,
            'total_checks': 0,
            'success_checks': 0,
            'error': str(e)
        }

def quick_check(url: str) -> bool:
    """
    快速检查域名是否可用
    
    Args:
        url (str): 要测试的URL地址
    
    Returns:
        bool: 域名是否可用
    
    Example:
        >>> if quick_check("github.com"):
        >>>     print("域名可用")
        >>> else:
        >>>     print("域名不可用")
    """
    result = test_domain(url)
    return result['available']

def get_domain_performance(url: str) -> dict:
    """
    获取域名性能指标
    
    Args:
        url (str): 要测试的URL地址
    
    Returns:
        dict: 性能指标，包含：
            - success_rate: 成功率
            - avg_response_time: 平均响应时间
            - fastest_area: 最快地区
            - slowest_area: 最慢地区
    
    Example:
        >>> perf = get_domain_performance("github.com")
        >>> print(f"平均响应时间: {perf['avg_response_time']}ms")
        >>> print(f"最快地区: {perf['fastest_area']}")
    """
    result = test_domain(url, verbose=True)
    
    if not result['success']:
        return {
            'success_rate': 0.0,
            'avg_response_time': 0.0,
            'fastest_area': 'N/A',
            'slowest_area': 'N/A',
            'error': result.get('error', '未知错误')
        }
    
    details = result.get('details', {})
    return {
        'success_rate': result['success_rate'],
        'avg_response_time': result['avg_response_time'],
        'fastest_area': details.get('min_latency_area', 'N/A'),
        'slowest_area': details.get('max_latency_area', 'N/A')
    }

# 示例使用
if __name__ == "__main__":
    # 基础测试
    print("=== 基础测试 ===")
    result = test_domain("github.com")
    print(f"测试成功: {result['success']}")
    print(f"域名可用: {result['available']}")
    print(f"成功率: {result['success_rate']}%")
    print(f"平均响应时间: {result['avg_response_time']}ms")
    
    # 快速检查
    print("\n=== 快速检查 ===")
    is_available = quick_check("github.com")
    print(f"github.com 可用: {is_available}")
    
    # 性能指标
    print("\n=== 性能指标 ===")
    perf = get_domain_performance("github.com")
    print(f"最快地区: {perf['fastest_area']}")
    print(f"最慢地区: {perf['slowest_area']}")