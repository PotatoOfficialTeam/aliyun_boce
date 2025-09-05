"""
Caddy SSH管理模块
通过SSH管理远程Caddy服务器配置
"""

from .local_caddy_manager import LocalCaddyManager
from .ssh_client import SSHClient
from .api import (
    add_domain_to_caddy,
    batch_add_domains, 
    test_connection,
    get_caddy_config,
    get_system_info,
    quick_add_domain,
    quick_test_connection
)

__all__ = [
    'LocalCaddyManager',
    'SSHClient', 
    'add_domain_to_caddy',
    'batch_add_domains',
    'test_connection',
    'get_caddy_config',
    'get_system_info',
    'quick_add_domain',
    'quick_test_connection'
]

__version__ = '1.0.0'