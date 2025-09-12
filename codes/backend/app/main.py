"""
智诊通-多模态智能医生问诊系统
FastAPI主应用入口
"""

import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from .config import settings
from .database import create_tables, check_database_connection
from .cache import redis_client
from .api.v1 import api_router
from .models.base import Base
from .database import engine

# 全局变量用于存储应用启动时间
app_start_time = None

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # 输出到控制台
        logging.FileHandler(settings.LOG_FILE, encoding='utf-8')  # 输出到文件
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    global app_start_time
    
    # 启动时执行
    app_start_time = time.time()
    logger.info("🚀 智诊通系统启动中...")
    print("🚀 智诊通系统启动中...")
    
    # 检查数据库连接
    try:
        check_database_connection()
        logger.info("✅ 数据库连接正常")
        print("✅ 数据库连接正常")
    except Exception as e:
        logger.error(f"❌ 数据库连接失败: {e}")
        print(f"❌ 数据库连接失败: {e}")
        raise
    
    # 创建数据库表
    try:
        await create_tables()
        logger.info("✅ 数据库表创建完成")
        print("✅ 数据库表创建完成")
    except Exception as e:
        logger.error(f"❌ 数据库表创建失败: {e}")
        print(f"❌ 数据库表创建失败: {e}")
        raise
    
    # 检查Redis连接
    try:
        redis_client.ping()
        logger.info("✅ Redis连接正常")
        print("✅ Redis连接正常")
    except Exception as e:
        logger.error(f"❌ Redis连接失败: {e}")
        print(f"❌ Redis连接失败: {e}")
        raise
    
    logger.info("🎉 智诊通系统启动完成!")
    print("🎉 智诊通系统启动完成!")
    
    yield
    
    # 关闭时执行
    print("🔄 智诊通系统关闭中...")
    
    # 关闭Redis连接
    try:
        redis_client.close()
        print("✅ Redis连接已关闭")
    except Exception as e:
        print(f"❌ Redis连接关闭失败: {e}")
    
    print("👋 智诊通系统已关闭")


# 创建FastAPI应用实例
app = FastAPI(
    title="智诊通-多模态智能医生问诊系统",
    description="""
    ## 智诊通系统API文档
    
    这是一个基于多模态AI技术的智能医生问诊系统，支持：
    
    ### 核心功能
    - 🔐 **用户认证管理** - 用户注册、登录、会话管理
    - 💬 **智能对话管理** - 多轮对话、上下文跟踪、状态管理
    - 🏥 **智能诊断** - 症状分析、风险评估、诊断建议
    - 📚 **知识库检索** - RAG技术、医疗知识检索
    - 🎯 **多模态处理** - 文本、音频、图像综合处理
    - ⚙️ **系统管理** - 配置管理、用户偏好、操作日志
    
    ### 技术特点
    - 基于FastAPI构建的高性能API
    - 支持异步处理和实时响应
    - 集成Swagger自动文档生成
    - 完整的错误处理和日志记录
    - 模块化设计，易于扩展
    
    ### 开发状态
    - ✅ 后端API框架已完成
    - ✅ 数据库设计和ORM模型
    - ✅ 用户认证和权限管理
    - ✅ 多模态处理接口（模拟数据）
    - ✅ 智能诊断接口（模拟数据）
    - ✅ 知识库检索接口（模拟数据）
    - ✅ 对话管理系统
    - 🔄 算法服务开发中（当前使用模拟数据）
    
    ### 使用说明
    1. 首先通过 `/auth/register` 注册用户
    2. 使用 `/auth/login` 登录获取访问令牌
    3. 在请求头中添加 `Authorization: Bearer <token>` 进行认证
    4. 开始使用各种功能接口
    
    ### 注意事项
    - 当前算法相关接口返回模拟数据，用于前端开发测试
    - 所有敏感操作都需要有效的JWT令牌
    - 文件上传支持多种格式，大小限制为10MB
    """,
    version="1.0.0",
    contact={
        "name": "智诊通开发团队",
        "email": "support@zhizhentong.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    docs_url=None,  # 禁用默认文档URL
    redoc_url=None,  # 禁用默认ReDoc URL
    lifespan=lifespan
)


# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else settings.CORS_ORIGINS,  # 开发模式下允许所有源
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 添加可信主机中间件
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)


# 请求处理中间件
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    添加请求处理时间头和请求日志
    """
    start_time = time.time()
    
    # 记录请求信息
    logger.info(f"🔍 收到请求: {request.method} {request.url.path}")
    logger.info(f"📋 请求头: {dict(request.headers)}")
    
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # 记录响应信息
    logger.info(f"✅ 响应状态: {response.status_code}, 处理时间: {process_time:.3f}s")
    
    response.headers["X-Process-Time"] = str(process_time)
    return response


# 全局异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全局异常处理
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "内部服务器错误",
            "detail": str(exc),
            "timestamp": time.time(),
            "path": request.url.path
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    HTTP异常处理
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": time.time(),
            "path": request.url.path
        }
    )


# 全局OPTIONS处理器
@app.options("/{full_path:path}", include_in_schema=False)
async def options_handler():
    """
    全局OPTIONS请求处理器，用于CORS预检
    """
    return {"message": "OK"}


# 健康检查端点
@app.get("/health", summary="健康检查", tags=["系统"])
@app.options("/health", include_in_schema=False)
async def health_check():
    """
    系统健康检查
    
    返回系统运行状态和基本信息
    """
    global app_start_time
    
    # 检查数据库连接
    db_status = "healthy"
    try:
        check_database_connection()
    except Exception:
        db_status = "unhealthy"
    
    # 检查Redis连接
    redis_status = "healthy"
    try:
        redis_client.ping()
    except Exception:
        redis_status = "unhealthy"
    
    # 计算运行时间
    uptime = time.time() - app_start_time if app_start_time else 0
    
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "uptime_seconds": uptime,
        "version": "1.0.0",
        "services": {
            "database": db_status,
            "redis": redis_status
        },
        "system_info": {
            "name": "智诊通-多模态智能医生问诊系统",
            "description": "基于AI技术的智能医疗问诊系统"
        }
    }


# 根路径端点
@app.get("/", summary="系统根路径", tags=["系统"])
async def root():
    """
    系统根路径
    
    返回系统基本信息和API文档链接
    """
    return {
        "message": "欢迎使用智诊通-多模态智能医生问诊系统",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "features": [
            "用户认证管理",
            "智能对话管理", 
            "智能诊断",
            "知识库检索",
            "多模态处理",
            "系统管理"
        ]
    }


# 自定义Swagger UI
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """
    自定义Swagger UI界面
    """
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - API文档",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
        swagger_ui_parameters={
            "defaultModelsExpandDepth": -1,
            "defaultModelExpandDepth": 3,
            "displayRequestDuration": True,
            "docExpansion": "list",
            "filter": True,
            "showExtensions": True,
            "showCommonExtensions": True,
            "tryItOutEnabled": True,
            "syntaxHighlight.theme": "monokai"
        }
    )


# 自定义OpenAPI模式
def custom_openapi():
    """
    自定义OpenAPI模式
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # 确保components存在
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    
    # 添加安全模式
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT访问令牌，格式：Bearer <token>"
        }
    }
    
    # 添加全局安全要求
    openapi_schema["security"] = [{"BearerAuth": []}]
    
    # 添加服务器信息
    openapi_schema["servers"] = [
        {
            "url": "http://localhost:8000",
            "description": "开发服务器"
        },
        {
            "url": "https://api.zhizhentong.com",
            "description": "生产服务器"
        }
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "message": "智诊通系统运行正常",
        "version": "1.0.0"
    }

# 注册API路由
# 认证路由直接注册到根路径
from .api.auth import router as auth_router
app.include_router(auth_router)

# 其他API路由注册到 /api/v1 前缀
app.include_router(api_router, prefix="/api/v1")


# 开发模式下的调试信息
if settings.DEBUG:
    @app.get("/debug/info", summary="调试信息", tags=["调试"])
    async def debug_info():
        """
        调试信息端点（仅开发模式）
        """
        return {
            "debug": True,
            "environment": settings.ENVIRONMENT,
            "database_url": str(settings.DATABASE_URL),
            "redis_url": str(settings.REDIS_URL),
            "milvus_host": settings.MILVUS_HOST,
            "milvus_port": settings.MILVUS_PORT,
            "secret_key": settings.SECRET_KEY[:10] + "..." if settings.SECRET_KEY else None,
            "cors_origins": settings.CORS_ORIGINS,
            "allowed_hosts": settings.ALLOWED_HOSTS,
            "max_file_size": settings.MAX_FILE_SIZE,
            "log_level": settings.LOG_LEVEL
        }


# 启动事件
@app.on_event("startup")
async def startup_event():
    """
    应用启动事件
    """
    print("🎯 智诊通系统API服务已启动")
    print(f"📖 API文档地址: http://localhost:{settings.SERVER_PORT}/docs")
    print(f"🔍 健康检查: http://localhost:{settings.SERVER_PORT}/health")


# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """
    应用关闭事件
    """
    print("🔄 智诊通系统API服务正在关闭...")


# 如果直接运行此文件
if __name__ == "__main__":
    import uvicorn
    
    print("🚀 启动智诊通系统...")
    uvicorn.run(
        "main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )
