"""
认证管理模块
处理JWT令牌、用户认证、密码哈希等功能
"""

from datetime import datetime, timedelta
from typing import Optional, Union
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from .database import get_db
from .models.user import User, UserSession
from .config import settings

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer认证
security = HTTPBearer()


class AuthManager:
    """认证管理器"""
    
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """生成密码哈希"""
        return pwd_context.hash(password)
    
    def authenticate_user(self, db: Session, username: str, password: str) -> Optional[User]:
        """验证用户"""
        print(f"=== 开始验证用户 ===")
        print(f"输入的用户名/邮箱/手机号: {username}")
        
        # 支持用户名、邮箱或手机号登录
        user = db.query(User).filter(
            (User.username == username) | 
            (User.email == username) | 
            (User.phone == username)
        ).first()
        
        print(f"数据库查询结果: {user}")
        
        if not user:
            print(f"❌ 未找到用户: {username}")
            return None
        
        print(f"✅ 找到用户: {user.username}")
        print(f"用户密码哈希: {user.password_hash[:20]}...")
        
        # 验证密码
        password_valid = self.verify_password(password, user.password_hash)
        print(f"密码验证结果: {'✅ 正确' if password_valid else '❌ 错误'}")
        
        if not password_valid:
            print(f"❌ 密码验证失败")
            return None
        
        print(f"✅ 用户验证成功: {user.username}")
        return user
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: dict) -> str:
        """创建刷新令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> dict:
        """验证令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def create_user_session(self, db: Session, user_id: str, refresh_token: str, expires_at: datetime) -> UserSession:
        """创建用户会话"""
        session = UserSession(
            user_id=user_id,
            session_token=refresh_token,
            expires_at=expires_at.isoformat() if isinstance(expires_at, datetime) else expires_at
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
    
    def delete_user_session(self, db: Session, access_token: str) -> bool:
        """删除用户会话"""
        try:
            payload = self.verify_token(access_token)
            user_id = payload.get("sub")
            
            if user_id:
                # 删除该用户的所有会话
                db.query(UserSession).filter(UserSession.user_id == user_id).delete()
                db.commit()
                return True
        except:
            pass
        
        return False


# 创建全局认证管理器实例
auth_manager = AuthManager()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """获取当前用户"""
    try:
        payload = auth_manager.verify_token(credentials.credentials)
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 检查令牌类型
        token_type = payload.get("type")
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌类型错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 获取用户信息
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户已被禁用",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户已被禁用"
        )
    return current_user


def create_tokens(user_id: str, username: str) -> dict:
    """创建访问令牌和刷新令牌"""
    access_token_expires = timedelta(minutes=auth_manager.access_token_expire_minutes)
    access_token = auth_manager.create_access_token(
        data={"sub": user_id, "username": username},
        expires_delta=access_token_expires
    )
    
    refresh_token = auth_manager.create_refresh_token(
        data={"sub": user_id, "username": username}
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": auth_manager.access_token_expire_minutes * 60
    }
