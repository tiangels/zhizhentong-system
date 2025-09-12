"""
API路由聚合
整合所有API路由模块
"""

from fastapi import APIRouter

# 导入所有API模块（除了认证路由，它直接注册到主应用）
from ...api.conversations import router as conversations_router
from ...api.diagnosis import router as diagnosis_router
from ...api.knowledge import router as knowledge_router
from ...api.multimodal import router as multimodal_router
from ...api.system import router as system_router

# 创建主路由器
api_router = APIRouter()

# 注册所有API路由（除了认证路由）
api_router.include_router(conversations_router)
api_router.include_router(diagnosis_router)
api_router.include_router(knowledge_router)
api_router.include_router(multimodal_router)
api_router.include_router(system_router)

# 健康检查端点已移动到主应用中

# 导出主路由器
__all__ = ["api_router"]
