# GitHub Domains Manager

负责管理 domains.json 文件的读取、修改和 Git 操作的模块。

## 功能特性

- 🔧 **JSON管理**: 读取、修改、保存 domains.json 文件
- 📝 **智能替换**: 替换品牌第一个域名为新域名（立即生效）
- 🗑️ **域名移除**: 从品牌中移除指定域名
- 🔄 **Git集成**: 自动提交和推送到GitHub
- 🔍 **状态检查**: 检查Git仓库状态和更改
- 🚀 **同步功能**: 从远程拉取最新更改

## 核心类

### DomainsManager
管理 domains.json 文件的读写操作：
- `load_domains()` - 加载JSON数据
- `save_domains(data)` - 保存JSON数据
- `add_domain_to_brand(brand, url, desc)` - 添加域名到品牌
- `get_brand_domains(brand)` - 获取品牌域名列表
- `remove_domain_from_brand(brand, url)` - 移除域名

### GitManager  
处理Git相关操作：
- `get_status()` - 获取仓库状态
- `add_file(path)` - 添加文件到暂存区
- `commit(message)` - 提交更改
- `push()` - 推送到远程
- `pull()` - 拉取远程更改

### GitHubManager
整合上述功能的高级接口：
- `add_domain_and_commit(brand, domain, desc)` - 一键添加域名并推送
- `get_brand_domains(brand)` - 获取域名列表
- `sync_from_remote()` - 同步远程更改

## 使用示例

```python
from domains_manager import GitHubManager

# 初始化管理器
manager = GitHubManager(
    domains_file_path="/path/to/domains.json",
    git_repo_path="/path/to/git/repo"
)

# 添加新域名并自动提交推送
success = manager.add_domain_and_commit(
    brand="wujie",
    new_domain="https://apiwj250905.wj0001.cfd", 
    description="自动生成的备用域名"
)

if success:
    print("域名添加并推送成功！")

# 获取品牌域名列表
domains = manager.get_brand_domains("wujie")
print(f"wujie品牌有 {len(domains)} 个域名")
```

## 工作流程

1. **拉取最新代码** - 避免合并冲突
2. **修改JSON文件** - 在指定品牌列表开头添加新域名  
3. **检查文件更改** - 确认有实际修改
4. **添加到暂存区** - git add
5. **提交更改** - git commit（自动生成提交消息）
6. **推送到远程** - git push

## 提交消息格式

```
自动添加{brand}品牌域名: {domain_url} (2025-09-05)
```

## 错误处理

- 文件不存在时抛出异常
- Git操作失败时记录错误日志
- 网络问题时返回失败状态
- 自动跳过无更改的操作

## 日志记录

使用Python logging模块记录：
- 成功操作的信息日志
- 失败操作的错误日志  
- Git命令执行状态
- 文件操作结果