"""
智诊通统一日志配置系统
为所有服务提供统一的日志管理
"""

import os
import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime


class UnifiedLogManager:
    """统一日志管理器"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UnifiedLogManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._setup_unified_logging()
            UnifiedLogManager._initialized = True
    
    def _setup_unified_logging(self):
        """设置统一的日志配置"""
        # 获取项目根目录
        current_file = Path(__file__)
        self.project_root = current_file.parent.parent  # 回到codes目录
        self.log_dir = self.project_root / "logs"
        self.log_dir.mkdir(exist_ok=True)
        
        # 清除现有的根日志器配置
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(logging.INFO)
        
        # 创建统一的格式化器
        self.detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(funcName)s() - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        self.simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(self.simple_formatter)
        
        # 添加控制台处理器到根日志器
        root_logger.addHandler(console_handler)
        
        # 存储服务特定的日志文件
        self.service_log_files = {}
        
        # 打印系统信息
        self._print_system_info()
    
    def _print_system_info(self):
        """打印系统信息（只在初始化时打印一次）"""
        root_logger = logging.getLogger()
        root_logger.info("=" * 80)
        root_logger.info("🎯 智诊通统一日志系统启动")
        root_logger.info("=" * 80)
        root_logger.info(f"📁 项目根目录: {self.project_root}")
        root_logger.info(f"📁 日志目录: {self.log_dir}")
        root_logger.info("=" * 80)
    
    def setup_service_logging(self, service_name: str, log_level: int = logging.INFO, show_config_logs: bool = False) -> logging.Logger:
        """
        为特定服务设置日志记录
        
        Args:
            service_name: 服务名称
            log_level: 日志级别
            show_config_logs: 是否显示配置完成的日志
            
        Returns:
            配置好的logger实例
        """
        # 创建服务专用的logger
        logger = logging.getLogger(service_name)
        logger.setLevel(log_level)
        
        # 清除现有的handlers
        logger.handlers.clear()
        
        # 创建服务专用的日志文件
        # 后端服务使用统一的backend.log文件
        if service_name == "backend_service":
            log_file = self.log_dir / "backend.log"
        else:
            log_file = self.log_dir / f"{service_name}.log"
        self.service_log_files[service_name] = log_file
        
        # 创建文件处理器
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(self.detailed_formatter)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(self.simple_formatter)
        
        # 添加处理器
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        # 防止日志传播到根日志器（避免重复）
        logger.propagate = False
        
        # 只在需要时显示配置完成的日志
        if show_config_logs:
            logger.info(f"✅ {service_name} 服务日志配置完成")
            logger.info(f"📁 日志文件: {log_file}")
        
        return logger
    
    def get_logger(self, name: str) -> logging.Logger:
        """获取指定名称的logger"""
        return logging.getLogger(name)
    
    def get_project_root(self) -> Path:
        """获取项目根目录"""
        return self.project_root
    
    def get_log_dir(self) -> Path:
        """获取日志目录"""
        return self.log_dir
    
    def get_service_log_file(self, service_name: str) -> Optional[Path]:
        """获取服务的日志文件路径"""
        return self.service_log_files.get(service_name)


# 全局日志管理器实例
log_manager = UnifiedLogManager()


def setup_service_logging(service_name: str, log_level: int = logging.INFO, show_config_logs: bool = False) -> logging.Logger:
    """便捷函数：为服务设置日志记录"""
    return log_manager.setup_service_logging(service_name, log_level, show_config_logs)


def get_logger(name: str) -> logging.Logger:
    """便捷函数：获取logger"""
    return log_manager.get_logger(name)


def get_project_root() -> Path:
    """便捷函数：获取项目根目录"""
    return log_manager.get_project_root()


def get_log_dir() -> Path:
    """便捷函数：获取日志目录"""
    return log_manager.get_log_dir()


def get_log_file(service_name: str = "vectorization_service") -> Optional[Path]:
    """便捷函数：获取服务的日志文件路径"""
    return log_manager.get_service_log_file(service_name)


# 预定义的服务日志配置
def setup_rag_service_logging(show_config_logs: bool = False) -> logging.Logger:
    """设置RAG服务日志（兼容旧名，重定向到retrieval_service）"""
    return setup_service_logging("retrieval_service", show_config_logs=show_config_logs)


def setup_embedding_service_logging(show_config_logs: bool = False) -> logging.Logger:
    """设置向量化服务日志"""
    return setup_service_logging("embedding_service", show_config_logs=show_config_logs)


def setup_logging(service_name: str, show_config_logs: bool = False) -> logging.Logger:
    """设置服务日志 - 兼容旧接口"""
    return setup_service_logging(service_name, show_config_logs=show_config_logs)


def setup_backend_service_logging(show_config_logs: bool = False) -> logging.Logger:
    """设置后端服务日志"""
    return setup_service_logging("backend_service", show_config_logs=show_config_logs)


def setup_frontend_service_logging(show_config_logs: bool = False) -> logging.Logger:
    """设置前端服务日志"""
    return setup_service_logging("frontend_service", show_config_logs=show_config_logs)


# 后端服务专用日志函数
def log_request(method: str, path: str, user_id: Optional[str] = None, 
               request_data: Optional[dict] = None, duration: Optional[float] = None):
    """记录HTTP请求日志"""
    logger = get_logger("backend_service")
    log_data = {
        "type": "http_request",
        "method": method,
        "path": path,
        "user_id": user_id,
        "duration": f"{duration:.3f}s" if duration else None,
        "timestamp": datetime.now().isoformat()
    }
    
    if request_data:
        log_data["request_data"] = request_data
    
    logger.info(f"🌐 HTTP请求: {method} {path} - 用户: {user_id} - 耗时: {duration:.3f}s" if duration else f"🌐 HTTP请求: {method} {path} - 用户: {user_id}")


def log_response(status_code: int, response_data: Optional[dict] = None, 
                error: Optional[str] = None):
    """记录HTTP响应日志"""
    logger = get_logger("backend_service")
    log_data = {
        "type": "http_response",
        "status_code": status_code,
        "timestamp": datetime.now().isoformat()
    }
    
    if response_data:
        log_data["response_data"] = response_data
    
    if error:
        log_data["error"] = error
        logger.error(f"❌ HTTP响应错误: {status_code} - {error}")
    else:
        logger.info(f"✅ HTTP响应成功: {status_code}")


def log_rag_service_call(operation: str, input_data: dict, 
                       output_data: Optional[dict] = None, 
                       duration: Optional[float] = None,
                       success: bool = True, error: Optional[str] = None):
    """记录RAG服务调用日志"""
    logger = get_logger("backend_service")
    log_data = {
        "type": "rag_service_call",
        "operation": operation,
        "input_data": input_data,
        "output_data": output_data,
        "duration": f"{duration:.3f}s" if duration else None,
        "success": success,
        "timestamp": datetime.now().isoformat()
    }
    
    if error:
        log_data["error"] = error
    
    if success:
        logger.info(f"🤖 RAG服务调用: {operation} - 成功 - 耗时: {duration:.3f}s" if duration else f"🤖 RAG服务调用: {operation} - 成功")
    else:
        logger.error(f"❌ RAG服务调用失败: {operation} - {error}")


def log_database_operation(operation: str, table: str, 
                         record_id: Optional[str] = None,
                         duration: Optional[float] = None,
                         success: bool = True, error: Optional[str] = None):
    """记录数据库操作日志"""
    logger = get_logger("backend_service")
    log_data = {
        "type": "database_operation",
        "operation": operation,
        "table": table,
        "record_id": record_id,
        "duration": f"{duration:.3f}s" if duration else None,
        "success": success,
        "timestamp": datetime.now().isoformat()
    }
    
    if error:
        log_data["error"] = error
    
    if success:
        logger.info(f"🗄️ 数据库操作: {operation} {table} - 成功 - 耗时: {duration:.3f}s" if duration else f"🗄️ 数据库操作: {operation} {table} - 成功")
    else:
        logger.error(f"❌ 数据库操作失败: {operation} {table} - {error}")


def log_user_authentication(user_id: str, action: str, 
                          success: bool = True, error: Optional[str] = None):
    """记录用户认证日志"""
    logger = get_logger("backend_service")
    log_data = {
        "type": "user_authentication",
        "user_id": user_id,
        "action": action,
        "success": success,
        "timestamp": datetime.now().isoformat()
    }
    
    if error:
        log_data["error"] = error
    
    if success:
        logger.info(f"🔐 用户认证: {action} - 用户: {user_id} - 成功")
    else:
        logger.error(f"❌ 用户认证失败: {action} - 用户: {user_id} - {error}")


def log_conversation_processing(conversation_id: str, user_id: str,
                              message_count: int, processing_time: float,
                              rag_used: bool = False, success: bool = True):
    """记录对话处理日志"""
    logger = get_logger("backend_service")
    log_data = {
        "type": "conversation_processing",
        "conversation_id": conversation_id,
        "user_id": user_id,
        "message_count": message_count,
        "processing_time": f"{processing_time:.3f}s",
        "rag_used": rag_used,
        "success": success,
        "timestamp": datetime.now().isoformat()
    }
    
    if success:
        logger.info(f"💬 对话处理: 对话ID={conversation_id} - 用户={user_id} - 消息数={message_count} - RAG={'是' if rag_used else '否'} - 耗时={processing_time:.3f}s")
    else:
        logger.error(f"❌ 对话处理失败: 对话ID={conversation_id} - 用户={user_id}")


def log_system_event(event: str, details: Optional[dict] = None, 
                    level: str = "INFO"):
    """记录系统事件日志"""
    logger = get_logger("backend_service")
    log_data = {
        "type": "system_event",
        "event": event,
        "details": details,
        "timestamp": datetime.now().isoformat()
    }
    
    if level.upper() == "ERROR":
        logger.error(f"🚨 系统事件: {event}")
    elif level.upper() == "WARNING":
        logger.warning(f"⚠️ 系统事件: {event}")
    else:
        logger.info(f"ℹ️ 系统事件: {event}")


def log_performance_metrics(operation: str, metrics: dict):
    """记录性能指标日志"""
    logger = get_logger("backend_service")
    log_data = {
        "type": "performance_metrics",
        "operation": operation,
        "metrics": metrics,
        "timestamp": datetime.now().isoformat()
    }
    
    logger.info(f"📊 性能指标: {operation} - {metrics}")


# 后端服务日志记录器类
class BackendServiceLogger:
    """后端服务专用日志记录器"""
    
    def __init__(self, log_file: str = None):
        """初始化后端服务日志记录器"""
        self.logger = get_logger("backend_service")
    
    def log_request(self, method: str, path: str, user_id: Optional[str] = None, 
                   request_data: Optional[dict] = None, duration: Optional[float] = None):
        """记录HTTP请求日志"""
        log_request(method, path, user_id, request_data, duration)
    
    def log_response(self, status_code: int, response_data: Optional[dict] = None, 
                    error: Optional[str] = None):
        """记录HTTP响应日志"""
        log_response(status_code, response_data, error)
    
    def log_rag_service_call(self, operation: str, input_data: dict, 
                           output_data: Optional[dict] = None, 
                           duration: Optional[float] = None,
                           success: bool = True, error: Optional[str] = None):
        """记录RAG服务调用日志"""
        log_rag_service_call(operation, input_data, output_data, duration, success, error)
    
    def log_database_operation(self, operation: str, table: str, 
                             record_id: Optional[str] = None,
                             duration: Optional[float] = None,
                             success: bool = True, error: Optional[str] = None):
        """记录数据库操作日志"""
        log_database_operation(operation, table, record_id, duration, success, error)
    
    def log_user_authentication(self, user_id: str, action: str, 
                              success: bool = True, error: Optional[str] = None):
        """记录用户认证日志"""
        log_user_authentication(user_id, action, success, error)
    
    def log_conversation_processing(self, conversation_id: str, user_id: str,
                                  message_count: int, processing_time: float,
                                  rag_used: bool = False, success: bool = True):
        """记录对话处理日志"""
        log_conversation_processing(conversation_id, user_id, message_count, processing_time, rag_used, success)
    
    def log_system_event(self, event: str, details: Optional[dict] = None, 
                        level: str = "INFO"):
        """记录系统事件日志"""
        log_system_event(event, details, level)
    
    def log_performance_metrics(self, operation: str, metrics: dict):
        """记录性能指标日志"""
        log_performance_metrics(operation, metrics)


# 创建全局后端服务日志记录器实例
backend_service_logger = BackendServiceLogger()


def get_backend_logger() -> BackendServiceLogger:
    """获取后端服务日志记录器实例"""
    return backend_service_logger
