"""
RAG系统API接口
提供标准化的REST API接口，供前端和其他服务调用
"""

import os
import json
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
import uvicorn
import asyncio

# 导入RAG核心模块
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.rag_pipeline import RAGPipeline, RAGPipelineFactory

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="RAG Knowledge Retrieval API",
    description="基于Qwen2-0.5B-Medical-MLX的RAG检索增强系统API",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局RAG流程实例
rag_pipeline: Optional[RAGPipeline] = None

# Pydantic模型定义
class DocumentModel(BaseModel):
    """文档模型"""
    content: str = Field(..., description="文档内容")
    title: Optional[str] = Field(None, description="文档标题")
    category: Optional[str] = Field(None, description="文档类别")
    source: Optional[str] = Field(None, description="文档来源")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")
    type: Optional[str] = Field("text", description="文档类型")

class ImageDocumentModel(BaseModel):
    """图像文档模型"""
    image_path: str = Field(..., description="图像文件路径")
    title: Optional[str] = Field(None, description="图像标题")
    category: Optional[str] = Field(None, description="图像类别")
    source: Optional[str] = Field(None, description="图像来源")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")

class QueryRequest(BaseModel):
    """查询请求模型"""
    question: str = Field(..., description="用户问题")
    top_k: int = Field(5, description="检索文档数量", ge=1, le=20)
    response_type: str = Field("general", description="响应类型")
    similarity_threshold: float = Field(0.5, description="相似度阈值", ge=0.0, le=1.0)

class ChatRequest(BaseModel):
    """对话请求模型"""
    messages: List[Dict[str, str]] = Field(..., description="对话历史")
    top_k: int = Field(5, description="检索文档数量", ge=1, le=20)

class SearchRequest(BaseModel):
    """搜索请求模型"""
    query: str = Field(..., description="搜索查询")
    search_type: str = Field("semantic", description="搜索类型")
    top_k: int = Field(10, description="返回文档数量", ge=1, le=50)

class BatchQueryRequest(BaseModel):
    """批量查询请求模型"""
    questions: List[str] = Field(..., description="问题列表")
    top_k: int = Field(5, description="检索文档数量", ge=1, le=20)

class ResponseModel(BaseModel):
    """响应模型"""
    success: bool = Field(..., description="是否成功")
    data: Optional[Dict[str, Any]] = Field(None, description="响应数据")
    message: Optional[str] = Field(None, description="响应消息")
    timestamp: str = Field(..., description="时间戳")

# 依赖注入
def get_rag_pipeline() -> RAGPipeline:
    """获取RAG流程实例"""
    global rag_pipeline
    if rag_pipeline is None:
        raise HTTPException(status_code=503, detail="RAG pipeline not initialized")
    return rag_pipeline

# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化RAG流程"""
    global rag_pipeline
    try:
        logger.info("Initializing RAG pipeline...")
        
        # 加载配置
        config_path = os.path.join(os.path.dirname(__file__), "config", "rag_config.json")
        rag_pipeline = RAGPipelineFactory.create_rag_pipeline(config_path)
        
        logger.info("RAG pipeline initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing RAG pipeline: {e}")
        raise

# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    global rag_pipeline
    if rag_pipeline:
        try:
            rag_pipeline.clear_system()
            logger.info("RAG pipeline cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up RAG pipeline: {e}")

# API路由
@app.get("/", response_model=ResponseModel)
async def root():
    """根路径，返回API信息"""
    return ResponseModel(
        success=True,
        data={
            "api_name": "RAG Knowledge Retrieval API",
            "version": "1.0.0",
            "status": "running"
        },
        message="API is running",
        timestamp=datetime.now().isoformat()
    )

@app.get("/health", response_model=ResponseModel)
async def health_check():
    """健康检查"""
    try:
        rag = get_rag_pipeline()
        stats = rag.get_system_stats()
        
        return ResponseModel(
            success=True,
            data=stats,
            message="System is healthy",
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        return ResponseModel(
            success=False,
            message=f"Health check failed: {str(e)}",
            timestamp=datetime.now().isoformat()
        )

@app.post("/documents", response_model=ResponseModel)
async def add_documents(
    documents: List[DocumentModel],
    background_tasks: BackgroundTasks,
    rag: RAGPipeline = Depends(get_rag_pipeline)
):
    """添加文档到RAG系统"""
    try:
        # 转换文档格式
        doc_list = []
        for doc in documents:
            doc_dict = doc.dict()
            doc_list.append(doc_dict)
        
        # 异步添加文档
        def add_docs():
            return rag.add_documents(doc_list)
        
        background_tasks.add_task(add_docs)
        
        return ResponseModel(
            success=True,
            data={"document_count": len(documents)},
            message=f"Added {len(documents)} documents",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error adding documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/documents/images", response_model=ResponseModel)
async def add_image_documents(
    documents: List[ImageDocumentModel],
    background_tasks: BackgroundTasks,
    rag: RAGPipeline = Depends(get_rag_pipeline)
):
    """添加图像文档到RAG系统"""
    try:
        # 转换文档格式
        doc_list = []
        for doc in documents:
            doc_dict = doc.dict()
            doc_dict['type'] = 'image'
            doc_list.append(doc_dict)
        
        # 异步添加文档
        def add_docs():
            return rag.add_documents(doc_list, vectorize_images=True)
        
        background_tasks.add_task(add_docs)
        
        return ResponseModel(
            success=True,
            data={"document_count": len(documents)},
            message=f"Added {len(documents)} image documents",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error adding image documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=ResponseModel)
async def query_documents(
    request: QueryRequest,
    rag: RAGPipeline = Depends(get_rag_pipeline)
):
    """查询RAG系统"""
    try:
        print("=" * 50)
        print("🌐 API查询请求开始")
        print("=" * 50)
        logger.info("开始处理API查询请求...")
        
        # 1. 获取用户输入
        print("==========")
        print("获取用户输入开始")
        print("==========")
        logger.info(f"获取用户输入细节日志：问题='{request.question}', top_k={request.top_k}, response_type='{request.response_type}'")
        logger.info("获取用户输入成功")
        print("获取用户输入结束")
        print("==========")
        
        # 2. 用户数据处理
        print("==========")
        print("用户数据处理开始")
        print("==========")
        logger.info("用户数据处理的细节日志：开始验证请求参数")
        logger.info(f"问题长度: {len(request.question)} 字符")
        logger.info(f"检索数量: {request.top_k}")
        logger.info(f"响应类型: {request.response_type}")
        logger.info("用户数据处理完成")
        logger.info("用户数据处理成功")
        print("==========")
        
        # 3. 调用RAG系统
        print("==========")
        print("调用RAG系统开始")
        print("==========")
        logger.info("调用RAG系统的细节日志：开始调用RAG Pipeline")
        
        try:
            # 设置60秒超时
            result = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: rag.query(
                        question=request.question,
                        top_k=request.top_k,
                        response_type=request.response_type,
                        similarity_threshold=request.similarity_threshold
                    )
                ),
                timeout=300.0
            )
            logger.info("RAG系统调用完成")
            logger.info("调用RAG系统成功")
        except asyncio.TimeoutError:
            logger.error("RAG系统调用超时")
            raise HTTPException(status_code=408, detail="查询超时，请稍后重试")
        
        print("调用RAG系统结束")
        print("==========")
        
        # 4. 返回用户结果
        print("==========")
        print("返回用户结果开始")
        print("==========")
        logger.info("返回用户结果的细节日志：开始构建API响应")
        response = ResponseModel(
            success=True,
            data=result,
            message="Query completed successfully",
            timestamp=datetime.now().isoformat()
        )
        logger.info("API响应构建完成")
        logger.info("返回用户结果成功")
        print("返回用户结果结束")
        print("==========")
        
        print("=" * 50)
        print("🎉 API查询请求完成")
        print("=" * 50)
        logger.info("API查询请求成功完成")
        
        return response
        
    except Exception as e:
        print("=" * 50)
        print("❌ API查询请求失败")
        print("=" * 50)
        logger.error(f"API查询请求失败: {e}")
        logger.error(f"Error querying documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ResponseModel)
async def chat_with_rag(
    request: ChatRequest,
    rag: RAGPipeline = Depends(get_rag_pipeline)
):
    """与RAG系统对话"""
    try:
        print("=" * 50)
        print("💬 API对话请求开始")
        print("=" * 50)
        logger.info("开始处理API对话请求...")
        
        # 1. 获取用户输入
        print("==========")
        print("获取用户输入开始")
        print("==========")
        logger.info(f"获取用户输入细节日志：对话历史长度={len(request.messages)}, top_k={request.top_k}")
        for i, msg in enumerate(request.messages):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')[:50] + ('...' if len(msg.get('content', '')) > 50 else '')
            logger.info(f"消息 {i+1}: 角色={role}, 内容='{content}'")
        logger.info("获取用户输入成功")
        print("获取用户输入结束")
        print("==========")
        
        # 2. 用户数据处理
        print("==========")
        print("用户数据处理开始")
        print("==========")
        logger.info("用户数据处理的细节日志：开始验证对话请求")
        logger.info(f"对话轮数: {len(request.messages)}")
        logger.info(f"检索数量: {request.top_k}")
        logger.info("用户数据处理完成")
        logger.info("用户数据处理成功")
        print("==========")
        
        # 3. 调用RAG系统
        print("==========")
        print("调用RAG系统开始")
        print("==========")
        logger.info("调用RAG系统的细节日志：开始调用RAG Pipeline进行对话")
        result = rag.chat(
            messages=request.messages,
            top_k=request.top_k
        )
        logger.info("RAG系统对话调用完成")
        logger.info("调用RAG系统成功")
        print("调用RAG系统结束")
        print("==========")
        
        # 4. 返回用户结果
        print("==========")
        print("返回用户结果开始")
        print("==========")
        logger.info("返回用户结果的细节日志：开始构建对话API响应")
        response = ResponseModel(
            success=True,
            data=result,
            message="Chat completed successfully",
            timestamp=datetime.now().isoformat()
        )
        logger.info("对话API响应构建完成")
        logger.info("返回用户结果成功")
        print("返回用户结果结束")
        print("==========")
        
        print("=" * 50)
        print("🎉 API对话请求完成")
        print("=" * 50)
        logger.info("API对话请求成功完成")
        
        return response
        
    except Exception as e:
        print("=" * 50)
        print("❌ API对话请求失败")
        print("=" * 50)
        logger.error(f"API对话请求失败: {e}")
        logger.error(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search", response_model=ResponseModel)
async def search_documents(
    request: SearchRequest,
    rag: RAGPipeline = Depends(get_rag_pipeline)
):
    """搜索文档"""
    try:
        results = rag.search_documents(
            query=request.query,
            search_type=request.search_type,
            top_k=request.top_k
        )
        
        return ResponseModel(
            success=True,
            data={"documents": results, "count": len(results)},
            message="Search completed successfully",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/batch_query", response_model=ResponseModel)
async def batch_query_documents(
    request: BatchQueryRequest,
    rag: RAGPipeline = Depends(get_rag_pipeline)
):
    """批量查询"""
    try:
        print("=" * 50)
        print("📦 API批量查询请求开始")
        print("=" * 50)
        logger.info("开始处理API批量查询请求...")
        
        # 1. 获取用户输入
        print("==========")
        print("获取用户输入开始")
        print("==========")
        logger.info(f"获取用户输入细节日志：问题数量={len(request.questions)}, top_k={request.top_k}")
        for i, question in enumerate(request.questions):
            logger.info(f"问题 {i+1}: '{question[:50]}{'...' if len(question) > 50 else ''}'")
        logger.info("获取用户输入成功")
        print("获取用户输入结束")
        print("==========")
        
        # 2. 用户数据处理
        print("==========")
        print("用户数据处理开始")
        print("==========")
        logger.info("用户数据处理的细节日志：开始验证批量查询请求")
        logger.info(f"问题总数: {len(request.questions)}")
        logger.info(f"检索数量: {request.top_k}")
        logger.info("用户数据处理完成")
        logger.info("用户数据处理成功")
        print("==========")
        
        # 3. 调用RAG系统
        print("==========")
        print("调用RAG系统开始")
        print("==========")
        logger.info("调用RAG系统的细节日志：开始调用RAG Pipeline进行批量查询")
        results = rag.batch_query(
            questions=request.questions,
            top_k=request.top_k
        )
        logger.info("RAG系统批量查询调用完成")
        logger.info("调用RAG系统成功")
        print("调用RAG系统结束")
        print("==========")
        
        # 4. 返回用户结果
        print("==========")
        print("返回用户结果开始")
        print("==========")
        logger.info("返回用户结果的细节日志：开始构建批量查询API响应")
        response = ResponseModel(
            success=True,
            data={"results": results, "count": len(results)},
            message="Batch query completed successfully",
            timestamp=datetime.now().isoformat()
        )
        logger.info(f"批量查询API响应构建完成，结果数量: {len(results)}")
        logger.info("返回用户结果成功")
        print("返回用户结果结束")
        print("==========")
        
        print("=" * 50)
        print("🎉 API批量查询请求完成")
        print("=" * 50)
        logger.info("API批量查询请求成功完成")
        
        return response
        
    except Exception as e:
        print("=" * 50)
        print("❌ API批量查询请求失败")
        print("=" * 50)
        logger.error(f"API批量查询请求失败: {e}")
        logger.error(f"Error in batch query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats", response_model=ResponseModel)
async def get_system_stats(rag: RAGPipeline = Depends(get_rag_pipeline)):
    """获取系统统计信息"""
    try:
        stats = rag.get_system_stats()
        
        return ResponseModel(
            success=True,
            data=stats,
            message="Statistics retrieved successfully",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save", response_model=ResponseModel)
async def save_system(
    save_dir: str,
    rag: RAGPipeline = Depends(get_rag_pipeline)
):
    """保存系统状态"""
    try:
        rag.save_system(save_dir)
        
        return ResponseModel(
            success=True,
            data={"save_directory": save_dir},
            message="System saved successfully",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error saving system: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/load", response_model=ResponseModel)
async def load_system(
    save_dir: str,
    rag: RAGPipeline = Depends(get_rag_pipeline)
):
    """加载系统状态"""
    try:
        rag.load_system(save_dir)
        
        return ResponseModel(
            success=True,
            data={"load_directory": save_dir},
            message="System loaded successfully",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error loading system: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/clear", response_model=ResponseModel)
async def clear_system(rag: RAGPipeline = Depends(get_rag_pipeline)):
    """清空系统数据"""
    try:
        rag.clear_system()
        
        return ResponseModel(
            success=True,
            message="System cleared successfully",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error clearing system: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 错误处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "timestamp": datetime.now().isoformat()
        }
    )

@app.post("/query/stream")
async def query_documents_stream(
    request: QueryRequest,
    rag: RAGPipeline = Depends(get_rag_pipeline)
):
    """流式查询RAG系统"""
    try:
        print("=" * 50)
        print("🌐 API流式查询请求开始")
        print("=" * 50)
        logger.info("开始处理API流式查询请求...")
        
        def generate_stream():
            try:
                # 调用RAG系统的流式查询
                for chunk in rag.query_stream(
                    question=request.question,
                    top_k=request.top_k,
                    response_type=request.response_type,
                    similarity_threshold=request.similarity_threshold
                ):
                    # 将chunk转换为JSON格式
                    chunk_json = json.dumps(chunk, ensure_ascii=False) + "\n"
                    yield chunk_json
                    
            except Exception as e:
                logger.error(f"流式查询出错：{e}")
                error_chunk = {
                    "type": "error",
                    "message": f"查询出错：{str(e)}"
                }
                yield json.dumps(error_chunk, ensure_ascii=False) + "\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="application/x-ndjson",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )
        
    except Exception as e:
        logger.error(f"流式查询API出错：{e}")
        raise HTTPException(status_code=500, detail=f"流式查询出错：{str(e)}")


if __name__ == "__main__":
    # 运行API服务器
    uvicorn.run(
        "rag_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
