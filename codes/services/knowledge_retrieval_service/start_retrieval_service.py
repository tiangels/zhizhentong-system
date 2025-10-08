#!/usr/bin/env python
"""
知识检索服务启动脚本
启动知识检索 API 服务
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from api.retrieval_api import app
import uvicorn

# 使用统一日志配置
import sys
from pathlib import Path

# 添加common模块到路径
current_file = Path(__file__)
common_dir = current_file.parent.parent.parent.parent / "common"
sys.path.insert(0, str(common_dir))

from common.log_config import setup_logging, get_logger
setup_logging("retrieval_service")
logger = get_logger(__name__)


def load_config(config_path: str = None) -> dict:
    """加载配置文件"""
    default_config = {
        "api": {
            "host": "0.0.0.0",
            "port": 8002,
            "reload": False,
            "log_level": "info"
        }
    }
    
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
            default_config.update(user_config)
            logger.info(f"Loaded config from {config_path}")
        except Exception as e:
            logger.warning(f"Error loading config: {e}, using default config")
    else:
        logger.info("Using default config")
    
    return default_config


def check_dependencies():
    """检查依赖项"""
    try:
        import torch
        import transformers
        import sentence_transformers
        import chromadb
        from langchain_chroma import Chroma
        from langchain_community.embeddings import HuggingFaceEmbeddings
        import fastapi
        import uvicorn
        logger.info("All dependencies are available")
        return True
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        return False


def check_model_paths(config: dict):
    """检查模型路径"""
    llm_config = config.get('llm_service', {})
    model_path = llm_config.get('model_path', 'FreedomIntelligence/Apollo-0.5B')
    
    if not os.path.exists(model_path):
        logger.warning(f"LLM model path does not exist: {model_path}")
        logger.warning("Please ensure the model is properly downloaded")
        return False
    
    logger.info(f"LLM model path verified: {model_path}")
    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Start Knowledge Retrieval Service")
    parser.add_argument(
        "--config", 
        type=str, 
        default="api/config/retrieval_config.json",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--host", 
        type=str, 
        default="0.0.0.0",
        help="Host to bind to"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8002,
        help="Port to bind to"
    )
    parser.add_argument(
        "--reload", 
        action="store_true",
        help="Enable auto-reload for development"
    )
    parser.add_argument(
        "--log-level", 
        type=str, 
        default="info",
        choices=["debug", "info", "warning", "error"],
        help="Log level"
    )
    
    args = parser.parse_args()
    
    # 加载配置
    config = load_config(args.config)
    
    # 检查依赖项
    if not check_dependencies():
        logger.error("Dependencies check failed. Please install required packages.")
        sys.exit(1)
    
    # 检查模型路径
    if not check_model_paths(config):
        logger.warning("Model path check failed. Service may not work properly.")
    
    # 获取API配置
    api_config = config.get('api', {})
    
    # 命令行参数覆盖配置文件
    host = args.host or api_config.get('host', '0.0.0.0')
    port = args.port or api_config.get('port', 8002)
    reload = args.reload or api_config.get('reload', False)
    log_level = args.log_level or api_config.get('log_level', 'info')
    
    logger.info(f"Starting retrieval service on {host}:{port}")
    logger.info(f"Reload enabled: {reload}")
    logger.info(f"Log level: {log_level}")
    
    try:
        # 配置uvicorn日志
        log_config = uvicorn.config.LOGGING_CONFIG
        log_config["version"] = 1
        log_config["disable_existing_loggers"] = False
        log_config["formatters"]["default"]["fmt"] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        log_config["formatters"]["access"]["fmt"] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        # 启动服务
        uvicorn.run(
            "api.retrieval_api:app",
            host=host,
            port=port,
            reload=reload,
            log_level=log_level,
            access_log=True,
            log_config=log_config,
            workers=1,
            loop="asyncio",
            limit_concurrency=100,
            limit_max_requests=1000,
            timeout_keep_alive=30,
            timeout_graceful_shutdown=30
        )
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
    except Exception as e:
        logger.error(f"Error starting service: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


