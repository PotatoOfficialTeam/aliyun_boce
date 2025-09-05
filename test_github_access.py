#!/usr/bin/env python3
import requests
import os
import json
import base64
from dotenv import load_dotenv

load_dotenv()

token = os.environ.get("GITHUB_TOKEN")
repo_owner = "PotatoOfficialTeam"
repo_name = "domains"  # 修正名称

headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json"
}

# 测试仓库访问
print("测试仓库访问...")
url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
response = requests.get(url, headers=headers)

print(f"状态码: {response.status_code}")
if response.status_code == 200:
    repo_info = response.json()
    print(f"仓库名称: {repo_info['full_name']}")
    print(f"默认分支: {repo_info['default_branch']}")
    print(f"权限: {repo_info.get('permissions', 'N/A')}")
    print(f"私有仓库: {repo_info['private']}")
else:
    print(f"响应: {response.text}")

# 测试文件获取
print("\n测试文件获取...")
file_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/domains.json"
file_response = requests.get(file_url, headers=headers)
print(f"文件状态码: {file_response.status_code}")

if file_response.status_code == 200:
    file_info = file_response.json()
    print(f"文件SHA: {file_info['sha']}")
    print("文件获取成功")
    
    # 测试文件更新（模拟）
    print("\n测试文件更新权限...")
    test_content = {"test": "content"}
    encoded_content = base64.b64encode(json.dumps(test_content).encode('utf-8')).decode('ascii')
    
    update_data = {
        "message": "测试更新权限",
        "content": encoded_content,
        "sha": file_info["sha"]
    }
    
    # 只是测试权限，不实际提交
    print("模拟更新请求构建成功")
    print(f"需要的权限: Contents Write")
    
else:
    print(f"文件响应: {file_response.text}")

# 检查Token类型
print(f"\n检查Token信息...")
user_url = "https://api.github.com/user"
user_response = requests.get(user_url, headers=headers)
if user_response.status_code == 200:
    user_info = user_response.json()
    print(f"用户: {user_info['login']}")
    print(f"Token类型: Personal Access Token")
else:
    print("Token验证失败")