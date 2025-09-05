#!/usr/bin/env python3
"""
Caddy SSH管理API接口
提供简单易用的API接口
"""

import logging
from typing import Dict, List, Any

from .local_caddy_manager import LocalCaddyManager
from .config import config


def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def add_domain_to_caddy(domain: str, brand: str) -> Dict[str, Any]:
    """
    添加域名到Caddy配置（使用本地处理模式）
    
    Args:
        domain: 要添加的域名
        brand: 品牌名称 (wujie 或 v2word)
    
    Returns:
        操作结果字典
    
    Example:
        >>> result = add_domain_to_caddy("newapi.example.com", "wujie")
        >>> print(f"添加成功: {result['success']}")
    """
    try:
        # 验证品牌
        if brand.lower() not in config.get_supported_brands():
            return {
                'success': False,
                'domain': domain,
                'brand': brand,
                'error': f"不支持的品牌: {brand}，支持的品牌: {config.get_supported_brands()}"
            }
        
        # 验证SSH配置
        if not config.validate_ssh_config():
            return {
                'success': False,
                'domain': domain,
                'brand': brand,
                'error': "SSH配置不完整，请检查环境变量"
            }
        
        # 创建本地管理器并执行完整工作流程
        manager = LocalCaddyManager()
        workflow_result = manager.add_domain_complete_workflow(domain, brand)
        
        # 清理临时文件
        manager.cleanup_local_files()
        
        if workflow_result['success']:
            return {
                'success': True,
                'domain': domain,
                'brand': brand,
                'backup_path': workflow_result['backup_path'],
                'steps_completed': workflow_result['steps']
            }
        else:
            return {
                'success': False,
                'domain': domain,
                'brand': brand,
                'error': workflow_result['error'],
                'steps_completed': workflow_result['steps'],
                'backup_path': workflow_result.get('backup_path')
            }
        
    except Exception as e:
        return {
            'success': False,
            'domain': domain,
            'brand': brand,
            'error': str(e)
        }


def batch_add_domains(domains: List[str], brand: str) -> List[Dict[str, Any]]:
    """
    批量添加域名
    
    Args:
        domains: 域名列表
        brand: 品牌名称
    
    Returns:
        每个域名的操作结果列表
    
    Example:
        >>> domains = ["api1.example.com", "api2.example.com"]
        >>> results = batch_add_domains(domains, "wujie")
        >>> success_count = sum(1 for r in results if r['success'])
    """
    results = []
    
    for domain in domains:
        result = add_domain_to_caddy(domain, brand)
        results.append(result)
    
    return results


def test_connection() -> Dict[str, Any]:
    """
    测试SSH连接
    
    Returns:
        连接测试结果
    
    Example:
        >>> result = test_connection()
        >>> print(f"连接状态: {'正常' if result['success'] else '失败'}")
    """
    result = {
        'success': False,
        'error': None
    }
    
    try:
        if not config.validate_ssh_config():
            result['error'] = "SSH配置不完整"
            return result
        
        manager = LocalCaddyManager()
        success = manager.test_connection()
        
        result['success'] = success
        if not success:
            result['error'] = "SSH连接测试失败"
        
        return result
        
    except Exception as e:
        result['error'] = str(e)
        return result


def get_caddy_config() -> Dict[str, Any]:
    """
    获取当前Caddy配置（下载到本地）
    
    Returns:
        配置内容和操作结果
    
    Example:
        >>> result = get_caddy_config()
        >>> if result['success']:
        >>>     print(result['config'])
    """
    result = {
        'success': False,
        'config': None,
        'local_path': None,
        'error': None
    }
    
    try:
        if not config.validate_ssh_config():
            result['error'] = "SSH配置不完整"
            return result
        
        manager = LocalCaddyManager()
        
        # 下载配置到本地
        if not manager.download_config():
            result['error'] = "下载配置失败"
            return result
        
        # 读取本地配置
        with open(manager.local_caddy_path, 'r', encoding='utf-8') as f:
            config_content = f.read()
        
        result['success'] = True
        result['config'] = config_content
        result['local_path'] = str(manager.local_caddy_path)
        
        return result
        
    except Exception as e:
        result['error'] = str(e)
        return result


def get_system_info() -> Dict[str, Any]:
    """
    获取系统信息
    
    Returns:
        系统信息字典
    
    Example:
        >>> info = get_system_info()
        >>> print(f"支持的品牌: {info['supported_brands']}")
    """
    ssh_config = config.get_ssh_config()
    
    return {
        'supported_brands': config.get_supported_brands(),
        'ssh_host': ssh_config.get('host'),
        'ssh_port': ssh_config.get('port'),
        'ssh_configured': config.validate_ssh_config(),
        'caddy_file_path': config.get_caddy_config()['file_path']
    }


# 简化的便捷函数
def quick_add_domain(domain: str, brand: str) -> bool:
    """
    快速添加域名（简化接口）
    
    Args:
        domain: 域名
        brand: 品牌
    
    Returns:
        是否成功
    """
    result = add_domain_to_caddy(domain, brand)
    return result['success']


def quick_test_connection() -> bool:
    """
    快速测试连接（简化接口）
    
    Returns:
        连接是否正常
    """
    result = test_connection()
    return result['success']