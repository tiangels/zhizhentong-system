"""
智诊通系统配置文件
包含数据库、Redis、Milvus、认证等所有配置项
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基础配置
    APP_NAME: str = "智诊通-多模态智能医生问诊系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=True, env="DEBUG")
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    
    # 服务器配置
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    SERVER_HOST: str = Field(default="0.0.0.0", env="SERVER_HOST")
    SERVER_PORT: int = Field(default=8000, env="SERVER_PORT")
    
    # 数据库配置
    DATABASE_URL: str = Field(
        default="postgresql://zhizhentong:zhizhentong123@localhost:5432/zhizhentong",
        env="DATABASE_URL"
    )
    
    # Redis配置
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # Milvus向量数据库配置
    MILVUS_HOST: str = Field(default="localhost", env="MILVUS_HOST")
    MILVUS_PORT: int = Field(default=19530, env="MILVUS_PORT")
    MILVUS_COLLECTION_NAME: str = Field(default="medical_knowledge", env="MILVUS_COLLECTION_NAME")
    
    # RabbitMQ消息队列配置
    RABBITMQ_URL: str = Field(
        default="amqp://zhizhentong:zhizhentong123@localhost:5672/",
        env="RABBITMQ_URL"
    )
    
    # JWT认证配置
    SECRET_KEY: str = Field(
        default="your-secret-key-here-change-in-production",
        env="SECRET_KEY"
    )
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # CORS配置
    CORS_ORIGINS: list = Field(
        default=[
            "http://localhost:3000", 
            "http://localhost:8080", 
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8080",
            "null"  # 支持file://协议
        ],
        env="CORS_ORIGINS"
    )
    
    # 允许的主机配置
    ALLOWED_HOSTS: list = Field(
        default=["*"],
        env="ALLOWED_HOSTS"
    )
    
    # 文件上传配置
    UPLOAD_DIR: str = Field(default="./uploads", env="UPLOAD_DIR")
    MAX_FILE_SIZE: int = Field(default=10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB
    ALLOWED_FILE_TYPES: list = Field(
        default=["image/jpeg", "image/png", "image/gif", "audio/wav", "audio/mp3"],
        env="ALLOWED_FILE_TYPES"
    )
    
    # AI模型配置
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    OPENAI_BASE_URL: Optional[str] = Field(default=None, env="OPENAI_BASE_URL")
    CLAUDE_API_KEY: Optional[str] = Field(default=None, env="CLAUDE_API_KEY")
    WENXIN_API_KEY: Optional[str] = Field(default=None, env="WENXIN_API_KEY")
    WENXIN_SECRET_KEY: Optional[str] = Field(default=None, env="WENXIN_SECRET_KEY")
    
    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: str = Field(default="./logs/app.log", env="LOG_FILE")
    
    # 缓存配置
    CACHE_TTL: int = Field(default=3600, env="CACHE_TTL")  # 1小时
    CACHE_PREFIX: str = Field(default="zhizhentong:", env="CACHE_PREFIX")
    
    # 系统限制配置
    MAX_CONVERSATION_LENGTH: int = Field(default=1000, env="MAX_CONVERSATION_LENGTH")
    MAX_MESSAGE_LENGTH: int = Field(default=5000, env="MAX_MESSAGE_LENGTH")
    SESSION_TIMEOUT: int = Field(default=3600, env="SESSION_TIMEOUT")  # 1小时
    
    # 监控配置
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    METRICS_PORT: int = Field(default=9090, env="METRICS_PORT")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()

# 确保上传目录存在
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True)
