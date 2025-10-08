"""
智能诊断服务API接口
提供RESTful API接口用于智能诊断功能
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# 使用统一日志配置
import sys
from pathlib import Path

# 添加common模块到路径
current_file = Path(__file__)
common_dir = current_file.parent.parent.parent.parent / "common"
sys.path.insert(0, str(common_dir))

# 添加项目根目录到路径
import sys
from pathlib import Path
current_file = Path(__file__)
project_root = current_file.parent.parent.parent.parent  # 回到codes目录
sys.path.insert(0, str(project_root))

from common.log_config import setup_logging, get_logger
setup_logging("diagnosis_service")
logger = get_logger(__name__)

# 导入核心服务
from services.intelligent_diagnosis_service.core.diagnosis_service import IntelligentDiagnosisService, create_intelligent_diagnosis_service


# 请求模型
class DiagnosisRequest(BaseModel):
    """诊断请求模型"""
    query: str = Field(..., description="用户查询", min_length=1, max_length=1000)
    context: str = Field(default="", description="检索到的上下文信息", max_length=10000)
    response_type: str = Field(default="diagnosis", description="响应类型", pattern="^(diagnosis|advice|explanation)$")
    enable_summary: bool = Field(default=True, description="是否启用文本摘要")


class SummarizeRequest(BaseModel):
    """摘要请求模型"""
    text: str = Field(..., description="需要摘要的文本", min_length=1, max_length=5000)
    max_length: int = Field(default=200, description="最大摘要长度", ge=50, le=500)
    retrieval_content: str = Field(default="", description="检索到的医疗文献内容", max_length=5000)


# 响应模型
class DiagnosisResponse(BaseModel):
    """诊断响应模型"""
    success: bool = Field(..., description="是否成功")
    query: str = Field(..., description="用户查询")
    context: str = Field(..., description="上下文信息")
    response_type: str = Field(..., description="响应类型")
    summary: str = Field(..., description="文本摘要")
    diagnosis_response: str = Field(..., description="诊断响应")
    error: Optional[str] = Field(None, description="错误信息")


class SummarizeResponse(BaseModel):
    """摘要响应模型"""
    success: bool = Field(..., description="是否成功")
    original_text: str = Field(..., description="原始文本")
    summary: str = Field(..., description="摘要结果")
    error: Optional[str] = Field(None, description="错误信息")


class ServiceInfoResponse(BaseModel):
    """服务信息响应模型"""
    service_name: str = Field(..., description="服务名称")
    service_version: str = Field(..., description="服务版本")
    service_status: str = Field(..., description="服务状态")
    summarization_service: Dict[str, Any] = Field(..., description="摘要服务信息")
    llm_service: Dict[str, Any] = Field(..., description="LLM服务信息")
    config: Dict[str, Any] = Field(..., description="配置信息")


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    service: str = Field(..., description="服务名称")
    status: str = Field(..., description="健康状态")
    timestamp: str = Field(..., description="时间戳")
    components: Dict[str, Any] = Field(..., description="组件状态")


# 创建FastAPI应用
app = FastAPI(
    title="智诊通智能诊断服务",
    description="基于大语言模型的医疗智能诊断服务",
    version="1.0.0",
    docs_url="/diagnosis/docs",
    redoc_url="/diagnosis/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局服务实例
diagnosis_service: Optional[IntelligentDiagnosisService] = None


@app.on_event("startup")
async def startup_event():
    """启动事件"""
    global diagnosis_service
    try:
        logger.info("正在启动智能诊断服务...")
        diagnosis_service = create_intelligent_diagnosis_service()
        logger.info("智能诊断服务启动成功")
    except Exception as e:
        logger.error(f"智能诊断服务启动失败: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """关闭事件"""
    logger.info("智能诊断服务正在关闭...")


@app.get("/diagnosis/health", response_model=HealthResponse)
async def health_check():
    """健康检查接口"""
    try:
        if diagnosis_service is None:
            raise HTTPException(status_code=503, detail="服务未初始化")
        
        health_status = diagnosis_service.health_check()
        return HealthResponse(**health_status)
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")


@app.get("/diagnosis/info", response_model=ServiceInfoResponse)
async def get_service_info():
    """获取服务信息接口"""
    try:
        if diagnosis_service is None:
            raise HTTPException(status_code=503, detail="服务未初始化")
        
        service_info = diagnosis_service.get_service_info()
        return ServiceInfoResponse(**service_info)
        
    except Exception as e:
        logger.error(f"获取服务信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取服务信息失败: {str(e)}")


@app.post("/diagnosis/summarize", response_model=SummarizeResponse)
async def summarize_text(request: SummarizeRequest):
    """文本摘要接口"""
    try:
        if diagnosis_service is None:
            raise HTTPException(status_code=503, detail="服务未初始化")
        
        logger.info(f"收到摘要请求: text长度={len(request.text)}, max_length={request.max_length}")
        
        # 调用摘要服务
        summary = diagnosis_service.summarization_service.summarize_medical_text(
            request.text,
            max_length=request.max_length,
            retrieval_content=request.retrieval_content
        )
        
        logger.info(f"摘要完成: 原文长度={len(request.text)}, 摘要长度={len(summary)}")
        
        return SummarizeResponse(
            success=True,
            original_text=request.text,
            summary=summary,
            error=None
        )
        
    except Exception as e:
        logger.error(f"文本摘要失败: {e}")
        return SummarizeResponse(
            success=False,
            original_text=request.text,
            summary="",
            error=str(e)
        )


@app.post("/diagnosis/generate", response_model=DiagnosisResponse)
async def generate_diagnosis(request: DiagnosisRequest):
    """生成诊断建议接口"""
    try:
        if diagnosis_service is None:
            raise HTTPException(status_code=503, detail="服务未初始化")
        
        logger.info(f"收到诊断请求: query='{request.query}', context长度={len(request.context)}, response_type='{request.response_type}'")
        
        # 调用诊断服务
        result = diagnosis_service.process_diagnosis_request(
            query=request.query,
            context=request.context,
            response_type=request.response_type,
            enable_summary=request.enable_summary
        )
        
        logger.info(f"诊断完成: success={result['success']}, 响应长度={len(result['diagnosis_response'])}")
        
        return DiagnosisResponse(**result)
        
    except Exception as e:
        logger.error(f"生成诊断建议失败: {e}")
        return DiagnosisResponse(
            success=False,
            query=request.query,
            context=request.context,
            response_type=request.response_type,
            summary="",
            diagnosis_response="抱歉，生成诊断建议时出现错误。请咨询专业医生。",
            error=str(e)
        )


@app.post("/diagnosis/stream")
async def generate_diagnosis_stream(request: DiagnosisRequest):
    """流式生成诊断建议接口"""
    try:
        if diagnosis_service is None:
            raise HTTPException(status_code=503, detail="服务未初始化")
        
        logger.info(f"收到流式诊断请求: query='{request.query}', context长度={len(request.context)}, response_type='{request.response_type}'")
        
        def generate():
            """生成器函数"""
            try:
                for chunk in diagnosis_service.process_diagnosis_request_stream(
                    query=request.query,
                    context=request.context,
                    response_type=request.response_type,
                    enable_summary=request.enable_summary
                ):
                    yield f"data: {json.dumps({'chunk': chunk}, ensure_ascii=False)}\n\n"
                
                # 发送结束标记
                yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"
                
            except Exception as e:
                logger.error(f"流式生成失败: {e}")
                yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/plain; charset=utf-8"
            }
        )
        
    except Exception as e:
        logger.error(f"流式生成诊断建议失败: {e}")
        raise HTTPException(status_code=500, detail=f"流式生成失败: {str(e)}")


@app.get("/diagnosis/")
async def root():
    """根路径接口"""
    return {
        "service": "智诊通智能诊断服务",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/diagnosis/health",
            "info": "/diagnosis/info",
            "summarize": "/diagnosis/summarize",
            "generate": "/diagnosis/generate",
            "stream": "/diagnosis/stream",
            "docs": "/diagnosis/docs"
        }
    }


# 异常处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理"""
    logger.error(f"HTTP异常: {exc.status_code} - {exc.detail}")
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "path": str(request.url)
    }


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理"""
    logger.error(f"未处理的异常: {str(exc)}")
    return {
        "error": "内部服务器错误",
        "status_code": 500,
        "path": str(request.url)
    }


if __name__ == "__main__":
    # 启动服务
    uvicorn.run(
        "diagnosis_api:app",
        host="0.0.0.0",
        port=8003,
        reload=False,
        log_level="info"
    )
