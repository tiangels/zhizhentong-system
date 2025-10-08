"""
流式输出配置模块
"""
from typing import Dict, Any
import os

class StreamingConfig:
    """流式输出配置类"""
    
    # 流式输出模式配置
    STREAMING_MODE = os.getenv("STREAMING_MODE", "real")  # real, pseudo, hybrid
    
    # 真流式输出配置
    REAL_STREAMING = {
        "enabled": True,
        "chunk_size": 1,  # 每个token立即发送
        "buffer_size": 0,  # 不使用缓冲
        "delay_ms": 0,  # 无延迟
        "timeout": 60.0,  # 60秒超时
    }
    
    # 伪流式输出配置（回退模式）
    PSEUDO_STREAMING = {
        "enabled": False,
        "chunk_size": 20,  # 每次发送20个字符
        "buffer_size": 100,  # 100字符缓冲
        "delay_ms": 100,  # 100ms延迟
        "timeout": 30.0,  # 30秒超时
    }
    
    # 混合模式配置
    HYBRID_STREAMING = {
        "enabled": False,
        "real_threshold": 0.8,  # 80%概率使用真流式
        "fallback_to_pseudo": True,  # 失败时回退到伪流式
        "timeout": 45.0,  # 45秒超时
    }
    
    @classmethod
    def get_streaming_config(cls) -> Dict[str, Any]:
        """获取当前流式输出配置"""
        if cls.STREAMING_MODE == "real":
            return cls.REAL_STREAMING
        elif cls.STREAMING_MODE == "pseudo":
            return cls.PSEUDO_STREAMING
        elif cls.STREAMING_MODE == "hybrid":
            return cls.HYBRID_STREAMING
        else:
            return cls.REAL_STREAMING
    
    @classmethod
    def is_real_streaming_enabled(cls) -> bool:
        """检查是否启用真流式输出"""
        config = cls.get_streaming_config()
        return config.get("enabled", True)
    
    @classmethod
    def get_chunk_size(cls) -> int:
        """获取数据块大小"""
        config = cls.get_streaming_config()
        return config.get("chunk_size", 1)
    
    @classmethod
    def get_delay_ms(cls) -> int:
        """获取延迟时间（毫秒）"""
        config = cls.get_streaming_config()
        return config.get("delay_ms", 0)
    
    @classmethod
    def get_timeout(cls) -> float:
        """获取超时时间（秒）"""
        config = cls.get_streaming_config()
        return config.get("timeout", 60.0)

# 流式输出状态监控
class StreamingMonitor:
    """流式输出监控类"""
    
    def __init__(self):
        self.stats = {
            "total_requests": 0,
            "real_streaming_requests": 0,
            "pseudo_streaming_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "total_tokens_generated": 0,
        }
    
    def record_request(self, mode: str, response_time: float, tokens: int = 0):
        """记录请求统计"""
        self.stats["total_requests"] += 1
        self.stats["average_response_time"] = (
            (self.stats["average_response_time"] * (self.stats["total_requests"] - 1) + response_time)
            / self.stats["total_requests"]
        )
        self.stats["total_tokens_generated"] += tokens
        
        if mode == "real":
            self.stats["real_streaming_requests"] += 1
        elif mode == "pseudo":
            self.stats["pseudo_streaming_requests"] += 1
        elif mode == "failed":
            self.stats["failed_requests"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "total_requests": 0,
            "real_streaming_requests": 0,
            "pseudo_streaming_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "total_tokens_generated": 0,
        }

# 全局监控实例
streaming_monitor = StreamingMonitor()
