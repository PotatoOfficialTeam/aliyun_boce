#!/usr/bin/env python3
"""
配置文件
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """配置管理类"""
    
    def __init__(self):
        """初始化配置"""
        self.ssh_config = self._load_ssh_config()
        self.brand_configs = self._load_brand_configs()
        self.caddy_config = self._load_caddy_config()
    
    def _load_ssh_config(self) -> Dict[str, Any]:
        """加载SSH配置"""
        return {
            'host': os.environ.get("CADDY_IP"),
            'port': int(os.environ.get("CADDY_PORT", 22)),
            'username': os.environ.get("CADDY_USER"),
            'password': os.environ.get("CADDY_PASSWD")
        }
    
    def _load_brand_configs(self) -> Dict[str, Dict[str, str]]:
        """加载品牌配置"""
        return {
            "wujie": {
                "target_host": "wujie.one",
                "log_file": "/var/log/caddy/wujie.log"
            },
            "v2word": {
                "target_host": "v2word.art", 
                "log_file": "/var/log/caddy/v2word.log"
            }
        }
    
    def _load_caddy_config(self) -> Dict[str, str]:
        """加载Caddy配置"""
        return {
            'file_path': '/etc/caddy/Caddyfile'
        }
    
    def get_ssh_config(self) -> Dict[str, Any]:
        """获取SSH配置"""
        return self.ssh_config
    
    def get_brand_config(self, brand: str) -> Dict[str, str]:
        """获取品牌配置"""
        return self.brand_configs.get(brand.lower(), {})
    
    def get_caddy_config(self) -> Dict[str, str]:
        """获取Caddy配置"""
        return self.caddy_config
    
    def get_supported_brands(self) -> list:
        """获取支持的品牌列表"""
        return list(self.brand_configs.keys())
    
    def validate_ssh_config(self) -> bool:
        """验证SSH配置完整性"""
        required_keys = ['host', 'username', 'password']
        return all(self.ssh_config.get(key) for key in required_keys)


# 全局配置实例
config = Config()