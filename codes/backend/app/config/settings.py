"""
智诊通系统配置管理
"""

import os
from typing import List, Optional
from pydantic import validator
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """系统配置类"""
    
    # 基础配置
    PROJECT_NAME: str = "智诊通-多模态智能医生问诊系统"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "基于AI技术的智能医疗问诊系统"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # 服务器配置
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    
    # 数据库配置
    DATABASE_URL: str = "postgresql://zhizhentong:zhizhentong123@localhost:5432/zhizhentong"
    
    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ]
    
    # 可信主机配置
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "0.0.0.0"]
    
    # 文件上传配置
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_DIR: str = "uploads"
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/backend.log"
    
    # Milvus向量数据库配置
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION_NAME: str = "medical_knowledge"
    
    # AI模型配置
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    
    # 检索服务配置
    RETRIEVAL_SERVICE_URL: str = "http://localhost:8002"
    
    # 智能诊断服务配置
    DIAGNOSIS_SERVICE_URL: str = "http://localhost:8003"
    
    # 其他配置
    TIMEZONE: str = "Asia/Shanghai"
    
    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @validator("ALLOWED_HOSTS", pre=True)
    def assemble_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """获取配置实例（单例模式）"""
    return Settings()


# 创建全局配置实例
settings = get_settings()
