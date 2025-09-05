# 域名拨测系统

自动从GitHub仓库获取域名配置并进行可访问性拨测的系统。

## 功能特性

- 🔄 **自动同步**：从GitHub仓库自动获取最新的域名配置
- 🧪 **智能拨测**：使用阿里云拨测服务检测域名可访问性
- 📊 **品牌管理**：支持多品牌域名管理，每品牌测试第一个域名
- 💾 **Redis存储**：测试结果自动存储到Redis数据库
- 🔄 **缓存同步**：自动清理过期缓存，确保数据与仓库同步
- 📝 **详细日志**：完整的拨测过程日志记录

## 支持的域名格式

程序支持新版JSON格式，通过字段名区分品牌：

```json
{
  "panels": {
    "wujie": [
      {
        "url": "https://apiwj0902.wujie001.info",
        "description": "主Gitee项目域名 - 无界"
      }
    ],
    "v2word": [
      {
        "url": "https://apiv20829.wujie001.info", 
        "description": "主Gitee项目域名 - V2"
      }
    ]
  }
}
```

## 拨测结果

每次拨测会生成详细的分析报告：
- 检测总数和成功数量
- 成功率百分比
- 平均响应时间
- 最高/最低延迟地区
- 域名可用性判断
- 不可用地区列表

## 配置要求

在 `.env` 文件中配置以下变量：

```env
# GitHub仓库配置
GITHUB_DOMAINS_URL="https://raw.githubusercontent.com/PotatoOfficialTeam/domains/main"
GITHUB_TOKEN="your-github-token"
GITHUB_DOMAIN_FILES='["domains.json"]'
GITHUB_REFRESH_INTERVAL=1800

# Redis配置
REDIS_HOST=127.0.0.1
REDIS_PORT=6380
REDIS_DB=0
```

## Redis数据结构

- `domain_test:{domain}` - 域名详细拨测结果
- `domain_test:brand:{brand}` - 品牌域名索引和排序
- `domain_test:metadata` - 拨测元数据信息

## 安装运行

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 配置环境变量：
复制并修改 `.env` 文件

3. 运行程序：
```bash
python domain_tester.py
```

## 使用Supervisor管理

可以使用提供的 `domain_tester.conf` 配置文件通过Supervisor管理进程：

```bash
sudo cp domain_tester.conf /etc/supervisor/conf.d/
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start domain_tester
```

## 拨测流程

1. **获取配置**：从GitHub仓库获取域名配置文件
2. **缓存同步**：清理Redis中过期的域名缓存
3. **执行拨测**：对每个品牌的第一个域名进行拨测
4. **结果存储**：将拨测结果保存到Redis
5. **等待循环**：按配置间隔等待下次拨测

## 日志文件

- `logs/domain_tester.log` - 主程序日志
- `/var/log/supervisor/domain_tester.log` - Supervisor标准输出日志
- `/var/log/supervisor/domain_tester_error.log` - Supervisor错误日志

## 兼容性

- 支持新格式（通过字段名区分品牌）
- 兼容旧格式（通过文件名区分品牌）
- 自动处理数据格式转换