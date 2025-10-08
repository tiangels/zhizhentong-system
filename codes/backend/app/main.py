"""
智诊通-多模态智能医生问诊系统
FastAPI主应用入口
"""

import time
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import create_tables, check_database_connection
from .cache import redis_client
from .api.v1 import api_router
from .models.base import Base
from .database import engine

# 全局变量用于存储应用启动时间
app_start_time = None

# 导入统一日志配置
import sys
from pathlib import Path

# 添加common模块到路径
current_file = Path(__file__)
common_dir = current_file.parent.parent.parent / "common"  # codes/common
sys.path.insert(0, str(common_dir))

try:
    from log_config import (
        setup_backend_service_logging, 
        get_backend_logger, 
        log_system_event, 
        log_performance_metrics,
        log_request,
        log_response
    )
    # 初始化后端服务日志配置
    backend_logger = setup_backend_service_logging(show_config_logs=True)
    print("✅ 统一日志配置加载成功")
except ImportError as e:
    print(f"❌ 统一日志配置加载失败: {e}")
    # 如果导入失败，使用简单的日志记录
    import logging
    backend_logger = logging.getLogger("backend")
    
    def log_system_event(message: str, **kwargs):
        backend_logger.logger.info(f"系统事件: {message}")
    
    def log_performance_metrics(operation: str, duration: float, **kwargs):
        backend_logger.logger.info(f"性能指标 - {operation}: {duration:.2f}秒")
    
    def log_request(method: str, path: str, user_id: str = None, request_data: dict = None, duration: float = None):
        backend_logger.logger.info(f"HTTP请求: {method} {path} - 用户: {user_id}")
    
    def log_response(status_code: int, response_data: dict = None, error: str = None):
        backend_logger.logger.info(f"HTTP响应: {status_code}")

# 获取后端服务专用日志记录器（如果导入成功）
try:
    backend_logger = get_backend_logger()
except NameError:
    # 如果get_backend_logger未定义，使用上面创建的backend_logger
    pass

# 为后端服务添加标准日志方法
def log_info(message: str):
    """记录信息日志"""
    backend_logger.log_system_event(message)

def log_error(message: str):
    """记录错误日志"""
    backend_logger.log_system_event(f"ERROR: {message}", level="ERROR")

def log_warning(message: str):
    """记录警告日志"""
    backend_logger.log_system_event(f"WARNING: {message}", level="WARNING")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    global app_start_time
    
    # 启动时执行
    app_start_time = time.time()
    backend_logger.logger.info("🚀 智诊通系统启动中...")
    print("🚀 智诊通系统启动中...")
    
    # 记录系统启动事件
    log_system_event("系统启动开始", {
        "start_time": datetime.now().isoformat(),
        "environment": settings.ENVIRONMENT,
        "debug_mode": settings.DEBUG
    })
    
    # 检查数据库连接
    db_start_time = time.time()
    try:
        check_database_connection()
        db_duration = time.time() - db_start_time
        backend_logger.logger.info("✅ 数据库连接正常")
        print("✅ 数据库连接正常")
        log_system_event("数据库连接检查", {
            "status": "success",
            "duration": f"{db_duration:.3f}s"
        })
    except Exception as e:
        db_duration = time.time() - db_start_time
        backend_logger.logger.error(f"❌ 数据库连接失败: {e}")
        print(f"❌ 数据库连接失败: {e}")
        log_system_event("数据库连接检查", {
            "status": "failed",
            "error": str(e),
            "duration": f"{db_duration:.3f}s"
        }, "ERROR")
        raise
    
    # 创建数据库表
    table_start_time = time.time()
    try:
        await create_tables()
        table_duration = time.time() - table_start_time
        backend_logger.logger.info("✅ 数据库表创建完成")
        print("✅ 数据库表创建完成")
        log_system_event("数据库表创建", {
            "status": "success",
            "duration": f"{table_duration:.3f}s"
        })
    except Exception as e:
        table_duration = time.time() - table_start_time
        backend_logger.logger.error(f"❌ 数据库表创建失败: {e}")
        print(f"❌ 数据库表创建失败: {e}")
        log_system_event("数据库表创建", {
            "status": "failed",
            "error": str(e),
            "duration": f"{table_duration:.3f}s"
        }, "ERROR")
        raise
    
    # 检查Redis连接
    redis_start_time = time.time()
    try:
        redis_client.ping()
        redis_duration = time.time() - redis_start_time
        backend_logger.logger.info("✅ Redis连接正常")
        print("✅ Redis连接正常")
        log_system_event("Redis连接检查", {
            "status": "success",
            "duration": f"{redis_duration:.3f}s"
        })
    except Exception as e:
        redis_duration = time.time() - redis_start_time
        backend_logger.logger.error(f"❌ Redis连接失败: {e}")
        print(f"❌ Redis连接失败: {e}")
        log_system_event("Redis连接检查", {
            "status": "failed",
            "error": str(e),
            "duration": f"{redis_duration:.3f}s"
        }, "ERROR")
        raise
    
    # 记录系统启动完成
    total_startup_time = time.time() - app_start_time
    backend_logger.logger.info("🎉 智诊通系统启动完成!")
    print("🎉 智诊通系统启动完成!")
    log_system_event("系统启动完成", {
        "total_startup_time": f"{total_startup_time:.3f}s",
        "database_check_time": f"{db_duration:.3f}s",
        "table_creation_time": f"{table_duration:.3f}s",
        "redis_check_time": f"{redis_duration:.3f}s"
    })
    
    # 记录性能指标
    log_performance_metrics("系统启动", {
        "total_time": total_startup_time,
        "database_check": db_duration,
        "table_creation": table_duration,
        "redis_check": redis_duration
    })
    
    yield
    
    # 关闭时执行
    shutdown_start_time = time.time()
    print("🔄 智诊通系统关闭中...")
    log_system_event("系统关闭开始", {
        "shutdown_time": datetime.now().isoformat()
    })
    
    # 关闭Redis连接
    redis_close_start = time.time()
    try:
        redis_client.close()
        redis_close_duration = time.time() - redis_close_start
        print("✅ Redis连接已关闭")
        log_system_event("Redis连接关闭", {
            "status": "success",
            "duration": f"{redis_close_duration:.3f}s"
        })
    except Exception as e:
        redis_close_duration = time.time() - redis_close_start
        print(f"❌ Redis连接关闭失败: {e}")
        log_system_event("Redis连接关闭", {
            "status": "failed",
            "error": str(e),
            "duration": f"{redis_close_duration:.3f}s"
        }, "ERROR")
    
    # 记录系统关闭完成
    total_shutdown_time = time.time() - shutdown_start_time
    print("👋 智诊通系统已关闭")
    log_system_event("系统关闭完成", {
        "total_shutdown_time": f"{total_shutdown_time:.3f}s",
        "redis_close_time": f"{redis_close_duration:.3f}s"
    })
    
    # 记录性能指标
    log_performance_metrics("系统关闭", {
        "total_time": total_shutdown_time,
        "redis_close": redis_close_duration
    })


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
    - 📚 **知识库检索** - 检索技术、医疗知识检索
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

# 设置文件上传大小限制
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# 配置文件上传大小限制
app.state.max_file_size = settings.MAX_FILE_SIZE


# 请求处理中间件
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    添加请求处理时间头和请求日志
    """
    start_time = time.time()
    
    # 获取用户信息（如果有的话）
    user_id = None
    try:
        # 尝试从请求头中获取用户ID
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # 这里可以解析JWT token获取用户ID，暂时设为None
            user_id = "authenticated_user"
    except Exception:
        pass
    
    # 记录请求信息
    backend_logger.logger.info(f"🔍 收到请求: {request.method} {request.url.path}")
    backend_logger.logger.info(f"📋 请求头: {dict(request.headers)}")
    
    # 使用后端服务日志记录器记录请求
    
    # 获取请求数据（仅对POST/PUT请求）
    request_data = None
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            # 这里可以获取请求体，但要注意不要记录敏感信息
            request_data = {"method": request.method, "path": request.url.path}
        except Exception:
            pass
    
    # 记录请求日志
    log_request(
        method=request.method,
        path=request.url.path,
        user_id=user_id,
        request_data=request_data
    )
    
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # 记录响应信息
    backend_logger.logger.info(f"✅ 响应状态: {response.status_code}, 处理时间: {process_time:.3f}s")
    
    # 记录响应日志
    log_response(
        status_code=response.status_code,
        response_data={"process_time": f"{process_time:.3f}s"} if response.status_code < 400 else None,
        error=str(response.status_code) if response.status_code >= 400 else None
    )
    
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


# 移除重复的健康检查端点（已在上方定义并包含详细检查）

# 添加静态文件服务
import os
from pathlib import Path

# 注册API路由
# 认证路由直接注册到根路径
from .api.auth import router as auth_router
app.include_router(auth_router)

# 其他API路由注册到 /api/v1 前缀
app.include_router(api_router, prefix="/api/v1")

# 确保上传目录存在
upload_dir = Path(settings.UPLOAD_DIR)
upload_dir.mkdir(parents=True, exist_ok=True)

# 挂载静态文件服务（在API路由之后，避免冲突）
app.mount("/api/v1/files", StaticFiles(directory=str(upload_dir)), name="files")


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
        "app.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )
