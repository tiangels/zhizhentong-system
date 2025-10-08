#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能诊断服务启动脚本
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path

# 添加项目根目录到路径
current_file = Path(__file__)
project_root = current_file.parent.parent.parent  # 回到codes目录
sys.path.insert(0, str(project_root))

# 添加common模块到路径
common_dir = project_root / "common"
sys.path.insert(0, str(common_dir))

from common.log_config import setup_logging, get_logger
setup_logging("diagnosis_service")
logger = get_logger(__name__)

import uvicorn


def load_config(config_path: str = None) -> dict:
    """加载配置文件"""
    try:
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # 使用默认配置文件
        default_config_path = Path(__file__).parent / "config" / "diagnosis_config.json"
        if default_config_path.exists():
            with open(default_config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # 返回默认配置
        return {
            "api": {
                "host": "0.0.0.0",
                "port": 8003,
                "reload": False,
                "log_level": "info"
            }
        }
        
    except Exception as e:
        logger.warning(f"加载配置文件失败: {e}，使用默认配置")
        return {
            "api": {
                "host": "0.0.0.0",
                "port": 8003,
                "reload": False,
                "log_level": "info"
            }
        }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="启动智能诊断服务")
    parser.add_argument("--host", default="0.0.0.0", help="服务主机地址")
    parser.add_argument("--port", type=int, default=8003, help="服务端口")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--reload", action="store_true", help="启用热重载")
    parser.add_argument("--log-level", default="info", help="日志级别")
    
    args = parser.parse_args()
    
    # 加载配置
    config = load_config(args.config)
    api_config = config.get("api", {})
    
    # 使用命令行参数覆盖配置
    host = args.host or api_config.get("host", "0.0.0.0")
    port = args.port or api_config.get("port", 8003)
    reload = args.reload or api_config.get("reload", False)
    log_level = args.log_level or api_config.get("log_level", "info")
    
    logger.info("=" * 60)
    logger.info("🚀 启动智诊通智能诊断服务")
    logger.info("=" * 60)
    logger.info(f"服务地址: http://{host}:{port}")
    logger.info(f"API文档: http://{host}:{port}/diagnosis/docs")
    logger.info(f"健康检查: http://{host}:{port}/diagnosis/health")
    logger.info(f"热重载: {'启用' if reload else '禁用'}")
    logger.info(f"日志级别: {log_level}")
    logger.info("=" * 60)
    
    try:
        # 启动服务
        uvicorn.run(
            "api.diagnosis_api:app",
            host=host,
            port=port,
            reload=reload,
            log_level=log_level,
            access_log=True
        )
        
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭服务...")
    except Exception as e:
        logger.error(f"服务启动失败: {e}")
        sys.exit(1)
    finally:
        logger.info("智能诊断服务已关闭")


if __name__ == "__main__":
    main()
