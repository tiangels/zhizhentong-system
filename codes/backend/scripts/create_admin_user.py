#!/usr/bin/env python3
"""
创建默认管理员用户脚本
用于在系统初始化时创建默认的admin用户
"""

import sys
import os
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database import get_db_context
from app.auth import AuthManager
from app.models.user import User
from sqlalchemy.orm import Session

async def create_admin_user():
    """创建默认管理员用户"""
    print("🚀 开始创建默认管理员用户...")
    
    # 创建认证管理器
    auth_manager = AuthManager()
    
    # 管理员用户信息
    admin_data = {
        "username": "admin",
        "email": "admin@zhizhentong.com",
        "password": "admin123",
        "full_name": "系统管理员",
        "phone": "13800138000"
    }
    
    try:
        with get_db_context() as db:
            # 检查admin用户是否已存在
            existing_user = db.query(User).filter(
                (User.username == admin_data["username"]) | 
                (User.email == admin_data["email"])
            ).first()
            
            if existing_user:
                print(f"⚠️  管理员用户已存在: {existing_user.username}")
                print(f"   用户ID: {existing_user.id}")
                print(f"   邮箱: {existing_user.email}")
                print(f"   是否激活: {existing_user.is_active}")
                return existing_user
            
            # 创建新用户
            print(f"📝 创建新管理员用户...")
            print(f"   用户名: {admin_data['username']}")
            print(f"   邮箱: {admin_data['email']}")
            print(f"   全名: {admin_data['full_name']}")
            print(f"   手机号: {admin_data['phone']}")
            
            # 生成密码哈希
            password_hash = auth_manager.get_password_hash(admin_data["password"])
            print(f"   密码哈希: {password_hash[:20]}...")
            
            # 创建用户对象
            new_user = User(
                username=admin_data["username"],
                email=admin_data["email"],
                password_hash=password_hash,
                full_name=admin_data["full_name"],
                phone=admin_data["phone"],
                is_active=True,
                is_verified=True
            )
            
            # 保存到数据库
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            print(f"✅ 管理员用户创建成功!")
            print(f"   用户ID: {new_user.id}")
            print(f"   用户名: {new_user.username}")
            print(f"   邮箱: {new_user.email}")
            print(f"   全名: {new_user.full_name}")
            print(f"   手机号: {new_user.phone}")
            print(f"   是否激活: {new_user.is_active}")
            print(f"   是否已验证: {new_user.is_verified}")
            print(f"   创建时间: {new_user.created_at}")
            
            # 测试登录
            print(f"\n🔐 测试管理员用户登录...")
            test_user = auth_manager.authenticate_user(
                db, admin_data["username"], admin_data["password"]
            )
            
            if test_user:
                print(f"✅ 登录测试成功!")
                print(f"   验证的用户: {test_user.username}")
            else:
                print(f"❌ 登录测试失败!")
            
            return new_user
            
    except Exception as e:
        print(f"❌ 创建管理员用户失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """主函数"""
    print("=" * 60)
    print("🏥 智诊通系统 - 创建默认管理员用户")
    print("=" * 60)
    
    admin_user = await create_admin_user()
    
    if admin_user:
        print("\n" + "=" * 60)
        print("🎉 管理员用户创建完成!")
        print("=" * 60)
        print("📋 登录信息:")
        print(f"   用户名: admin")
        print(f"   密码: admin123")
        print(f"   邮箱: admin@zhizhentong.com")
        print("\n🌐 测试登录:")
        print("   1. 访问调试页面: http://localhost:3000/debug-multimodal.html")
        print("   2. 使用上述凭据登录")
        print("   3. 测试多模态功能")
    else:
        print("\n❌ 管理员用户创建失败!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
