"""
数据库连接和会话管理
配置SQLAlchemy数据库连接和会话
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator
from .config import settings

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.DEBUG,  # 在调试模式下打印SQL语句
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话的依赖函数
    用于FastAPI的依赖注入
"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.debug(f"🔗 创建新的数据库会话...")
    db = SessionLocal()
    try:
        logger.debug(f"✅ 数据库会话创建成功")
        yield db
    finally:
        logger.debug(f"🔒 关闭数据库会话...")
        db.close()
        logger.debug(f"✅ 数据库会话已关闭")


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    获取数据库会话的上下文管理器
    用于手动管理数据库会话
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.debug(f"🔗 创建数据库上下文会话...")
    db = SessionLocal()
    try:
        logger.debug(f"✅ 数据库上下文会话创建成功")
        yield db
        logger.debug(f"💾 提交数据库事务...")
        db.commit()
        logger.debug(f"✅ 数据库事务提交成功")
    except Exception as e:
        logger.error(f"❌ 数据库操作失败，开始回滚: {e}")
        db.rollback()
        logger.error(f"🔄 数据库事务已回滚")
        raise
    finally:
        logger.debug(f"🔒 关闭数据库上下文会话...")
        db.close()
        logger.debug(f"✅ 数据库上下文会话已关闭")


async def create_tables():
    """创建所有数据库表"""
    from .models import (
        User, UserSession, Conversation, Message, 
        Diagnosis, MedicalKnowledge, UserPreference, 
        SystemConfig, OperationLog, MultimodalInput, MultimodalOutput
    )
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """删除所有数据库表"""
    Base.metadata.drop_all(bind=engine)


def check_database_connection() -> bool:
    """检查数据库连接是否正常"""
    try:
        with get_db_context() as db:
            from sqlalchemy import text
            db.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return False
