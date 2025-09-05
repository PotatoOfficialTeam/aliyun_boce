#!/usr/bin/env python3
"""
主协调程序
协调 domain_monitor 和 github_manager 模块，实现完整的域名管理工作流
"""

import asyncio
import logging
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# 添加各模块到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir / "domain_monitor"))
sys.path.insert(0, str(current_dir / "github_manager"))

# 导入各模块
import domain_monitor
from github_api import DomainsGitHubManager

# 获取需要的函数
monitor_single_check = domain_monitor.monitor_single_check

# 加载环境变量
load_dotenv()

class DomainCoordinator:
    """域名协调器 - 协调各个模块的工作"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        
        # 配置 GitHub API 管理器
        domains_file_path = current_dir / "domain_monitor" / "domain_json" / "domains.json"
        
        if not domains_file_path.exists():
            raise FileNotFoundError(f"domains.json 文件不存在: {domains_file_path}")
        
        # 从环境变量获取GitHub配置
        github_token = os.environ.get("GITEE_DOMAINS_TOKEN")
        if not github_token:
            raise ValueError("未找到GITHUB_TOKEN环境变量")
        
        self.github_manager = DomainsGitHubManager(
            domains_file_path=str(domains_file_path),
            github_token=github_token,
            repo_owner="PotatoOfficialTeam",
            repo_name="domains",  # 修正仓库名称
            target_file_path="domains.json"
        )
        
        # 配置检查间隔（分钟）
        self.check_interval = int(os.environ.get("COORDINATOR_INTERVAL", 10))
        
        self.logger.info(f"域名协调器已初始化")
        self.logger.info(f"domains.json路径: {domains_file_path}")
        self.logger.info(f"GitHub仓库: PotatoOfficialTeam/domains")
        self.logger.info(f"检查间隔: {self.check_interval}分钟")
    
    def _setup_logging(self):
        """设置日志配置"""
        logger = logging.getLogger("coordinator")
        logger.setLevel(logging.INFO)
        
        # 避免重复添加handler
        if logger.hasHandlers():
            logger.handlers.clear()
        
        # 创建日志目录
        log_dir = current_dir / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # 创建formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 控制台handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 文件handler
        log_file = log_dir / "coordinator.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def process_domain_creation(self, brand: str, new_domain_info: dict) -> bool:
        """
        处理新域名的创建和GitHub提交
        
        Args:
            brand: 品牌名称
            new_domain_info: 新域名信息
            
        Returns:
            bool: 处理是否成功
        """
        try:
            domain_url = new_domain_info.get("domain")
            description = new_domain_info.get("description", "")
            
            if not domain_url:
                self.logger.error("域名信息中缺少domain字段")
                return False
            
            # 添加https前缀
            if not domain_url.startswith(("http://", "https://")):
                full_url = f"https://{domain_url}"
            else:
                full_url = domain_url
            
            self.logger.info(f"开始处理品牌 {brand} 的新域名: {full_url}")
            
            # 替换品牌第一个域名并提交到GitHub
            success = self.github_manager.replace_and_commit(
                brand=brand,
                new_domain=full_url,
                description=description
            )
            
            if success:
                self.logger.info(f"成功替换域名到GitHub: {brand} -> {full_url}")
                return True
            else:
                self.logger.error(f"替换域名到GitHub失败: {brand} -> {full_url}")
                return False
                
        except Exception as e:
            self.logger.error(f"处理新域名创建失败: {e}")
            return False
    
    def single_check_and_process(self) -> dict:
        """
        执行一次完整的检查和处理流程
        
        Returns:
            dict: 处理结果
        """
        self.logger.info("开始执行域名监控检查...")
        
        try:
            # 1. 执行域名健康监控检查
            monitor_results = monitor_single_check()
            
            process_results = {}
            
            # 2. 处理每个品牌的结果
            for brand, result in monitor_results.items():
                process_result = {
                    "brand": brand,
                    "health_check": result,
                    "github_updated": False,
                    "error": None
                }
                
                # 如果需要创建新域名且已成功创建
                if result.get("should_create") and result.get("new_domain"):
                    new_domain_info = result["new_domain"]
                    
                    if new_domain_info["status"] in ["created", "existed"]:
                        # 处理域名添加到GitHub
                        github_success = self.process_domain_creation(brand, new_domain_info)
                        process_result["github_updated"] = github_success
                        
                        if github_success:
                            self.logger.info(f"品牌 {brand} 完整流程处理成功")
                        else:
                            process_result["error"] = "GitHub更新失败"
                    else:
                        process_result["error"] = "域名创建失败"
                
                process_results[brand] = process_result
            
            self.logger.info("域名监控检查完成")
            return {
                "timestamp": int(time.time()),
                "success": True,
                "results": process_results
            }
            
        except Exception as e:
            self.logger.error(f"检查和处理流程失败: {e}")
            return {
                "timestamp": int(time.time()),
                "success": False,
                "error": str(e)
            }
    
    async def start_monitoring(self):
        """开始持续监控"""
        self.logger.info(f"开始持续域名协调监控，每{self.check_interval}分钟检查一次")
        
        while True:
            try:
                # 执行检查和处理
                result = self.single_check_and_process()
                
                if result["success"]:
                    self.logger.info(f"本轮检查完成，等待{self.check_interval}分钟...")
                else:
                    self.logger.error(f"本轮检查失败: {result.get('error', '未知错误')}")
                
                # 等待下次检查
                await asyncio.sleep(self.check_interval * 60)  # 转换为秒
                
            except KeyboardInterrupt:
                self.logger.info("收到中断信号，停止监控")
                break
            except Exception as e:
                self.logger.error(f"监控过程中发生意外错误: {e}", exc_info=True)
                # 出错后等待5分钟再重试
                await asyncio.sleep(300)
    
    def manual_check(self):
        """手动执行一次检查（用于测试）"""
        self.logger.info("执行手动检查...")
        result = self.single_check_and_process()
        
        print("\n=== 检查结果 ===")
        print(f"执行时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(result['timestamp']))}")
        print(f"整体状态: {'成功' if result['success'] else '失败'}")
        
        if result.get("error"):
            print(f"错误信息: {result['error']}")
        
        if result.get("results"):
            for brand, brand_result in result["results"].items():
                print(f"\n品牌: {brand}")
                health = brand_result["health_check"]
                
                if health.get("health_data"):
                    hd = health["health_data"]
                    success_rate = hd.get("success_rate", 0)
                    if success_rate > 1:
                        success_rate = success_rate / 100
                    
                    print(f"  域名: {hd.get('domain', 'N/A')}")
                    print(f"  成功率: {success_rate:.2%}")
                    print(f"  响应时间: {round(hd.get('average_response_time_ms', 0))}ms")
                    print(f"  需要新域名: {'是' if health.get('should_create') else '否'}")
                    print(f"  原因: {health.get('reason', 'N/A')}")
                
                if health.get("new_domain"):
                    nd = health["new_domain"]
                    print(f"  新域名: {nd.get('domain', 'N/A')}")
                    print(f"  创建状态: {nd.get('status', 'N/A')}")
                
                print(f"  GitHub更新: {'成功' if brand_result.get('github_updated') else '未更新'}")
                
                if brand_result.get("error"):
                    print(f"  错误: {brand_result['error']}")
        
        return result

async def main():
    """主函数"""
    coordinator = DomainCoordinator()
    
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == "--manual":
        # 手动模式
        coordinator.manual_check()
    else:
        # 持续监控模式
        await coordinator.start_monitoring()

if __name__ == "__main__":
    asyncio.run(main())