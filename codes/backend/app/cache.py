import redis
import os
from typing import Optional

# Redis连接配置
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# 创建Redis客户端
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

def get_redis_client() -> redis.Redis:
    """获取Redis客户端实例"""
    return redis_client

def set_cache(key: str, value: str, expire: Optional[int] = None) -> bool:
    """设置缓存"""
    try:
        if expire:
            return redis_client.setex(key, expire, value)
        else:
            return redis_client.set(key, value)
    except Exception as e:
        print(f"设置缓存失败: {e}")
        return False

def get_cache(key: str) -> Optional[str]:
    """获取缓存"""
    try:
        return redis_client.get(key)
    except Exception as e:
        print(f"获取缓存失败: {e}")
        return None

def delete_cache(key: str) -> bool:
    """删除缓存"""
    try:
        return bool(redis_client.delete(key))
    except Exception as e:
        print(f"删除缓存失败: {e}")
        return False

def clear_cache() -> bool:
    """清空所有缓存"""
    try:
        redis_client.flushdb()
        return True
    except Exception as e:
        print(f"清空缓存失败: {e}")
        return False
