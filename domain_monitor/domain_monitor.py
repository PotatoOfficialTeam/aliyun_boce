#!/usr/bin/env python3
"""
智能域名监控和管理程序
监控Redis中的域名健康状况，当检测到问题时自动创建新的Cloudflare A记录
"""

import asyncio
import json
import os
import redis
import requests
from datetime import date
from dotenv import load_dotenv
from logging_config import setup_logging

# 加载环境变量
load_dotenv()

# 配置日志
logger = setup_logging("domain_monitor")

class CloudflareManager:
    """Cloudflare DNS管理器"""
    
    def __init__(self, email, api_key):
        self.email = email
        self.api_key = api_key
        self.base_url = "https://api.cloudflare.com/client/v4"
        self.headers = {
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Content-Type": "application/json"
        }
        self.zone_cache = {}
    
    def get_zone_id(self, domain):
        """获取域名的Zone ID"""
        if domain in self.zone_cache:
            return self.zone_cache[domain]
        
        url = f"{self.base_url}/zones"
        params = {"name": domain}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data["success"] and data["result"]:
                zone_id = data["result"][0]["id"]
                self.zone_cache[domain] = zone_id
                return zone_id
            else:
                logger.error(f"未找到域名 {domain} 的Zone ID: {data}")
                return None
                
        except Exception as e:
            logger.error(f"获取Zone ID失败 {domain}: {e}")
            return None
    
    def create_a_record(self, zone_id, name, ip, ttl=300):
        """创建A记录"""
        url = f"{self.base_url}/zones/{zone_id}/dns_records"
        
        data = {
            "type": "A",
            "name": name,
            "content": ip,
            "ttl": ttl,
            "proxied": False  # 不通过CF代理，直接解析
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            if result["success"]:
                logger.info(f"成功创建A记录: {name} -> {ip}")
                return result["result"]
            else:
                logger.error(f"创建A记录失败: {result}")
                return None
                
        except Exception as e:
            logger.error(f"创建A记录时发生错误: {e}")
            return None
    
    def check_record_exists(self, zone_id, name):
        """检查DNS记录是否已存在"""
        url = f"{self.base_url}/zones/{zone_id}/dns_records"
        params = {"name": name, "type": "A"}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data["success"] and data["result"]:
                return data["result"][0]  # 返回第一个匹配的记录
            return None
            
        except Exception as e:
            logger.error(f"检查DNS记录时发生错误: {e}")
            return None

class DomainHealthMonitor:
    """域名健康监控器"""
    
    def __init__(self, redis_host, redis_port, redis_db):
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, db=redis_db)
        self.success_rate_threshold = 0.7  # 成功率低于70%时触发
        self.response_time_threshold = 15000  # 响应时间超过15秒时触发
        
    def get_domain_health(self, brand):
        """获取指定品牌的域名健康状况"""
        try:
            # 获取品牌的域名列表
            brand_key = f"domain_test:brand:{brand}"
            brand_data = self.redis_client.get(brand_key)
            
            if not brand_data:
                logger.warning(f"未找到品牌 {brand} 的数据")
                return None
            
            if isinstance(brand_data, bytes):
                brand_domains = json.loads(brand_data.decode('utf-8'))
            elif isinstance(brand_data, str):
                brand_domains = json.loads(brand_data)
            else:
                logger.error(f"未知的brand_data类型: {type(brand_data)}")
                return None
            if not brand_domains:
                return None
            
            # 获取第一个域名的详细健康数据
            primary_domain = brand_domains[0]
            domain_name = primary_domain.get("domain")
            
            if not domain_name:
                return None
            
            # 获取详细的拨测结果
            domain_key = f"domain_test:{domain_name}"
            domain_data = self.redis_client.get(domain_key)
            
            if not domain_data:
                return None
            
            if isinstance(domain_data, bytes):
                health_data = json.loads(domain_data.decode('utf-8'))
            elif isinstance(domain_data, str):
                health_data = json.loads(domain_data)
            else:
                logger.error(f"未知的domain_data类型: {type(domain_data)}")
                return None
            return {
                "domain": domain_name,
                "brand": brand,
                "success_rate": health_data.get("success_rate", 0),
                "average_response_time_ms": health_data.get("average_response_time_ms", 999999),
                "timestamp": health_data.get("timestamp", 0),
                "raw_data": health_data
            }
            
        except Exception as e:
            logger.error(f"获取域名健康数据失败 {brand}: {e}")
            return None
    
    def should_create_new_domain(self, health_data):
        """判断是否需要创建新域名"""
        if not health_data:
            return False
        
        success_rate = health_data.get("success_rate", 1.0)
        response_time = health_data.get("average_response_time_ms", 0)
        
        # 如果成功率数据是百分比形式（>1），转换为小数
        if success_rate > 1:
            success_rate = success_rate / 100
        
        # 检查成功率是否过低
        if success_rate < self.success_rate_threshold:
            logger.info(f"域名 {health_data['domain']} 成功率过低: {success_rate:.2%}")
            return True
        
        # 检查响应时间是否过长
        if response_time > self.response_time_threshold:
            logger.info(f"域名 {health_data['domain']} 响应时间过长: {round(response_time)}ms")
            return True
        
        return False

class DomainNameGenerator:
    """域名名称生成器"""
    
    @staticmethod
    def generate_subdomain(brand):
        """生成新的子域名"""
        today = date.today()
        date_str = today.strftime("%y%m%d")  # 格式: YYMMDD
        
        if brand.lower() == "wujie":
            prefix = "apiwj"
        elif brand.lower() == "v2word":
            prefix = "apiv2"
        else:
            prefix = f"api{brand.lower()}"
        
        return f"{prefix}{date_str}"

class DomainMonitor:
    """主域名监控类"""
    
    def __init__(self):
        # 从环境变量加载配置
        self.cf_email = os.environ.get("CF_EMAIL")
        self.cf_api_key = os.environ.get("CF_API_KEY")
        self.caddy_ip = os.environ.get("CADDY_IP")
        self.v2word_domain = os.environ.get("V2WORD", "v20000.cfd")
        self.wujie_domain = os.environ.get("WUJIE", "wj0001.cfd")
        
        # Redis配置
        redis_host = os.environ.get("REDIS_HOST", "127.0.0.1")
        redis_port = int(os.environ.get("REDIS_PORT", 6380))
        redis_db = int(os.environ.get("REDIS_DB", 0))
        
        # 初始化组件
        self.cf_manager = CloudflareManager(self.cf_email, self.cf_api_key)
        self.health_monitor = DomainHealthMonitor(redis_host, redis_port, redis_db)
        self.domain_generator = DomainNameGenerator()
        
        # 品牌域名映射
        self.brand_domains = {
            "wujie": self.wujie_domain,
            "v2word": self.v2word_domain
        }
        
        logger.info(f"域名监控器已初始化: CF={self.cf_email}, Caddy IP={self.caddy_ip}")
    
    def create_new_domain_for_brand(self, brand):
        """为指定品牌创建新的域名解析，返回创建的域名信息"""
        try:
            # 获取品牌对应的主域名
            main_domain = self.brand_domains.get(brand)
            if not main_domain:
                logger.error(f"未找到品牌 {brand} 的主域名配置")
                return None
            
            # 生成新的子域名
            subdomain = self.domain_generator.generate_subdomain(brand)
            full_domain = f"{subdomain}.{main_domain}"
            
            logger.info(f"为品牌 {brand} 生成新域名: {full_domain}")
            
            # 获取Cloudflare Zone ID
            zone_id = self.cf_manager.get_zone_id(main_domain)
            if not zone_id:
                logger.error(f"无法获取域名 {main_domain} 的Zone ID")
                return None
            
            # 检查记录是否已存在
            existing_record = self.cf_manager.check_record_exists(zone_id, full_domain)
            if existing_record:
                logger.info(f"域名 {full_domain} 已存在，跳过创建")
                return {
                    "brand": brand,
                    "domain": full_domain,
                    "status": "existed",
                    "description": f"自动生成的域名 - {brand}"
                }
            
            # 创建A记录
            result = self.cf_manager.create_a_record(zone_id, full_domain, self.caddy_ip)
            if result:
                logger.info(f"成功为品牌 {brand} 创建新域名: {full_domain} -> {self.caddy_ip}")
                return {
                    "brand": brand,
                    "domain": full_domain,
                    "status": "created",
                    "description": f"自动生成的域名 - {brand}",
                    "ip": self.caddy_ip
                }
            else:
                logger.error(f"创建域名失败: {full_domain}")
                return None
                
        except Exception as e:
            logger.error(f"为品牌 {brand} 创建新域名时发生错误: {e}")
            return None
    
    async def monitor_and_manage(self):
        """监控并管理域名"""
        logger.info("开始域名监控...")
        
        # 监控的品牌列表
        brands = ["wujie", "v2word"]
        
        while True:
            try:
                for brand in brands:
                    logger.info(f"检查品牌 {brand} 的域名健康状况")
                    
                    # 获取域名健康数据
                    health_data = self.health_monitor.get_domain_health(brand)
                    if not health_data:
                        logger.warning(f"无法获取品牌 {brand} 的健康数据")
                        continue
                    
                    # 修正成功率显示格式
                    success_rate = health_data['success_rate']
                    if success_rate > 1:
                        success_rate = success_rate / 100  # 如果数据是百分比形式，转换为小数
                    
                    logger.info(f"品牌 {brand}: 域名={health_data['domain']}, "
                              f"成功率={success_rate:.2%}, "
                              f"响应时间={round(health_data['average_response_time_ms'])}ms")
                    
                    # 判断是否需要创建新域名
                    if self.health_monitor.should_create_new_domain(health_data):
                        logger.warning(f"品牌 {brand} 域名健康状况不佳，准备创建新域名")
                        success = self.create_new_domain_for_brand(brand)
                        if success:
                            logger.info(f"品牌 {brand} 新域名创建成功")
                        else:
                            logger.error(f"品牌 {brand} 新域名创建失败")
                    else:
                        logger.info(f"品牌 {brand} 域名健康状况良好")
                
                # 等待下次检查（每10分钟检查一次）
                logger.info("域名监控周期完成，等待10分钟后继续...")
                await asyncio.sleep(600)
                
            except Exception as e:
                logger.error(f"域名监控过程中发生错误: {e}", exc_info=True)
                # 出错后等待5分钟再重试
                await asyncio.sleep(300)

def check_domain_health(brand: str) -> dict:
    """
    检查指定品牌的域名健康状况
    
    Args:
        brand: 品牌名称
        
    Returns:
        dict: 健康状况数据，如果失败返回None
    """
    try:
        # Redis配置
        redis_host = os.environ.get("REDIS_HOST", "127.0.0.1")
        redis_port = int(os.environ.get("REDIS_PORT", 6380))
        redis_db = int(os.environ.get("REDIS_DB", 0))
        
        health_monitor = DomainHealthMonitor(redis_host, redis_port, redis_db)
        return health_monitor.get_domain_health(brand)
    except Exception as e:
        logger.error(f"检查域名健康状况失败: {e}")
        return None

def should_create_new_domain(brand: str) -> tuple:
    """
    判断是否应该为品牌创建新域名
    
    Args:
        brand: 品牌名称
        
    Returns:
        tuple: (should_create: bool, health_data: dict, reason: str)
    """
    try:
        health_data = check_domain_health(brand)
        if not health_data:
            return False, None, "无法获取健康数据"
        
        # Redis配置
        redis_host = os.environ.get("REDIS_HOST", "127.0.0.1") 
        redis_port = int(os.environ.get("REDIS_PORT", 6380))
        redis_db = int(os.environ.get("REDIS_DB", 0))
        
        health_monitor = DomainHealthMonitor(redis_host, redis_port, redis_db)
        
        if health_monitor.should_create_new_domain(health_data):
            success_rate = health_data.get("success_rate", 1.0)
            if success_rate > 1:
                success_rate = success_rate / 100
            
            response_time = health_data.get("average_response_time_ms", 0)
            
            if success_rate < health_monitor.success_rate_threshold:
                reason = f"成功率过低: {success_rate:.2%}"
            elif response_time > health_monitor.response_time_threshold:
                reason = f"响应时间过长: {round(response_time)}ms"
            else:
                reason = "域名健康状况不佳"
            
            return True, health_data, reason
        else:
            return False, health_data, "域名健康状况良好"
    
    except Exception as e:
        logger.error(f"判断是否需要创建新域名失败: {e}")
        return False, None, f"检查失败: {str(e)}"

def create_new_domain(brand: str) -> dict:
    """
    为指定品牌创建新域名
    
    Args:
        brand: 品牌名称
        
    Returns:
        dict: 创建结果，包含域名信息，失败返回None
    """
    try:
        monitor = DomainMonitor()
        return monitor.create_new_domain_for_brand(brand)
    except Exception as e:
        logger.error(f"创建新域名失败: {e}")
        return None

def monitor_single_check(brands: list = None) -> dict:
    """
    执行一次域名监控检查
    
    Args:
        brands: 要检查的品牌列表，默认为["wujie", "v2word"]
        
    Returns:
        dict: 检查结果
    """
    if brands is None:
        brands = ["wujie", "v2word"]
    
    results = {}
    
    for brand in brands:
        logger.info(f"检查品牌 {brand} 的域名健康状况")
        
        # 检查是否需要创建新域名
        should_create, health_data, reason = should_create_new_domain(brand)
        
        result = {
            "brand": brand,
            "health_data": health_data,
            "should_create": should_create,
            "reason": reason,
            "new_domain": None
        }
        
        if health_data:
            success_rate = health_data.get("success_rate", 0)
            if success_rate > 1:
                success_rate = success_rate / 100
            
            logger.info(f"品牌 {brand}: 域名={health_data['domain']}, "
                      f"成功率={success_rate:.2%}, "
                      f"响应时间={round(health_data['average_response_time_ms'])}ms")
        
        if should_create:
            logger.warning(f"品牌 {brand} 域名健康状况不佳: {reason}")
            new_domain_info = create_new_domain(brand)
            if new_domain_info:
                result["new_domain"] = new_domain_info
                logger.info(f"品牌 {brand} 新域名创建成功: {new_domain_info['domain']}")
            else:
                logger.error(f"品牌 {brand} 新域名创建失败")
        else:
            logger.info(f"品牌 {brand} 域名健康状况良好")
        
        results[brand] = result
    
    return results

async def main():
    """主函数"""
    logger.info("智能域名监控程序启动")
    
    try:
        monitor = DomainMonitor()
        await monitor.monitor_and_manage()
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序启动失败: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())