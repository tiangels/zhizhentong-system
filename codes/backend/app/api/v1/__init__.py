"""
API路由聚合
整合所有API路由模块
"""

from fastapi import APIRouter

# 导入所有API模块
from ..auth import router as auth_router
from ..conversations import router as conversations_router
from ..diagnosis import router as diagnosis_router
from ..knowledge import router as knowledge_router
from ..multimodal import router as multimodal_router
from ..system import router as system_router

# 创建主路由器
api_router = APIRouter()

# 注册所有API路由
api_router.include_router(auth_router)
api_router.include_router(conversations_router)
api_router.include_router(diagnosis_router)
api_router.include_router(knowledge_router)
api_router.include_router(multimodal_router)
api_router.include_router(system_router)

# 健康检查端点
@api_router.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "message": "智诊通系统运行正常",
        "version": "1.0.0"
    }

# 导出主路由器
__all__ = ["api_router"]
