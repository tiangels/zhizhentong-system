"""
智诊通服务路径设置模块
为各个服务提供统一的路径管理和模块导入支持
"""

import sys
import os
from pathlib import Path

def setup_project_paths():
    """
    设置项目路径，确保各个服务能够正确导入common模块
    """
    # 获取当前文件的目录
    current_dir = Path(__file__).parent
    
    # 获取项目根目录 (codes目录)
    project_root = current_dir.parent
    
    # 将项目根目录添加到Python路径
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    return project_root

def get_common_log_config():
    """
    获取common模块的log_config
    这样各个服务就不需要复制log_config.py文件了
    """
    # 确保路径设置正确
    project_root = setup_project_paths()
    
    # 导入common模块的log_config
    try:
        from common.log_config import (
            setup_service_logging, 
            get_logger, 
            setup_logging,
            log_manager
        )
        return {
            'setup_service_logging': setup_service_logging,
            'get_logger': get_logger,
            'setup_logging': setup_logging,
            'log_manager': log_manager
        }
    except ImportError as e:
        print(f"❌ 无法导入common.log_config: {e}")
        print(f"📁 项目根目录: {project_root}")
        print(f"📁 当前工作目录: {os.getcwd()}")
        print(f"🐍 Python路径: {sys.path[:3]}...")
        raise

# 自动设置路径
setup_project_paths()
