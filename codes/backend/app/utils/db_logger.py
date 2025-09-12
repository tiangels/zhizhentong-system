"""
数据库操作日志记录工具
为数据库操作提供统一的日志记录功能
"""

import logging
import time
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


def log_db_operation(operation_name: str = None):
    """
    数据库操作日志装饰器
    
    Args:
        operation_name: 操作名称，如果不提供则使用函数名
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation_name or func.__name__
            start_time = time.time()
            
            logger.info(f"🗄️ 开始数据库操作: {op_name}")
            logger.debug(f"📋 操作参数: args={len(args)}, kwargs={list(kwargs.keys())}")
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.info(f"✅ 数据库操作成功: {op_name}")
                logger.info(f"⏱️ 操作耗时: {duration:.3f}秒")
                
                # 记录结果统计
                if isinstance(result, list):
                    logger.info(f"📊 返回结果: {len(result)} 条记录")
                elif isinstance(result, dict):
                    logger.info(f"📊 返回结果: {len(result)} 个字段")
                elif result is not None:
                    logger.info(f"📊 返回结果: {type(result).__name__}")
                else:
                    logger.info(f"📊 返回结果: None")
                
                return result
                
            except SQLAlchemyError as e:
                duration = time.time() - start_time
                logger.error(f"❌ 数据库操作失败: {op_name}")
                logger.error(f"🔍 错误类型: {type(e).__name__}")
                logger.error(f"📋 错误详情: {str(e)}")
                logger.error(f"⏱️ 失败前耗时: {duration:.3f}秒")
                raise
                
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"❌ 数据库操作异常: {op_name}")
                logger.error(f"🔍 错误类型: {type(e).__name__}")
                logger.error(f"📋 错误详情: {str(e)}")
                logger.error(f"⏱️ 异常前耗时: {duration:.3f}秒")
                raise
                
        return wrapper
    return decorator


def log_query_execution(query_type: str, table_name: str = None):
    """
    查询执行日志装饰器
    
    Args:
        query_type: 查询类型 (SELECT, INSERT, UPDATE, DELETE)
        table_name: 表名
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            table_info = f"表 {table_name}" if table_name else "未知表"
            logger.info(f"🔍 执行{query_type}查询: {table_info}")
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.info(f"✅ {query_type}查询成功: {table_info}")
                logger.info(f"⏱️ 查询耗时: {duration:.3f}秒")
                
                if hasattr(result, '__len__'):
                    logger.info(f"📊 查询结果: {len(result)} 条记录")
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"❌ {query_type}查询失败: {table_info}")
                logger.error(f"🔍 错误: {str(e)}")
                logger.error(f"⏱️ 失败前耗时: {duration:.3f}秒")
                raise
                
        return wrapper
    return decorator


def log_transaction_operation(operation: str):
    """
    事务操作日志装饰器
    
    Args:
        operation: 操作类型 (COMMIT, ROLLBACK, BEGIN)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.info(f"🔄 开始事务操作: {operation}")
            
            try:
                result = func(*args, **kwargs)
                logger.info(f"✅ 事务操作成功: {operation}")
                return result
                
            except Exception as e:
                logger.error(f"❌ 事务操作失败: {operation}")
                logger.error(f"🔍 错误: {str(e)}")
                raise
                
        return wrapper
    return decorator


class DatabaseLogger:
    """数据库操作日志记录器"""
    
    @staticmethod
    def log_query(db: Session, query_type: str, table_name: str, 
                  filters: Dict = None, result_count: int = None):
        """记录查询操作"""
        filter_info = f", 过滤条件: {filters}" if filters else ""
        count_info = f", 结果数: {result_count}" if result_count is not None else ""
        logger.info(f"🔍 执行{query_type}查询: 表 {table_name}{filter_info}{count_info}")
    
    @staticmethod
    def log_insert(db: Session, table_name: str, record_count: int = 1):
        """记录插入操作"""
        logger.info(f"➕ 插入记录: 表 {table_name}, 数量: {record_count}")
    
    @staticmethod
    def log_update(db: Session, table_name: str, record_count: int = 1, 
                   filters: Dict = None):
        """记录更新操作"""
        filter_info = f", 过滤条件: {filters}" if filters else ""
        logger.info(f"✏️ 更新记录: 表 {table_name}, 数量: {record_count}{filter_info}")
    
    @staticmethod
    def log_delete(db: Session, table_name: str, record_count: int = 1, 
                   filters: Dict = None):
        """记录删除操作"""
        filter_info = f", 过滤条件: {filters}" if filters else ""
        logger.info(f"🗑️ 删除记录: 表 {table_name}, 数量: {record_count}{filter_info}")
    
    @staticmethod
    def log_commit(db: Session, operation_count: int = 1):
        """记录提交操作"""
        logger.info(f"💾 提交事务: {operation_count} 个操作")
    
    @staticmethod
    def log_rollback(db: Session, reason: str = None):
        """记录回滚操作"""
        reason_info = f", 原因: {reason}" if reason else ""
        logger.warning(f"🔄 回滚事务{reason_info}")
    
    @staticmethod
    def log_refresh(db: Session, table_name: str, record_count: int = 1):
        """记录刷新操作"""
        logger.debug(f"🔄 刷新记录: 表 {table_name}, 数量: {record_count}")


# 创建全局数据库日志记录器实例
db_logger = DatabaseLogger()
