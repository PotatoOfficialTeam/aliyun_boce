#!/usr/bin/env python3
"""
GitHub API 直接提交管理器
通过GitHub API直接提交文件，不依赖本地Git
"""

import json
import base64
import logging
import requests
from datetime import date
from pathlib import Path
from typing import Dict, Optional

class GitHubAPIManager:
    """通过GitHub API直接管理仓库文件"""
    
    def __init__(self, token: str, repo_owner: str, repo_name: str, branch: str = "main"):
        """
        初始化GitHub API管理器
        
        Args:
            token: GitHub Personal Access Token
            repo_owner: 仓库所有者
            repo_name: 仓库名称
            branch: 分支名称
        """
        self.token = token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.branch = branch
        self.base_url = "https://api.github.com"
        
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        
        self.logger = logging.getLogger("github_api")
        
        # 验证token和仓库访问权限
        self._verify_access()
    
    def _verify_access(self):
        """验证GitHub访问权限"""
        try:
            url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}"
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                repo_info = response.json()
                self.logger.info(f"成功连接到GitHub仓库: {repo_info['full_name']}")
            elif response.status_code == 404:
                self.logger.error("仓库不存在或无访问权限")
                raise Exception("仓库不存在或无访问权限")
            else:
                self.logger.error(f"验证访问权限失败: {response.status_code}")
                raise Exception(f"访问验证失败: {response.text}")
                
        except Exception as e:
            self.logger.error(f"GitHub访问验证失败: {e}")
            raise
    
    def get_file_content(self, file_path: str) -> Optional[Dict]:
        """
        获取文件内容和SHA
        
        Args:
            file_path: 文件路径（相对于仓库根目录）
            
        Returns:
            dict: 包含content和sha的字典，文件不存在返回None
        """
        try:
            url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/contents/{file_path}"
            params = {"ref": self.branch}
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                file_info = response.json()
                # 解码base64内容
                content = base64.b64decode(file_info["content"]).decode('utf-8')
                return {
                    "content": content,
                    "sha": file_info["sha"]
                }
            elif response.status_code == 404:
                # 文件不存在
                return None
            else:
                self.logger.error(f"获取文件失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"获取文件内容失败: {e}")
            return None
    
    def update_file(self, file_path: str, content: str, commit_message: str, 
                   author_name: str = "Domain Monitor Bot", 
                   author_email: str = "noreply@domain-monitor.com") -> bool:
        """
        创建或更新文件
        
        Args:
            file_path: 文件路径
            content: 文件内容
            commit_message: 提交消息
            author_name: 作者名称
            author_email: 作者邮箱
            
        Returns:
            bool: 是否成功
        """
        try:
            url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/contents/{file_path}"
            
            # 获取现有文件的SHA（如果存在）
            existing_file = self.get_file_content(file_path)
            
            # 编码内容为base64
            encoded_content = base64.b64encode(content.encode('utf-8')).decode('ascii')
            
            # 构建请求数据
            data = {
                "message": commit_message,
                "content": encoded_content,
                "branch": self.branch,
                "author": {
                    "name": author_name,
                    "email": author_email
                }
            }
            
            # 如果文件已存在，需要提供SHA
            if existing_file:
                data["sha"] = existing_file["sha"]
                action = "更新"
            else:
                action = "创建"
            
            response = requests.put(url, headers=self.headers, json=data, timeout=30)
            
            if response.status_code in [200, 201]:
                commit_info = response.json()
                commit_sha = commit_info["commit"]["sha"]
                self.logger.info(f"成功{action}文件 {file_path}, 提交SHA: {commit_sha[:8]}")
                return True
            else:
                self.logger.error(f"{action}文件失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"更新文件失败: {e}")
            return False

class DomainsGitHubManager:
    """domains.json的GitHub管理器"""
    
    def __init__(self, domains_file_path: str, github_token: str, 
                 repo_owner: str = "PotatoOfficialTeam", 
                 repo_name: str = "domians", 
                 target_file_path: str = "domains.json"):
        """
        初始化管理器
        
        Args:
            domains_file_path: 本地domains.json文件路径
            github_token: GitHub访问令牌
            repo_owner: 仓库所有者
            repo_name: 仓库名称
            target_file_path: 目标文件路径（在仓库中的路径）
        """
        self.domains_file_path = Path(domains_file_path)
        self.target_file_path = target_file_path
        self.github_api = GitHubAPIManager(github_token, repo_owner, repo_name)
        self.logger = logging.getLogger("domains_github")
        
        if not self.domains_file_path.exists():
            raise FileNotFoundError(f"本地domains.json文件不存在: {domains_file_path}")
    
    def load_local_domains(self) -> Dict:
        """加载本地domains.json内容"""
        try:
            with open(self.domains_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"加载本地domains.json失败: {e}")
            raise
    
    def save_local_domains(self, data: Dict) -> bool:
        """保存数据到本地domains.json"""
        try:
            with open(self.domains_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            self.logger.error(f"保存本地domains.json失败: {e}")
            return False
    
    def replace_first_domain_of_brand(self, brand: str, new_domain: str, description: str = "") -> bool:
        """替换指定品牌的第一个域名"""
        try:
            data = self.load_local_domains()
            
            if "panels" not in data:
                data["panels"] = {}
            
            if brand not in data["panels"]:
                data["panels"][brand] = []
            
            new_domain_entry = {
                "url": new_domain,
                "description": description or f"自动生成的域名 - {brand}"
            }
            
            # 记录被替换的域名
            old_domain = None
            if len(data["panels"][brand]) > 0:
                old_domain = data["panels"][brand][0].get("url", "N/A")
            
            # 替换第一个域名
            if len(data["panels"][brand]) == 0:
                data["panels"][brand].append(new_domain_entry)
                self.logger.info(f"品牌 {brand} 列表为空，添加新域名: {new_domain}")
            else:
                data["panels"][brand][0] = new_domain_entry
                self.logger.info(f"品牌 {brand} 第一个域名已替换: {old_domain} -> {new_domain}")
            
            # 保存到本地文件
            return self.save_local_domains(data)
            
        except Exception as e:
            self.logger.error(f"替换域名失败: {e}")
            return False
    
    def commit_to_github(self, commit_message: str = None) -> bool:
        """将本地domains.json提交到GitHub"""
        try:
            # 加载本地文件内容
            data = self.load_local_domains()
            content = json.dumps(data, ensure_ascii=False, indent=4)
            
            # 生成提交消息
            if not commit_message:
                today = date.today().strftime("%Y-%m-%d")
                commit_message = f"自动更新域名配置 ({today})"
            
            # 提交到GitHub
            success = self.github_api.update_file(
                file_path=self.target_file_path,
                content=content,
                commit_message=commit_message
            )
            
            if success:
                self.logger.info(f"成功提交domains.json到GitHub")
                return True
            else:
                self.logger.error("提交到GitHub失败")
                return False
                
        except Exception as e:
            self.logger.error(f"提交到GitHub失败: {e}")
            return False
    
    def replace_and_commit(self, brand: str, new_domain: str, description: str = "") -> bool:
        """替换域名并提交到GitHub（一站式操作）"""
        try:
            # 1. 替换本地域名
            if not self.replace_first_domain_of_brand(brand, new_domain, description):
                return False
            
            # 2. 生成提交消息
            today = date.today().strftime("%Y-%m-%d")
            commit_message = f"自动替换{brand}品牌主域名: {new_domain} ({today})"
            
            # 3. 提交到GitHub
            if not self.commit_to_github(commit_message):
                return False
            
            self.logger.info(f"成功替换并提交域名: {brand} -> {new_domain}")
            return True
            
        except Exception as e:
            self.logger.error(f"替换并提交域名失败: {e}")
            return False