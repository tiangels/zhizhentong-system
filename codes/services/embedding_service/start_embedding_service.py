#!/usr/bin/env python3
"""
智诊通向量化服务启动脚本
"""

import sys
import os
import asyncio
import uvicorn
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "codes" / "services" / "embedding_service"))

# 导入API应用
from api.embedding_api import app

def main():
    """启动向量化服务"""
    print("🚀 启动智诊通向量化服务...")
    print("📍 服务地址: http://localhost:8001")
    print("📖 API文档: http://localhost:8001/docs")
    print("🔧 管理界面: http://localhost:8001/redoc")
    print("=" * 50)
    
    try:
        # 启动服务
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8001,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 向量化服务已停止")
    except Exception as e:
        print(f"❌ 服务启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
