# domain_tester.py
import asyncio
import json
import logging
import os
from dotenv import load_dotenv
import numpy as np
import redis
import time
import httpx
from datetime import datetime

# 加载环境变量
load_dotenv()

# 导入你现有的拨测模块
from redis_opt import redis_operation
from run_boce import run_boce
from aliyun_boce import clean_url

# Redis客户端
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # 只保留标准输出，supervisor会处理日志存储
    ]
)
logger = logging.getLogger("domain_tester")

class NumpyEncoder(json.JSONEncoder):
    """处理numpy数据类型的JSON编码器"""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

async def fetch_domains_from_github(github_url, github_files, github_token=None):
    """从GitHub获取域名列表"""
    domains = []
    headers = {}
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
    
    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        for filename in github_files:
            url = f"{github_url}/{filename}"
            try:
                response = await client.get(url)
                response.raise_for_status()
                
                data = response.json()
                # 处理返回的域名数据
                if isinstance(data, list):
                    file_domains = data
                elif isinstance(data, dict) and "domains" in data:
                    file_domains = data["domains"]
                else:
                    continue
                
                # 提取品牌名称
                brand = filename.split('.')[0]
                
                # 添加域名和品牌信息
                for domain_data in file_domains:
                    if "brand" not in domain_data:
                        domain_data["brand"] = brand
                    domains.append(domain_data)
                    
            except Exception as e:
                logger.error(f"获取域名列表失败: {e}")
    
    return domains
async def test_domain(domain_info):
    """对单个域名执行拨测"""
    domain = domain_info.get("url")
    brand = domain_info.get("brand", "")
    name = domain_info.get("name", domain)
    
    if not domain:
        return None
    
    cleaned_domain = clean_url(domain)
    logger.info(f"开始对域名 {cleaned_domain} 进行拨测")
    
    try:
        # 执行拨测（同步操作）
        loop = asyncio.get_event_loop()
        result_data = await loop.run_in_executor(None, run_boce, cleaned_domain)
        
        # 检查结果
        if result_data is not None:
            # 检查分析结果是否是字典（分析结果）而不是DataFrame
            if isinstance(result_data, dict):
                # 已经是分析结果字典，添加域名信息
                result_data["domain"] = cleaned_domain
                result_data["brand"] = brand
                result_data["name"] = name
                result_data["timestamp"] = int(time.time())
                
                logger.info(f"域名 {cleaned_domain} 拨测完成")
                return result_data
            else:
                logger.error(f"域名 {cleaned_domain} 拨测返回了意外的数据类型: {type(result_data)}")
                return None
        else:
            logger.error(f"域名 {cleaned_domain} 拨测失败，结果为None")
            return None
    except Exception as e:
        logger.error(f"拨测 {domain} 时发生错误: {e}")
        return None

@redis_operation
def save_result_to_redis(client, result):
    """将拨测结果保存到Redis"""
    if not result or "domain" not in result:
        return False
    
    domain = result["domain"]
    brand = result.get("brand", "")
    
    try:
        # 确保没有使用.get()方法处理列表
        # 打印结果结构，帮助调试
        logger.debug(f"拨测结果结构: {type(result)}, 键: {list(result.keys())}")
        
        # 1. 保存域名拨测结果
        redis_key = f"domain_test:{domain}"
        # 使用自定义编码器处理numpy类型
        client.setex(redis_key, 86400, json.dumps(result, cls=NumpyEncoder))  # 24小时过期
        
        # 2. 更新品牌域名索引
        if brand:
            # 获取该品牌现有的所有域名拨测结果
            brand_domains = []
            brand_pattern = f"domain_test:*"
            for key in client.scan_iter(match=brand_pattern):
                key_str = key.decode('utf-8')
                if key_str == "domain_test:metadata" or key_str.startswith("domain_test:brand:"):
                    continue  # 跳过元数据和品牌索引键
                    
                domain_data = client.get(key)
                if domain_data:
                    try:
                        domain_obj = json.loads(domain_data)
                        # 确保domain_obj是字典而不是列表
                        if isinstance(domain_obj, dict) and domain_obj.get("brand") == brand:
                            brand_domains.append(domain_obj)
                    except json.JSONDecodeError:
                        logger.warning(f"Redis键 {key_str} 包含无效JSON")
                        continue
            
            # 按成功率排序
            brand_domains.sort(key=lambda x: (-x.get("success_rate", 0), x.get("average_response_time_ms", 999999)))
            
            # 保存排序后的品牌域名列表
            brand_key = f"domain_test:brand:{brand}"
            brand_summary = []
            for d in brand_domains:
                if isinstance(d, dict):  # 确保是字典
                    brand_summary.append({
                        "domain": d.get("domain", "unknown"),
                        "name": d.get("name", ""),
                        "success_rate": d.get("success_rate", 0)
                    })
            
            client.setex(brand_key, 86400, json.dumps(brand_summary, cls=NumpyEncoder))
        
        # 3. 更新拨测元数据
        metadata = {
            "last_test_time": int(time.time()),
            "domain_count": len(list(client.scan_iter(match="domain_test:*"))) - 
                          len(list(client.scan_iter(match="domain_test:brand:*"))) - 1
        }
        client.set("domain_test:metadata", json.dumps(metadata))
        
        logger.info(f"域名 {domain} 拨测结果已保存到Redis")
        return True
    except Exception as e:
        logger.error(f"保存拨测结果到Redis失败: {e}", exc_info=True)
        return False
    
async def main():
    """主函数"""
    logger.info("拨测服务启动")
    
    # 从环境变量获取GitHub配置
    github_url = os.environ.get("GITHUB_DOMAINS_URL")
    github_token = os.environ.get("GITHUB_TOKEN")
    
    # 从环境变量获取并解析文件列表
    github_files_str = os.environ.get("GITHUB_DOMAIN_FILES")
    try:
        github_files = json.loads(github_files_str)
    except json.JSONDecodeError:
        logger.error(f"无法解析GITHUB_DOMAIN_FILES环境变量: {github_files_str}，使用默认值")
        github_files = []
    
    # 获取刷新间隔（单位：秒）
    try:
        refresh_interval = int(os.environ.get("GITHUB_REFRESH_INTERVAL", 1800))
    except ValueError:
        logger.error("无法解析GITHUB_REFRESH_INTERVAL环境变量，使用默认值1800秒")
        refresh_interval = 1800
    
    logger.info(f"GitHub配置: URL={github_url}, 文件={github_files}, 刷新间隔={refresh_interval}秒")
    
    while True:
        try:
            # 1. 从GitHub获取域名列表
            domains = await fetch_domains_from_github(github_url, github_files, github_token)
            logger.info(f"获取到 {len(domains)} 个域名")
            
            if not domains:
                logger.warning("未获取到任何域名，等待5分钟后重试")
                await asyncio.sleep(300)
                continue
            
            # 2. 顺序执行拨测
            for domain_info in domains:
                # 执行拨测
                result = await test_domain(domain_info)
                
                # 保存结果到Redis
                if result:
                    save_result_to_redis(result)
                
                # 每个域名拨测后短暂等待，避免过于频繁
                await asyncio.sleep(5)
            
            logger.info(f"所有域名拨测完成，等待{refresh_interval}秒后进行下一轮拨测")
            
            # 3. 使用环境变量中配置的刷新间隔等待
            await asyncio.sleep(refresh_interval)
            
        except Exception as e:
            logger.error(f"拨测过程中发生错误: {e}", exc_info=True)
            # 出错后等待5分钟再重试
            await asyncio.sleep(300)

if __name__ == "__main__":
    asyncio.run(main())