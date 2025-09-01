"""
认证API路由
处理用户注册、登录、令牌刷新等认证相关功能
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from ..database import get_db
from ..auth import auth_manager, get_current_user
from ..models.user import (
    User, UserCreate, UserLogin, UserResponse, 
    UserLoginResponse, UserSessionCreate
)
from ..cache import set_cache, get_cache, delete_cache

router = APIRouter(prefix="/auth", tags=["认证"])

security = HTTPBearer()


@router.post("/register", response_model=UserResponse, summary="用户注册")
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    用户注册
    
    - **username**: 用户名（唯一）
    - **email**: 邮箱（唯一）
    - **password**: 密码
    - **full_name**: 全名（可选）
    - **phone**: 手机号（可选）
    """
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否已存在
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已存在"
        )
    
    # 创建新用户
    hashed_password = auth_manager.get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password,
        full_name=user_data.full_name,
        phone=user_data.phone
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UserResponse(
        id=str(new_user.id),
        username=new_user.username,
        email=new_user.email,
        full_name=new_user.full_name,
        phone=new_user.phone,
        avatar_url=new_user.avatar_url,
        is_active=new_user.is_active,
        is_verified=new_user.is_verified,
        created_at=new_user.created_at,
        updated_at=new_user.updated_at
    )


@router.post("/login", response_model=UserLoginResponse, summary="用户登录")
async def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    用户登录
    
    - **username**: 用户名或邮箱
    - **password**: 密码
    """
    print(f"=== 登录请求开始 ===")
    print(f"用户名/邮箱: {login_data.username}")
    print(f"密码长度: {len(login_data.password)}")
    
    # 验证用户
    user = auth_manager.authenticate_user(db, login_data.username, login_data.password)
    
    print(f"=== 用户验证结果 ===")
    if user:
        print(f"✅ 用户验证成功!")
        print(f"用户ID: {user.id}")
        print(f"用户名: {user.username}")
        print(f"邮箱: {user.email}")
        print(f"全名: {user.full_name}")
        print(f"手机号: {user.phone}")
        print(f"头像URL: {user.avatar_url}")
        print(f"是否激活: {user.is_active}")
        print(f"是否已验证: {user.is_verified}")
        print(f"创建时间: {user.created_at}")
        print(f"更新时间: {user.updated_at}")
        print(f"用户对象类型: {type(user)}")
        print(f"用户对象属性: {dir(user)}")
    else:
        print(f"❌ 用户验证失败!")
        print(f"可能的原因: 用户名不存在 或 密码错误")
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    if not user.is_active:
        print(f"❌ 用户已被禁用: {user.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户已被禁用"
        )
    
    print(f"=== 生成令牌 ===")
    # 生成访问令牌
    access_token_expires = timedelta(minutes=auth_manager.access_token_expire_minutes)
    access_token = auth_manager.create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    print(f"访问令牌: {access_token[:50]}...")
    
    # 生成刷新令牌
    refresh_token = auth_manager.create_refresh_token(
        data={"sub": str(user.id)}
    )
    print(f"刷新令牌: {refresh_token[:50]}...")
    
    print(f"=== 创建用户会话 ===")
    # 创建用户会话
    expires_at = datetime.utcnow() + timedelta(days=auth_manager.refresh_token_expire_days)
    session = auth_manager.create_user_session(
        db=db,
        user_id=str(user.id),
        refresh_token=refresh_token,
        expires_at=expires_at
    )
    print(f"会话ID: {session.id}")
    print(f"会话过期时间: {session.expires_at}")
    
    print(f"=== 缓存用户信息 ===")
    # 缓存用户信息
    cache_key = f"user:{user.id}"
    user_info = {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active
    }
    set_cache(cache_key, str(user_info), expire=3600)  # 缓存1小时
    print(f"缓存键: {cache_key}")
    print(f"缓存内容: {user_info}")
    
    print(f"=== 登录成功，返回响应 ===")
    response = UserLoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=auth_manager.access_token_expire_minutes * 60,
        user=UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            avatar_url=user.avatar_url,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    )
    print(f"响应用户信息: {response.user}")
    print(f"=== 登录请求结束 ===")
    
    return response


@router.post("/refresh", response_model=UserLoginResponse, summary="刷新令牌")
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    刷新访问令牌
    
    - **refresh_token**: 刷新令牌
    """
    # 验证刷新令牌
    payload = auth_manager.verify_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌"
        )
    
    # 获取用户信息
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用"
        )
    
    # 生成新的访问令牌
    access_token_expires = timedelta(minutes=auth_manager.access_token_expire_minutes)
    new_access_token = auth_manager.create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    
    # 生成新的刷新令牌
    new_refresh_token = auth_manager.create_refresh_token(
        data={"sub": str(user.id)}
    )
    
    return UserLoginResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=auth_manager.access_token_expire_minutes * 60,
        user=UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            avatar_url=user.avatar_url,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    )


@router.post("/logout", summary="用户登出")
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    credentials: HTTPBearer = Depends(security)
):
    """
    用户登出
    
    需要提供有效的访问令牌
    """
    # 删除用户会话
    auth_manager.delete_user_session(db, credentials.credentials)
    
    # 清除缓存
    cache_key = f"user:{current_user.id}"
    delete_cache(cache_key)
    
    return {"message": "登出成功"}


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户信息
    
    需要提供有效的访问令牌
    """
    return UserResponse(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        phone=current_user.phone,
        avatar_url=current_user.avatar_url,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )


@router.put("/me", response_model=UserResponse, summary="更新当前用户信息")
async def update_current_user_info(
    user_data: UserCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新当前用户信息
    
    需要提供有效的访问令牌
    """
    # 检查邮箱是否已被其他用户使用
    if user_data.email and user_data.email != current_user.email:
        existing_user = db.query(User).filter(
            User.email == user_data.email,
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被其他用户使用"
            )
    
    # 更新用户信息
    if user_data.email:
        current_user.email = user_data.email
    if user_data.full_name:
        current_user.full_name = user_data.full_name
    if user_data.phone:
        current_user.phone = user_data.phone
    if user_data.password:
        current_user.password_hash = auth_manager.get_password_hash(user_data.password)
    
    current_user.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(current_user)
    
    return UserResponse(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        phone=current_user.phone,
        avatar_url=current_user.avatar_url,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )
