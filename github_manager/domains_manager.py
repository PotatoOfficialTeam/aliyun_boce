#!/usr/bin/env python3
"""
GitHub domains.json 管理器
负责读取、修改和提交 domains.json 文件到 GitHub
"""

import json
import subprocess
import logging
from datetime import date
from pathlib import Path
from typing import Dict, List

class DomainsManager:
    """domains.json 文件管理器"""
    
    def __init__(self, domains_file_path: str, git_repo_path: str | None = None):
        """
        初始化管理器
        
        Args:
            domains_file_path: domains.json 文件的绝对路径
            git_repo_path: Git仓库路径，如果为None则使用domains_file_path的父目录
        """
        self.domains_file_path = Path(domains_file_path)
        self.git_repo_path = Path(git_repo_path) if git_repo_path else self.domains_file_path.parent
        
        # 设置日志
        self.logger = logging.getLogger("domains_manager")
        
        # 验证文件是否存在
        if not self.domains_file_path.exists():
            raise FileNotFoundError(f"domains.json 文件不存在: {self.domains_file_path}")
    
    def load_domains(self) -> Dict:
        """加载 domains.json 文件内容"""
        try:
            with open(self.domains_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.logger.info(f"成功加载 domains.json: {self.domains_file_path}")
            return data
        except Exception as e:
            self.logger.error(f"加载 domains.json 失败: {e}")
            raise
    
    def save_domains(self, data: Dict) -> bool:
        """保存数据到 domains.json 文件"""
        try:
            with open(self.domains_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            self.logger.info(f"成功保存 domains.json: {self.domains_file_path}")
            return True
        except Exception as e:
            self.logger.error(f"保存 domains.json 失败: {e}")
            return False
    
    def add_domain_to_brand(self, brand: str, new_domain: str, description: str = "") -> bool:
        """
        在指定品牌的域名列表开头添加新域名
        
        Args:
            brand: 品牌名称 (如 "wujie", "v2word")
            new_domain: 新域名URL
            description: 域名描述
            
        Returns:
            bool: 是否添加成功
        """
        try:
            # 加载当前数据
            data = self.load_domains()
            
            # 检查 panels 部分是否存在
            if "panels" not in data:
                data["panels"] = {}
            
            # 检查品牌是否存在
            if brand not in data["panels"]:
                data["panels"][brand] = []
            
            # 创建新的域名条目
            new_domain_entry = {
                "url": new_domain,
                "description": description or f"自动生成的域名 - {brand}"
            }
            
            # 在列表开头插入新域名（这样新域名会被优先测试）
            data["panels"][brand].insert(0, new_domain_entry)
            
            # 保存文件
            if self.save_domains(data):
                self.logger.info(f"成功添加域名到品牌 {brand}: {new_domain}")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"添加域名失败 {brand}: {new_domain}, 错误: {e}")
            return False
    
    def replace_first_domain_of_brand(self, brand: str, new_domain: str, description: str = "") -> bool:
        """
        替换指定品牌的第一个域名
        
        Args:
            brand: 品牌名称 (如 "wujie", "v2word")
            new_domain: 新域名URL
            description: 域名描述
            
        Returns:
            bool: 是否替换成功
        """
        try:
            # 加载当前数据
            data = self.load_domains()
            
            # 检查 panels 部分是否存在
            if "panels" not in data:
                data["panels"] = {}
            
            # 检查品牌是否存在
            if brand not in data["panels"]:
                data["panels"][brand] = []
            
            # 创建新的域名条目
            new_domain_entry = {
                "url": new_domain,
                "description": description or f"自动生成的域名 - {brand}"
            }
            
            # 记录被替换的域名
            old_domain = None
            if len(data["panels"][brand]) > 0:
                old_domain = data["panels"][brand][0].get("url", "N/A")
            
            # 替换第一个域名（如果列表为空则添加）
            if len(data["panels"][brand]) == 0:
                data["panels"][brand].append(new_domain_entry)
                self.logger.info(f"品牌 {brand} 列表为空，添加新域名: {new_domain}")
            else:
                data["panels"][brand][0] = new_domain_entry
                self.logger.info(f"品牌 {brand} 第一个域名已替换: {old_domain} -> {new_domain}")
            
            # 保存文件
            if self.save_domains(data):
                self.logger.info(f"成功替换品牌 {brand} 的第一个域名: {new_domain}")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"替换域名失败 {brand}: {new_domain}, 错误: {e}")
            return False
    
    def get_brand_domains(self, brand: str) -> List[Dict]:
        """获取指定品牌的所有域名"""
        try:
            data = self.load_domains()
            return data.get("panels", {}).get(brand, [])
        except Exception as e:
            self.logger.error(f"获取品牌域名失败 {brand}: {e}")
            return []
    
    def remove_domain_from_brand(self, brand: str, domain_url: str) -> bool:
        """从指定品牌移除域名"""
        try:
            data = self.load_domains()
            
            if "panels" not in data or brand not in data["panels"]:
                self.logger.warning(f"品牌 {brand} 不存在")
                return False
            
            # 查找并移除匹配的域名
            original_count = len(data["panels"][brand])
            data["panels"][brand] = [
                domain for domain in data["panels"][brand] 
                if domain.get("url") != domain_url
            ]
            
            removed_count = original_count - len(data["panels"][brand])
            
            if removed_count > 0:
                if self.save_domains(data):
                    self.logger.info(f"从品牌 {brand} 移除了 {removed_count} 个域名: {domain_url}")
                    return True
            else:
                self.logger.warning(f"在品牌 {brand} 中未找到域名: {domain_url}")
            
            return False
            
        except Exception as e:
            self.logger.error(f"移除域名失败 {brand}: {domain_url}, 错误: {e}")
            return False

class GitManager:
    """Git 操作管理器"""
    
    def __init__(self, repo_path: str):
        """
        初始化Git管理器
        
        Args:
            repo_path: Git仓库路径
        """
        self.repo_path = Path(repo_path)
        self.logger = logging.getLogger("git_manager")
        
        # 验证是否为Git仓库
        if not (self.repo_path / ".git").exists():
            raise ValueError(f"不是有效的Git仓库: {repo_path}")
    
    def _run_git_command(self, command: List[str]) -> tuple:
        """
        执行Git命令
        
        Returns:
            tuple: (success: bool, output: str, error: str)
        """
        try:
            result = subprocess.run(
                ["git"] + command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            success = result.returncode == 0
            return success, result.stdout.strip(), result.stderr.strip()
            
        except subprocess.TimeoutExpired:
            return False, "", "Git命令执行超时"
        except Exception as e:
            return False, "", str(e)
    
    def get_status(self) -> Dict:
        """获取Git状态"""
        success, output, error = self._run_git_command(["status", "--porcelain"])
        
        if success:
            return {
                "has_changes": bool(output),
                "changes": output.split('\n') if output else []
            }
        else:
            self.logger.error(f"获取Git状态失败: {error}")
            return {"has_changes": False, "changes": []}
    
    def add_file(self, file_path: str) -> bool:
        """添加文件到Git暂存区"""
        success, _, error = self._run_git_command(["add", file_path])
        
        if success:
            self.logger.info(f"文件已添加到暂存区: {file_path}")
            return True
        else:
            self.logger.error(f"添加文件失败: {error}")
            return False
    
    def commit(self, message: str, author_name: str = None, author_email: str = None) -> bool:
        """提交更改"""
        commit_args = ["commit", "-m", message]
        
        # 设置作者信息
        if author_name and author_email:
            commit_args.extend(["--author", f"{author_name} <{author_email}>"])
        
        success, _, error = self._run_git_command(commit_args)
        
        if success:
            self.logger.info(f"提交成功: {message}")
            return True
        else:
            self.logger.error(f"提交失败: {error}")
            return False
    
    def push(self, remote: str = "origin", branch: str = "main") -> bool:
        """推送到远程仓库"""
        success, _, error = self._run_git_command(["push", remote, branch])
        
        if success:
            self.logger.info(f"推送成功到 {remote}/{branch}")
            return True
        else:
            self.logger.error(f"推送失败: {error}")
            return False
    
    def pull(self, remote: str = "origin", branch: str = "main") -> bool:
        """从远程仓库拉取更新"""
        success, _, error = self._run_git_command(["pull", remote, branch])
        
        if success:
            self.logger.info(f"拉取成功从 {remote}/{branch}")
            return True
        else:
            self.logger.error(f"拉取失败: {error}")
            return False

class GitHubManager:
    """GitHub管理器 - 整合domains.json管理和Git操作"""
    
    def __init__(self, domains_file_path: str, git_repo_path: str = None):
        """
        初始化GitHub管理器
        
        Args:
            domains_file_path: domains.json文件路径
            git_repo_path: Git仓库路径
        """
        self.domains_manager = DomainsManager(domains_file_path, git_repo_path)
        self.git_manager = GitManager(str(git_repo_path or Path(domains_file_path).parent))
        self.logger = logging.getLogger("github_manager")
    
    def add_domain_and_commit(self, brand: str, new_domain: str, description: str = "") -> bool:
        """
        添加新域名并提交到GitHub
        
        Args:
            brand: 品牌名称
            new_domain: 新域名
            description: 描述
            
        Returns:
            bool: 是否成功
        """
        try:
            # 1. 先拉取最新代码，避免冲突
            if not self.git_manager.pull():
                self.logger.warning("拉取最新代码失败，继续执行...")
            
            # 2. 添加域名到JSON文件
            if not self.domains_manager.add_domain_to_brand(brand, new_domain, description):
                return False
            
            # 3. 检查是否有更改
            status = self.git_manager.get_status()
            if not status["has_changes"]:
                self.logger.info("没有检测到文件更改")
                return True
            
            # 4. 添加文件到暂存区
            relative_path = self.domains_manager.domains_file_path.name
            if not self.git_manager.add_file(relative_path):
                return False
            
            # 5. 生成提交消息
            today = date.today().strftime("%Y-%m-%d")
            commit_message = f"自动添加{brand}品牌域名: {new_domain} ({today})"
            
            # 6. 提交更改
            if not self.git_manager.commit(
                commit_message,
                author_name="Domain Monitor Bot",
                author_email="noreply@domain-monitor.com"
            ):
                return False
            
            # 7. 推送到远程仓库
            if not self.git_manager.push():
                return False
            
            self.logger.info(f"成功添加域名并推送到GitHub: {brand} -> {new_domain}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加域名并提交失败: {e}")
            return False
    
    def replace_first_domain_and_commit(self, brand: str, new_domain: str, description: str = "") -> bool:
        """
        替换品牌第一个域名并提交到GitHub
        
        Args:
            brand: 品牌名称
            new_domain: 新域名
            description: 描述
            
        Returns:
            bool: 是否成功
        """
        try:
            # 1. 先拉取最新代码，避免冲突
            if not self.git_manager.pull():
                self.logger.warning("拉取最新代码失败，继续执行...")
            
            # 2. 替换品牌第一个域名
            if not self.domains_manager.replace_first_domain_of_brand(brand, new_domain, description):
                return False
            
            # 3. 检查是否有更改
            status = self.git_manager.get_status()
            if not status["has_changes"]:
                self.logger.info("没有检测到文件更改")
                return True
            
            # 4. 添加文件到暂存区
            relative_path = self.domains_manager.domains_file_path.name
            if not self.git_manager.add_file(relative_path):
                return False
            
            # 5. 生成提交消息
            today = date.today().strftime("%Y-%m-%d")
            commit_message = f"自动替换{brand}品牌主域名: {new_domain} ({today})"
            
            # 6. 提交更改
            if not self.git_manager.commit(
                commit_message,
                author_name="Domain Monitor Bot",
                author_email="noreply@domain-monitor.com"
            ):
                return False
            
            # 7. 推送到远程仓库
            if not self.git_manager.push():
                return False
            
            self.logger.info(f"成功替换域名并推送到GitHub: {brand} -> {new_domain}")
            return True
            
        except Exception as e:
            self.logger.error(f"替换域名并提交失败: {e}")
            return False
    
    def get_brand_domains(self, brand: str) -> List[Dict]:
        """获取指定品牌的域名列表"""
        return self.domains_manager.get_brand_domains(brand)
    
    def sync_from_remote(self) -> bool:
        """从远程同步最新的domains.json"""
        return self.git_manager.pull()