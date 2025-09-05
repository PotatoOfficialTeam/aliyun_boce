#!/usr/bin/env python3
"""
本地Caddy配置管理器
先下载配置到本地，修改后再上传
"""

import os
import logging
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from .ssh_client import SSHClient
from .caddy_config_parser import CaddyConfigParser
from .config import config


class LocalCaddyManager:
    """本地Caddy配置管理器"""
    
    def __init__(self, work_dir: Optional[str] = None):
        """
        初始化本地管理器
        
        Args:
            work_dir: 本地工作目录，默认使用临时目录
        """
        # SSH配置
        ssh_config = config.get_ssh_config()
        if not config.validate_ssh_config():
            raise ValueError("SSH配置不完整，请检查环境变量")
        
        self.ssh = SSHClient(
            ssh_config['host'],
            ssh_config['port'], 
            ssh_config['username'],
            ssh_config['password']
        )
        
        # 本地工作目录
        if work_dir:
            self.work_dir = Path(work_dir)
        else:
            self.work_dir = Path(tempfile.gettempdir()) / "caddy_manager"
        
        self.work_dir.mkdir(parents=True, exist_ok=True)
        
        # 远程配置文件路径
        self.remote_caddy_path = "/etc/caddy/Caddyfile"
        
        # 本地文件路径
        self.local_caddy_path = self.work_dir / "Caddyfile"
        self.modified_caddy_path = self.work_dir / "Caddyfile.modified"
        
        # 品牌配置
        self.brand_configs = config.brand_configs
        
        self.logger = self._setup_logging()
        
        self.logger.info(f"本地工作目录: {self.work_dir}")
    
    def _setup_logging(self):
        """设置日志"""
        logger = logging.getLogger("local_caddy_manager")
        logger.setLevel(logging.INFO)
        
        if not logger.hasHandlers():
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def download_config(self) -> bool:
        """
        从远程服务器下载配置文件到本地
        
        Returns:
            是否下载成功
        """
        try:
            self.logger.info("从远程服务器下载配置文件...")
            
            # 获取远程配置内容
            stdout, stderr, exit_code = self.ssh.execute_command(f"cat {self.remote_caddy_path}")
            
            if exit_code != 0:
                self.logger.error(f"下载配置失败: {stderr}")
                return False
            
            # 保存到本地
            with open(self.local_caddy_path, 'w', encoding='utf-8') as f:
                f.write(stdout)
            
            self.logger.info(f"配置已下载到: {self.local_caddy_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"下载配置时出错: {e}")
            return False
    
    def add_domain_to_local_config(self, domain: str, brand: str) -> bool:
        """
        在本地配置文件中添加域名
        
        Args:
            domain: 要添加的域名
            brand: 品牌名称
            
        Returns:
            是否修改成功
        """
        try:
            brand = brand.lower()
            if brand not in self.brand_configs:
                raise ValueError(f"不支持的品牌: {brand}")
            
            self.logger.info(f"在本地配置中为品牌 {brand} 添加域名: {domain}")
            
            # 检查本地原始配置文件是否存在
            if not self.local_caddy_path.exists():
                self.logger.error("本地配置文件不存在，请先下载配置")
                return False
            
            # 读取本地配置
            with open(self.local_caddy_path, 'r', encoding='utf-8') as f:
                config_content = f.read()
            
            # 使用解析器修改配置
            parser = CaddyConfigParser(config_content)
            success, result = parser.add_domain_to_brand_block(domain, brand)
            
            if not success:
                self.logger.error(f"修改配置失败: {result}")
                return False
            
            if "已存在" in result:
                self.logger.warning(result)
                return True
            
            # 验证新配置语法
            new_parser = CaddyConfigParser(result)
            valid, msg = new_parser.validate_config_syntax()
            if not valid:
                self.logger.error(f"新配置语法错误: {msg}")
                return False
            
            # 保存修改后的配置
            with open(self.modified_caddy_path, 'w', encoding='utf-8') as f:
                f.write(result)
            
            self.logger.info(f"修改后的配置已保存到: {self.modified_caddy_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"修改本地配置时出错: {e}")
            return False
    
    def backup_remote_config(self) -> Optional[str]:
        """
        备份远程配置文件
        
        Returns:
            备份文件路径，失败返回None
        """
        try:
            # 生成备份文件名：Caddyfile.bak.年月日时间
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            backup_path = f"{self.remote_caddy_path}.bak.{timestamp}"
            
            self.logger.info(f"备份远程配置到: {backup_path}")
            
            # 执行备份命令
            stdout, stderr, exit_code = self.ssh.execute_command(
                f"cp {self.remote_caddy_path} {backup_path}"
            )
            
            if exit_code != 0:
                self.logger.error(f"备份失败: {stderr}")
                return None
            
            self.logger.info("远程配置备份成功")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"备份远程配置时出错: {e}")
            return None
    
    def upload_config(self) -> bool:
        """
        上传修改后的配置文件到远程服务器
        
        Returns:
            是否上传成功
        """
        try:
            # 检查修改后的配置文件是否存在
            if not self.modified_caddy_path.exists():
                self.logger.error("修改后的配置文件不存在")
                return False
            
            self.logger.info("上传修改后的配置到远程服务器...")
            
            # 读取修改后的配置内容
            with open(self.modified_caddy_path, 'r', encoding='utf-8') as f:
                config_content = f.read()
            
            # 转义配置内容中的特殊字符
            escaped_config = config_content.replace("'", "'\"'\"'")
            
            # 上传配置
            command = f"echo '{escaped_config}' > {self.remote_caddy_path}"
            stdout, stderr, exit_code = self.ssh.execute_command(command)
            
            if exit_code != 0:
                self.logger.error(f"上传配置失败: {stderr}")
                return False
            
            self.logger.info("配置上传成功")
            return True
            
        except Exception as e:
            self.logger.error(f"上传配置时出错: {e}")
            return False
    
    def validate_remote_config(self) -> bool:
        """
        验证远程配置文件语法
        
        Returns:
            配置是否有效
        """
        try:
            self.logger.info("验证远程配置语法...")
            
            stdout, stderr, exit_code = self.ssh.execute_command(
                f"caddy validate --config {self.remote_caddy_path}"
            )
            
            if exit_code != 0:
                self.logger.error(f"配置验证失败: {stderr}")
                return False
            
            self.logger.info("远程配置验证通过")
            return True
            
        except Exception as e:
            self.logger.error(f"验证配置时出错: {e}")
            return False
    
    def reload_caddy(self) -> bool:
        """
        重载Caddy服务
        
        Returns:
            是否重载成功
        """
        try:
            self.logger.info("重载Caddy服务...")
            
            stdout, stderr, exit_code = self.ssh.execute_command("systemctl reload caddy")
            
            if exit_code != 0:
                self.logger.error(f"Caddy重载失败: {stderr}")
                return False
            
            self.logger.info("Caddy服务重载成功")
            return True
            
        except Exception as e:
            self.logger.error(f"重载Caddy时出错: {e}")
            return False
    
    def add_domain_complete_workflow(self, domain: str, brand: str) -> Dict:
        """
        完整的域名添加工作流程
        1. 下载配置到本地
        2. 在本地修改配置
        3. 备份远程配置  
        4. 上传新配置
        5. 验证配置
        6. 重载服务
        
        Args:
            domain: 要添加的域名
            brand: 品牌名称
            
        Returns:
            操作结果字典
        """
        result = {
            'success': False,
            'domain': domain,
            'brand': brand,
            'steps': {
                'download': False,
                'modify': False,
                'backup': False,
                'upload': False,
                'validate': False,
                'reload': False
            },
            'backup_path': None,
            'error': None
        }
        
        try:
            # 1. 下载配置
            if not self.download_config():
                result['error'] = "下载配置失败"
                return result
            result['steps']['download'] = True
            
            # 2. 修改本地配置
            if not self.add_domain_to_local_config(domain, brand):
                result['error'] = "修改本地配置失败"
                return result
            result['steps']['modify'] = True
            
            # 3. 备份远程配置
            backup_path = self.backup_remote_config()
            if not backup_path:
                result['error'] = "备份远程配置失败"
                return result
            result['steps']['backup'] = True
            result['backup_path'] = backup_path
            
            # 4. 上传新配置
            if not self.upload_config():
                result['error'] = "上传配置失败"
                return result
            result['steps']['upload'] = True
            
            # 5. 验证配置
            if not self.validate_remote_config():
                result['error'] = "配置验证失败"
                return result
            result['steps']['validate'] = True
            
            # 6. 重载服务
            if not self.reload_caddy():
                result['error'] = "重载服务失败"
                return result
            result['steps']['reload'] = True
            
            result['success'] = True
            self.logger.info(f"域名 {domain} 成功添加到品牌 {brand}")
            
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"完整工作流程失败: {e}")
        
        return result
    
    def test_connection(self) -> bool:
        """测试SSH连接"""
        return self.ssh.test_connection()
    
    def cleanup_local_files(self):
        """清理本地临时文件"""
        try:
            if self.local_caddy_path.exists():
                self.local_caddy_path.unlink()
            if self.modified_caddy_path.exists():
                self.modified_caddy_path.unlink()
            self.logger.info("本地临时文件已清理")
        except Exception as e:
            self.logger.warning(f"清理本地文件时出错: {e}")
    
    def get_work_dir(self) -> Path:
        """获取工作目录路径"""
        return self.work_dir