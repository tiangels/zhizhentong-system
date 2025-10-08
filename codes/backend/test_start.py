#!/usr/bin/env python3
"""
简单的后端服务测试
"""

import sys
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from app.main import app
    print("✅ 应用导入成功")
    
    import uvicorn
    print("🚀 启动后端服务...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
except Exception as e:
    print(f"❌ 启动失败: {e}")
    import traceback
    traceback.print_exc()
