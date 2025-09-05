# 智能域名监控系统

自动监控域名健康状况，当检测到可访问性问题时自动创建新的Cloudflare DNS记录。

## 功能特性

- 🔍 **智能监控**：实时监控Redis中的域名拨测数据
- 🚀 **自动创建**：当域名出现问题时自动创建新的A记录
- 🌐 **Cloudflare集成**：直接通过API管理DNS记录
- 📊 **健康阈值**：可配置的成功率和响应时间阈值
- 🏷️ **智能命名**：自动生成有规律的子域名

## 域名生成规则

- **wujie品牌**: `apiwj{YYMMDD}.wj0001.cfd`
- **v2word品牌**: `apiv2{YYMMDD}.v20000.cfd`

例如：2025年9月5日会生成 `apiwj250905.wj0001.cfd`

## 触发条件

程序会在以下情况下创建新域名：
- 域名成功率 < 70%
- 平均响应时间 > 15秒

## 配置要求

在 `.env` 文件中配置以下变量：

```env
# Cloudflare API配置
CF_EMAIL=your-email@domain.com
CF_API_KEY=your-cloudflare-api-key

# 服务器配置
CADDY_IP=your-server-ip

# 品牌域名配置
V2WORD=v20000.cfd
WUJIE=wj0001.cfd

# Redis配置
REDIS_HOST=127.0.0.1
REDIS_PORT=6380
REDIS_DB=0
```

## 安装运行

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 运行程序：
```bash
python domain_monitor.py
```

## 监控频率

- 每10分钟检查一次域名健康状况
- 出错后等待5分钟重试
- 避免创建重复的DNS记录

## 日志记录

程序会将日志同时输出到：
- 控制台（实时查看）
- `logs/domain_monitor.log`文件（永久保存）

## 独立运行

此程序完全独立于域名拨测系统，可以单独部署和运行。