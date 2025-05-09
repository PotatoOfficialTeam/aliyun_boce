import time
import redis
from redis.exceptions import ConnectionError, TimeoutError
import logging
import backoff  # 推荐安装这个库来处理重试逻辑

# Redis连接池
redis_pool = None
redis_client = None

# 创建Redis客户端的函数(使用backoff库进行指数退避重试)
@backoff.on_exception(backoff.expo, 
                     (ConnectionError, TimeoutError),
                     max_tries=None,  # 无限重试
                     max_time=None,   # 无时间限制
                     on_backoff=lambda details: logger.warning(
                         f"Redis连接失败，正在进行第{details['tries']}次重试，等待{details['wait']:.2f}秒..."))
def get_redis_client():
    global redis_pool, redis_client
    
    if redis_client is not None:
        try:
            # 测试连接是否有效
            redis_client.ping()
            return redis_client
        except:
            logger.warning("现有Redis连接无效，尝试重新建立连接...")
            redis_client = None
    
    # 创建连接池(如果还没有)
    if redis_pool is None:
        redis_pool = redis.ConnectionPool(
            host='localhost', 
            port=6379, 
            db=0,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30
        )
    
    # 创建客户端
    redis_client = redis.Redis(connection_pool=redis_pool)
    
    # 测试连接
    redis_client.ping()
    logger.info("成功连接到Redis服务器")
    
    return redis_client

# 包装Redis操作的函数，支持自动重试
def redis_operation(operation_func):
    """装饰器，为Redis操作添加自动重试功能"""
    def wrapper(*args, **kwargs):
        while True:
            try:
                # 确保获取最新的有效连接
                client = get_redis_client()
                # 执行Redis操作
                return operation_func(client, *args, **kwargs)
            except (ConnectionError, TimeoutError) as e:
                logger.error(f"执行Redis操作时发生连接错误: {e}")
                # 重置客户端，下次循环会重新获取
                global redis_client
                redis_client = None
                # 短暂等待后重试
                time.sleep(1)
            except Exception as e:
                logger.error(f"执行Redis操作时发生其他错误: {e}")
                # 非连接类错误，可能需要传递给调用者
                raise
    return wrapper