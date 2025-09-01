"""
系统管理API路由
处理系统配置、用户偏好、操作日志等
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..auth import get_current_user
from ..models.user import User
from ..models.config import SystemConfig, SystemConfigCreate, SystemConfigResponse
from ..models.preference import UserPreference, UserPreferenceCreate, UserPreferenceUpdate, UserPreferenceResponse
from ..models.log import (
    OperationLog, OperationLogCreate, OperationLogResponse
)

router = APIRouter(prefix="/system", tags=["系统管理"])


# ==================== 系统配置管理 ====================

@router.get("/config", response_model=List[SystemConfigResponse], summary="获取系统配置列表")
async def get_system_configs(
    category: Optional[str] = Query(None, description="配置分类"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取系统配置列表
    
    - **category**: 配置分类过滤（可选）
    """
    query = db.query(SystemConfig)
    
    if category:
        query = query.filter(SystemConfig.config_type == category)
    
    configs = query.all()
    
    return [
        SystemConfigResponse(
            id=config.id,
            config_key=config.config_key,
            config_value=config.config_value,
            config_type=config.config_type,
            description=config.description,
            is_active=config.is_active,
            created_at=config.created_at,
            updated_at=config.updated_at
        )
        for config in configs
    ]


@router.get("/config/{config_key}", response_model=SystemConfigResponse, summary="获取系统配置详情")
async def get_system_config(
    config_key: str,
    db: Session = Depends(get_db)
):
    """
    获取指定系统配置详情
    
    - **config_key**: 配置键名
    """
    config = db.query(SystemConfig).filter(SystemConfig.config_key == config_key).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="系统配置不存在"
        )
    
    return SystemConfigResponse(
        id=config.id,
        config_key=config.config_key,
        config_value=config.config_value,
        config_type=config.config_type,
        description=config.description,
        is_active=config.is_active,
        created_at=config.created_at,
        updated_at=config.updated_at
    )


@router.post("/config", response_model=SystemConfigResponse, summary="创建系统配置")
async def create_system_config(
    config_data: SystemConfigCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建新的系统配置
    
    - **key**: 配置键名
    - **value**: 配置值
    - **category**: 配置分类
    - **description**: 配置描述
    - **is_active**: 是否激活
    """
    # 检查配置键是否已存在
    existing_config = db.query(SystemConfig).filter(SystemConfig.config_key == config_data.config_key).first()
    if existing_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="配置键已存在"
        )
    
    new_config = SystemConfig(
        config_key=config_data.config_key,
        config_value=config_data.config_value,
        config_type=config_data.config_type,
        description=config_data.description,
        is_active=config_data.is_active
    )
    
    db.add(new_config)
    db.commit()
    db.refresh(new_config)
    
    return SystemConfigResponse(
        id=new_config.id,
        config_key=new_config.config_key,
        config_value=new_config.config_value,
        config_type=new_config.config_type,
        description=new_config.description,
        is_active=new_config.is_active,
        created_at=new_config.created_at,
        updated_at=new_config.updated_at
    )


@router.put("/config/{config_key}", response_model=SystemConfigResponse, summary="更新系统配置")
async def update_system_config(
    config_key: str,
    config_data: SystemConfigCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新系统配置
    
    - **config_key**: 配置键名
    - **value**: 新配置值
    - **category**: 新分类
    - **description**: 新描述
    - **is_active**: 新激活状态
    """
    config = db.query(SystemConfig).filter(SystemConfig.config_key == config_key).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="系统配置不存在"
        )
    
    # 更新字段
    if config_data.config_value is not None:
        config.config_value = config_data.config_value
    if config_data.config_type is not None:
        config.config_type = config_data.config_type
    if config_data.description is not None:
        config.description = config_data.description
    if config_data.is_active is not None:
        config.is_active = config_data.is_active
    
    db.commit()
    db.refresh(config)
    
    return SystemConfigResponse(
        id=config.id,
        config_key=config.config_key,
        config_value=config.config_value,
        config_type=config.config_type,
        description=config.description,
        is_active=config.is_active,
        created_at=config.created_at,
        updated_at=config.updated_at
    )


@router.delete("/config/{config_key}", summary="删除系统配置")
async def delete_system_config(
    config_key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除系统配置
    
    - **config_key**: 配置键名
    """
    config = db.query(SystemConfig).filter(SystemConfig.config_key == config_key).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="系统配置不存在"
        )
    
    db.delete(config)
    db.commit()
    
    return {"message": "系统配置删除成功"}


# ==================== 用户偏好管理 ====================

@router.get("/preferences/{user_id}", response_model=UserPreferenceResponse, summary="获取用户偏好")
async def get_user_preferences(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户偏好设置
    
    - **user_id**: 用户ID
    """
    # 检查权限
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问其他用户的偏好设置"
        )
    
    preference = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    
    if not preference:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户偏好不存在"
        )
    
    return UserPreferenceResponse(
        id=preference.id,
        user_id=preference.user_id,
        theme=preference.theme,
        language=preference.language,
        notification_enabled=preference.notification_enabled,
        email_notification=preference.email_notification,
        push_notification=preference.push_notification,
        privacy_level=preference.privacy_level,
        ai_model_preference=preference.ai_model_preference,
        settings=preference.settings,
        created_at=preference.created_at,
        updated_at=preference.updated_at
    )


@router.post("/preferences/{user_id}", response_model=UserPreferenceResponse, summary="创建用户偏好")
async def create_user_preference(
    user_id: int,
    preference_data: UserPreferenceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建用户偏好设置
    
    - **user_id**: 用户ID
    """
    # 检查权限
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权为其他用户创建偏好设置"
        )
    
    # 检查偏好是否已存在
    existing_pref = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    
    if existing_pref:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户偏好已存在"
        )
    
    new_preference = UserPreference(
        user_id=user_id,
        theme=preference_data.theme,
        language=preference_data.language,
        notification_enabled=preference_data.notification_enabled,
        email_notification=preference_data.email_notification,
        push_notification=preference_data.push_notification,
        privacy_level=preference_data.privacy_level,
        ai_model_preference=preference_data.ai_model_preference,
        settings=preference_data.settings
    )
    
    db.add(new_preference)
    db.commit()
    db.refresh(new_preference)
    
    return UserPreferenceResponse(
        id=new_preference.id,
        user_id=new_preference.user_id,
        theme=new_preference.theme,
        language=new_preference.language,
        notification_enabled=new_preference.notification_enabled,
        email_notification=new_preference.email_notification,
        push_notification=new_preference.push_notification,
        privacy_level=new_preference.privacy_level,
        ai_model_preference=new_preference.ai_model_preference,
        settings=new_preference.settings,
        created_at=new_preference.created_at,
        updated_at=new_preference.updated_at
    )


@router.put("/preferences/{user_id}", response_model=UserPreferenceResponse, summary="更新用户偏好")
async def update_user_preference(
    user_id: int,
    preference_data: UserPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新用户偏好设置
    
    - **user_id**: 用户ID
    """
    # 检查权限
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权更新其他用户的偏好设置"
        )
    
    preference = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    
    if not preference:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户偏好不存在"
        )
    
    # 更新字段
    if preference_data.theme is not None:
        preference.theme = preference_data.theme
    if preference_data.language is not None:
        preference.language = preference_data.language
    if preference_data.notification_enabled is not None:
        preference.notification_enabled = preference_data.notification_enabled
    if preference_data.email_notification is not None:
        preference.email_notification = preference_data.email_notification
    if preference_data.push_notification is not None:
        preference.push_notification = preference_data.push_notification
    if preference_data.privacy_level is not None:
        preference.privacy_level = preference_data.privacy_level
    if preference_data.ai_model_preference is not None:
        preference.ai_model_preference = preference_data.ai_model_preference
    if preference_data.settings is not None:
        preference.settings = preference_data.settings
    
    db.commit()
    db.refresh(preference)
    
    return UserPreferenceResponse(
        id=preference.id,
        user_id=preference.user_id,
        theme=preference.theme,
        language=preference.language,
        notification_enabled=preference.notification_enabled,
        email_notification=preference.email_notification,
        push_notification=preference.push_notification,
        privacy_level=preference.privacy_level,
        ai_model_preference=preference.ai_model_preference,
        settings=preference.settings,
        created_at=preference.created_at,
        updated_at=preference.updated_at
    )


@router.delete("/preferences/{user_id}", summary="删除用户偏好")
async def delete_user_preference(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除用户偏好设置
    
    - **user_id**: 用户ID
    """
    # 检查权限
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除其他用户的偏好设置"
        )
    
    preference = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    
    if not preference:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户偏好不存在"
        )
    
    db.delete(preference)
    db.commit()
    
    return {"message": "用户偏好删除成功"}


# ==================== 操作日志管理 ====================

@router.get("/logs", response_model=List[OperationLogResponse], summary="获取操作日志")
async def get_operation_logs(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回记录数"),
    user_id: Optional[str] = Query(None, description="用户ID过滤"),
    operation: Optional[str] = Query(None, description="操作类型过滤"),
    resource_type: Optional[str] = Query(None, description="资源类型过滤"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取操作日志列表
    
    - **skip**: 跳过记录数
    - **limit**: 返回记录数
    - **user_id**: 用户ID过滤（可选）
    - **operation**: 操作类型过滤（可选）
    - **resource_type**: 资源类型过滤（可选）
    """
    query = db.query(OperationLog)
    
    # 添加过滤条件
    if user_id:
        query = query.filter(OperationLog.user_id == user_id)
    if operation:
        query = query.filter(OperationLog.operation == operation)
    if resource_type:
        query = query.filter(OperationLog.resource_type == resource_type)
    
    logs = query.order_by(OperationLog.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        OperationLogResponse(
            id=str(log.id),
            user_id=str(log.user_id) if log.user_id else None,
            operation=log.operation,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            details=log.details or {},
            ip_address=str(log.ip_address) if log.ip_address else None,
            user_agent=log.user_agent,
            created_at=log.created_at
        )
        for log in logs
    ]


@router.get("/logs/{log_id}", response_model=OperationLogResponse, summary="获取操作日志详情")
async def get_operation_log(
    log_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取指定操作日志详情
    
    - **log_id**: 日志ID
    """
    log = db.query(OperationLog).filter(OperationLog.id == log_id).first()
    
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="操作日志不存在"
        )
    
    return OperationLogResponse(
        id=str(log.id),
        user_id=str(log.user_id) if log.user_id else None,
        operation=log.operation,
        resource_type=log.resource_type,
        resource_id=log.resource_id,
        details=log.details or {},
        ip_address=str(log.ip_address) if log.ip_address else None,
        user_agent=log.user_agent,
        created_at=log.created_at
    )


@router.post("/logs", response_model=OperationLogResponse, summary="创建操作日志")
async def create_operation_log(
    log_data: OperationLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建操作日志
    
    - **user_id**: 用户ID
    - **operation**: 操作类型
    - **resource_type**: 资源类型
    - **resource_id**: 资源ID
    - **details**: 操作详情
    - **ip_address**: IP地址
    - **user_agent**: 用户代理
    """
    new_log = OperationLog(
        user_id=log_data.user_id,
        operation=log_data.operation,
        resource_type=log_data.resource_type,
        resource_id=log_data.resource_id,
        details=log_data.details,
        ip_address=log_data.ip_address,
        user_agent=log_data.user_agent
    )
    
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    
    return OperationLogResponse(
        id=str(new_log.id),
        user_id=str(new_log.user_id) if new_log.user_id else None,
        operation=new_log.operation,
        resource_type=new_log.resource_type,
        resource_id=new_log.resource_id,
        details=new_log.details or {},
        ip_address=str(new_log.ip_address) if new_log.ip_address else None,
        user_agent=new_log.user_agent,
        created_at=new_log.created_at
    )


# ==================== 系统统计信息 ====================

@router.get("/stats/overview", summary="获取系统概览统计")
async def get_system_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取系统概览统计信息
    """
    # 统计用户数量
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    
    # 统计系统配置数量
    total_configs = db.query(SystemConfig).count()
    active_configs = db.query(SystemConfig).filter(SystemConfig.is_active == True).count()
    
    # 统计操作日志数量
    total_logs = db.query(OperationLog).count()
    
    # 统计用户偏好数量
    total_preferences = db.query(UserPreference).count()
    
    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "inactive": total_users - active_users
        },
        "configs": {
            "total": total_configs,
            "active": active_configs,
            "inactive": total_configs - active_configs
        },
        "logs": {
            "total": total_logs
        },
        "preferences": {
            "total": total_preferences
        }
    }


@router.get("/stats/logs/operation-types", summary="获取操作类型统计")
async def get_operation_type_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取操作类型统计信息
    """
    # 统计各种操作类型的数量
    operation_stats = db.query(
        OperationLog.operation,
        db.func.count(OperationLog.id)
    ).group_by(OperationLog.operation).all()
    
    return {
        "operation_types": dict(operation_stats),
        "total_operations": sum(count for _, count in operation_stats)
    }


@router.get("/stats/logs/resource-types", summary="获取资源类型统计")
async def get_resource_type_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取资源类型统计信息
    """
    # 统计各种资源类型的数量
    resource_stats = db.query(
        OperationLog.resource_type,
        db.func.count(OperationLog.id)
    ).group_by(OperationLog.resource_type).all()
    
    return {
        "resource_types": dict(resource_stats),
        "total_resources": sum(count for _, count in resource_stats)
    }
