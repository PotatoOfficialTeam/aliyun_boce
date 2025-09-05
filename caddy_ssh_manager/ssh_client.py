#!/usr/bin/env python3
"""
SSH客户端基础类
"""

import paramiko
import logging
from typing import Tuple


class SSHClient:
    """SSH客户端封装"""
    
    def __init__(self, host: str, port: int, username: str, password: str):
        """
        初始化SSH客户端
        
        Args:
            host: 服务器地址
            port: SSH端口
            username: 用户名
            password: 密码
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def create_connection(self) -> paramiko.SSHClient:
        """创建SSH连接"""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=10
            )
            return client
        except Exception as e:
            self.logger.error(f"SSH连接失败: {e}")
            raise
    
    def execute_command(self, command: str) -> Tuple[str, str, int]:
        """
        执行SSH命令
        
        Args:
            command: 要执行的命令
            
        Returns:
            Tuple[stdout, stderr, exit_code]
        """
        with self.create_connection() as client:
            stdin, stdout, stderr = client.exec_command(command)
            
            stdout_content = stdout.read().decode('utf-8')
            stderr_content = stderr.read().decode('utf-8')
            exit_code = stdout.channel.recv_exit_status()
            
            return stdout_content, stderr_content, exit_code
    
    def test_connection(self) -> bool:
        """测试SSH连接"""
        try:
            self.logger.info(f"测试SSH连接到 {self.host}:{self.port}")
            
            stdout, stderr, exit_code = self.execute_command("echo 'SSH连接测试成功'")
            
            if exit_code == 0:
                self.logger.info("SSH连接测试成功")
                return True
            else:
                self.logger.error(f"SSH连接测试失败: {stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"SSH连接测试异常: {e}")
            return False