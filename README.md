# 阿里云域名拨测和监控系统

一个完整的域名可访问性监控解决方案，包含自动拨测、智能域名管理和GitHub自动化功能。

## 项目结构

```
aliyun_boce/
├── coordinator.py          # 🎯 主协调程序（新增）
├── domain_tester/          # 域名拨测系统
│   ├── domain_tester.py    # 主拨测程序
│   ├── aliyun_boce.py     # 阿里云拨测接口
│   ├── run_boce.py        # 拨测执行器
│   ├── redis_opt.py       # Redis操作模块
│   ├── logging_config.py  # 日志配置
│   ├── domain_tester.conf # Supervisor配置
│   ├── requirements.txt   # 依赖包
│   └── README.md         # 详细说明
├── domain_monitor/         # 智能域名监控系统
│   ├── domain_monitor.py   # 主监控程序（已改为可调用）
│   ├── domain_json/       # 🗂️ domains.json文件目录（新增）
│   │   └── domains.json   # 域名配置文件
│   ├── logging_config.py  # 日志配置
│   ├── requirements.txt   # 依赖包
│   └── README.md         # 详细说明
├── github_manager/         # 🐙 GitHub管理模块（新增）
│   ├── domains_manager.py  # GitHub操作和JSON管理
│   ├── requirements.txt   # 依赖包
│   └── README.md         # 详细说明
├── logs/                  # 日志目录
├── docker-compose.yml     # Docker编排配置
├── Dockerfile            # Docker镜像构建
└── .env                  # 环境变量配置
```

## 系统组件

### 🎯 主协调程序 (`coordinator.py`)

**核心功能**：
- 协调 domain_monitor 和 github_manager 模块
- 检测到域名问题时自动创建DNS记录
- 将新域名自动添加到 domains.json
- 自动提交并推送到GitHub仓库

**运行模式**：
```bash
# 持续监控模式（默认每10分钟检查一次）
python coordinator.py

# 手动执行一次检查
python coordinator.py --manual
```

### 1. 域名拨测系统 (`domain_tester/`)

**功能**：
- 从GitHub仓库自动获取域名配置
- 使用阿里云拨测服务进行可访问性检测
- 支持多品牌域名管理
- 结果存储到Redis数据库
- 自动缓存同步和清理

**特点**：
- 支持新旧两种配置格式
- 每个品牌只测试第一个域名
- 详细的拨测结果分析
- 完整的日志记录

### 2. 智能域名监控系统 (`domain_monitor/`)

**功能**：
- 监控Redis中的域名健康数据
- 当检测到可访问性问题时自动创建新域名
- 通过Cloudflare API管理DNS记录
- 智能的域名生成规则

**特点**：
- 可配置的健康阈值（成功率<70%，响应时间>15秒）
- 自动生成有规律的子域名（如：apiwj250905.wj0001.cfd）
- 避免重复创建记录
- 支持函数调用模式

### 3. GitHub管理模块 (`github_manager/`)

**功能**：
- 读取和修改 domains.json 文件
- 在品牌域名列表开头添加新域名
- 自动Git提交和推送到远程仓库
- 同步远程更改

**特点**：
- 智能的JSON文件管理
- 自动生成提交消息
- 错误处理和回滚机制
- 支持多品牌域名管理

## 🔄 完整工作流程

### 自动化流程
1. **domain_tester** 持续从GitHub获取配置并拨测域名
2. **coordinator** 定期检查Redis中的域名健康数据
3. 当检测到问题时：
   - **domain_monitor** 自动创建新的Cloudflare DNS记录
   - **github_manager** 替换品牌的第一个域名为新域名
   - **github_manager** 自动提交并推送到GitHub
4. **domain_tester** 在下次更新时获取新配置
5. 新域名开始接受拨测，形成闭环

### 触发条件
- 域名成功率 < 70%
- 平均响应时间 > 15秒
- 连续拨测失败

## 配置要求

需要在 `.env` 文件中配置：

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

# Cloudflare配置
CF_EMAIL=your-email@domain.com
CF_API_KEY=your-cloudflare-api-key

# 服务器配置
CADDY_IP=your-server-ip
V2WORD=v20000.cfd
WUJIE=wj0001.cfd
```

## 🚀 快速开始

### 1. 运行完整的协调系统（推荐）

```bash
# 安装所有依赖
pip install -r domain_monitor/requirements.txt
pip install -r github_manager/requirements.txt

# 配置环境变量
cp .env.example .env  # 修改配置

# 手动测试一次
python coordinator.py --manual

# 启动持续监控
python coordinator.py
```

### 2. 单独运行各组件

**拨测系统**：
```bash
cd domain_tester
pip install -r requirements.txt
python domain_tester.py
```

**监控系统**：
```bash
cd domain_monitor  
pip install -r requirements.txt
python domain_monitor.py
```

### 3. 使用Docker运行

```bash
docker-compose up -d
```

## 监控数据

系统将生成以下Redis数据：

- **域名测试结果**：`domain_test:{domain}`
- **品牌域名索引**：`domain_test:brand:{brand}`
- **系统元数据**：`domain_test:metadata`

## 日志记录

两个系统都会生成详细的日志：
- 控制台实时输出
- 本地日志文件存储
- Supervisor日志管理（可选）

## 扩展性

- 支持添加新的拨测服务提供商
- 可配置的健康检查规则
- 模块化的DNS管理接口
- 灵活的域名生成策略

## 注意事项

- 确保Redis服务正常运行
- Cloudflare API密钥需要Zone编辑权限
- GitHub Token需要仓库读取权限
- 服务器IP地址需要正确配置