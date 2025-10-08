"""
知识检索系统API接口
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

# 导入核心模块
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.retrieval_pipeline import KnowledgeRetrievalPipeline, KnowledgeRetrievalPipelineFactory

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

from common.log_config import get_logger
# 注意：不在这里调用setup_logging，避免重复配置
logger = get_logger("retrieval_service")

# 创建FastAPI应用
app = FastAPI(
    title="知识检索 API",
    description="知识检索与生成一体化 API",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局知识检索流程实例
retrieval_pipeline: Optional[KnowledgeRetrievalPipeline] = None

# Pydantic模型定义
class DocumentModel(BaseModel):
    content: str = Field(..., description="文档内容")
    title: Optional[str] = Field(None, description="文档标题")
    category: Optional[str] = Field(None, description="文档类别")
    source: Optional[str] = Field(None, description="文档来源")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")
    type: Optional[str] = Field("text", description="文档类型")

class ImageDocumentModel(BaseModel):
    image_path: str = Field(..., description="图像文件路径")
    title: Optional[str] = Field(None, description="图像标题")
    category: Optional[str] = Field(None, description="图像类别")
    source: Optional[str] = Field(None, description="图像来源")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")

class QueryRequest(BaseModel):
    question: str = Field(..., description="用户问题")
    top_k: int = Field(5, description="检索文档数量", ge=1, le=20)
    response_type: str = Field("general", description="响应类型")
    similarity_threshold: float = Field(0.5, description="相似度阈值", ge=0.0, le=1.0)

class ChatRequest(BaseModel):
    messages: List[Dict[str, str]] = Field(..., description="对话历史")
    top_k: int = Field(5, description="检索文档数量", ge=1, le=20)
    multimodal_data: Optional[Dict[str, Any]] = Field(None, description="多模态数据")

class SearchRequest(BaseModel):
    query: str = Field(..., description="搜索查询")
    search_type: str = Field("hybrid", description="搜索类型")
    top_k: int = Field(3, description="返回文档数量", ge=1, le=50)

class BatchQueryRequest(BaseModel):
    questions: List[str] = Field(..., description="问题列表")
    top_k: int = Field(5, description="检索文档数量", ge=1, le=20)

class ResponseModel(BaseModel):
    success: bool = Field(..., description="是否成功")
    data: Optional[Dict[str, Any]] = Field(None, description="响应数据")
    message: Optional[str] = Field(None, description="响应消息")
    timestamp: str = Field(..., description="时间戳")

# 依赖注入
def get_retrieval_pipeline() -> KnowledgeRetrievalPipeline:
    global retrieval_pipeline
    if retrieval_pipeline is None:
        raise HTTPException(status_code=503, detail="Retrieval pipeline not initialized")
    return retrieval_pipeline

# 启动事件
@app.on_event("startup")
async def startup_event():
    global retrieval_pipeline
    try:
        logger.info("Initializing retrieval pipeline...")
        retrieval_pipeline = KnowledgeRetrievalPipelineFactory.create_pipeline()
        logger.info("Retrieval pipeline initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing retrieval pipeline: {e}")
        raise

# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    global retrieval_pipeline
    if retrieval_pipeline:
        try:
            retrieval_pipeline.clear_system()
            logger.info("Retrieval pipeline cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up retrieval pipeline: {e}")

# API路由
@app.get("/", response_model=ResponseModel)
async def root():
    return ResponseModel(
        success=True,
        data={
            "api_name": "知识检索 API",
            "version": "1.0.0",
            "status": "running"
        },
        message="API is running",
        timestamp=datetime.now().isoformat()
    )

@app.get("/health", response_model=ResponseModel)
async def health_check():
    logger.info("🔍 收到健康检查请求")
    try:
        pipeline = get_retrieval_pipeline()
        stats = pipeline.get_system_stats()
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

@app.post("/process/unified", response_model=ResponseModel)
async def process_unified_multimodal(
    request: dict,
    pipeline: KnowledgeRetrievalPipeline = Depends(get_retrieval_pipeline)
):
    try:
        logger.info(f"收到统一多模态处理请求: {request}")
        text = request.get("text")
        image_data = request.get("image_data")
        audio_data = request.get("audio_data")
        user_id = request.get("user_id")
        session_id = request.get("session_id")

        if not text and not image_data and not audio_data:
            raise HTTPException(status_code=400, detail="至少需要提供文本、图片或音频中的一种输入")

        result = {
            "text_result": {},
            "audio_result": {},
            "image_result": {},
            "fusion_result": {},
            "confidence_score": 0.0,
            "processing_time": 0.0
        }

        if text:
            logger.info("处理文本输入")
            text_query = QueryRequest(question=text, top_k=5, response_type="general", similarity_threshold=0.5)
            text_response = pipeline.query(
                question=text_query.question,
                top_k=text_query.top_k,
                response_type=text_query.response_type,
                similarity_threshold=text_query.similarity_threshold
            )
            result["text_result"] = {
                "answer": text_response.get("answer", ""),
                "retrieved_documents": text_response.get("retrieved_documents", []),
                "confidence": text_response.get("confidence", 0.0)
            }

        if image_data:
            logger.info("处理图片输入")
            try:
                image_search_result = pipeline.vectorization_client.search_multimodal(
                    texts=[text] if text else None,
                    image_paths=[image_data.get("file_path")] if image_data.get("file_path") else None,
                    top_k=5,
                    search_type="semantic",
                    similarity_threshold=0.5,
                    fusion_method="concat"
                )
                if image_search_result["success"]:
                    result["image_result"] = {
                        "filename": image_data.get("filename", ""),
                        "content_type": image_data.get("content_type", ""),
                        "size": image_data.get("size", 0),
                        "retrieved_documents": image_search_result.get("documents", []),
                        "confidence": 0.8,
                        "description": f"图片检索完成，找到 {len(image_search_result.get('documents', []))} 个相关文档"
                    }
                else:
                    result["image_result"] = {
                        "filename": image_data.get("filename", ""),
                        "content_type": image_data.get("content_type", ""),
                        "size": image_data.get("size", 0),
                        "error": image_search_result.get("error", "图片检索失败"),
                        "description": "图片检索失败"
                    }
            except Exception as e:
                logger.error(f"图片处理失败: {e}")
                result["image_result"] = {
                    "filename": image_data.get("filename", ""),
                    "content_type": image_data.get("content_type", ""),
                    "size": image_data.get("size", 0),
                    "error": str(e),
                    "description": "图片处理异常"
                }

        if audio_data:
            logger.info("处理音频输入")
            result["audio_result"] = {
                "filename": audio_data.get("filename", ""),
                "content_type": audio_data.get("content_type", ""),
                "size": audio_data.get("size", 0),
                "transcription": "语音转文字功能待实现"
            }

        if (text and image_data) or (text and audio_data) or (image_data and audio_data):
            logger.info("执行多模态融合处理")
            result["fusion_result"] = {
                "fused_answer": "多模态融合处理完成",
                "modality_weights": {
                    "text": 0.4 if text else 0.0,
                    "image": 0.3 if image_data else 0.0,
                    "audio": 0.3 if audio_data else 0.0
                }
            }

        confidence_scores = []
        if result["text_result"].get("confidence"):
            confidence_scores.append(result["text_result"]["confidence"])
        if result["audio_result"].get("confidence"):
            confidence_scores.append(result["audio_result"]["confidence"])
        if result["image_result"].get("confidence"):
            confidence_scores.append(result["image_result"]["confidence"])
        result["confidence_score"] = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0

        logger.info(f"统一多模态处理完成: {result}")
        return ResponseModel(success=True, data=result, message="统一多模态处理成功", timestamp=datetime.now().isoformat())
    except Exception as e:
        logger.error(f"统一多模态处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"统一多模态处理失败: {str(e)}")

@app.post("/query", response_model=ResponseModel)
async def query_documents(
    request: QueryRequest,
    pipeline: KnowledgeRetrievalPipeline = Depends(get_retrieval_pipeline)
):
    logger.info(f"🔍 收到查询请求: {request.question[:50]}...")
    logger.info(f"📊 查询参数: top_k={request.top_k}, threshold={request.similarity_threshold}")
    try:
        result = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None,
                lambda: pipeline.query(
                    question=request.question,
                    top_k=request.top_k,
                    response_type=request.response_type,
                    similarity_threshold=request.similarity_threshold
                )
            ),
            timeout=300.0
        )
        return ResponseModel(success=True, data=result, message="Query completed successfully", timestamp=datetime.now().isoformat())
    except asyncio.TimeoutError:
        logger.error("检索调用超时")
        raise HTTPException(status_code=408, detail="查询超时，请稍后重试")
    except Exception as e:
        logger.error(f"API查询请求失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ResponseModel)
async def chat(
    request: ChatRequest,
    pipeline: KnowledgeRetrievalPipeline = Depends(get_retrieval_pipeline)
):
    try:
        result = pipeline.chat(messages=request.messages, top_k=request.top_k, multimodal_data=request.multimodal_data or {})
        return ResponseModel(success=True, data=result, message="Chat completed successfully", timestamp=datetime.now().isoformat())
    except Exception as e:
        logger.error(f"API对话请求失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search", response_model=ResponseModel)
async def search_documents(
    request: SearchRequest,
    pipeline: KnowledgeRetrievalPipeline = Depends(get_retrieval_pipeline)
):
    try:
        results = pipeline.search_documents(query=request.query, search_type=request.search_type, top_k=request.top_k)
        return ResponseModel(success=True, data={"documents": results, "count": len(results)}, message="Search completed successfully", timestamp=datetime.now().isoformat())
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/batch_query", response_model=ResponseModel)
async def batch_query_documents(
    request: BatchQueryRequest,
    pipeline: KnowledgeRetrievalPipeline = Depends(get_retrieval_pipeline)
):
    try:
        results = pipeline.batch_query(questions=request.questions, top_k=request.top_k)
        return ResponseModel(success=True, data={"results": results, "count": len(results)}, message="Batch query completed successfully", timestamp=datetime.now().isoformat())
    except Exception as e:
        logger.error(f"Error in batch query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats", response_model=ResponseModel)
async def get_system_stats(pipeline: KnowledgeRetrievalPipeline = Depends(get_retrieval_pipeline)):
    try:
        stats = pipeline.get_system_stats()
        return ResponseModel(success=True, data=stats, message="Statistics retrieved successfully", timestamp=datetime.now().isoformat())
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save", response_model=ResponseModel)
async def save_system(save_dir: str, pipeline: KnowledgeRetrievalPipeline = Depends(get_retrieval_pipeline)):
    try:
        pipeline.save_system(save_dir)
        return ResponseModel(success=True, data={"save_directory": save_dir}, message="System saved successfully", timestamp=datetime.now().isoformat())
    except Exception as e:
        logger.error(f"Error saving system: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/load", response_model=ResponseModel)
async def load_system(save_dir: str, pipeline: KnowledgeRetrievalPipeline = Depends(get_retrieval_pipeline)):
    try:
        pipeline.load_system(save_dir)
        return ResponseModel(success=True, data={"load_directory": save_dir}, message="System loaded successfully", timestamp=datetime.now().isoformat())
    except Exception as e:
        logger.error(f"Error loading system: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/clear", response_model=ResponseModel)
async def clear_system(pipeline: KnowledgeRetrievalPipeline = Depends(get_retrieval_pipeline)):
    try:
        pipeline.clear_system()
        return ResponseModel(success=True, message="System cleared successfully", timestamp=datetime.now().isoformat())
    except Exception as e:
        logger.error(f"Error clearing system: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query/stream")
async def query_documents_stream(
    request: QueryRequest,
    pipeline: KnowledgeRetrievalPipeline = Depends(get_retrieval_pipeline)
):
    try:
        async def generate_stream():
            try:
                async for chunk in pipeline.query_stream(
                    question=request.question,
                    top_k=request.top_k,
                    response_type=request.response_type,
                    similarity_threshold=request.similarity_threshold
                ):
                    yield json.dumps(chunk, ensure_ascii=False) + "\n"
            except Exception as e:
                logger.error(f"流式查询出错：{e}")
                yield json.dumps({"type": "error", "message": f"查询出错：{str(e)}"}, ensure_ascii=False) + "\n"

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
    import uvicorn
    uvicorn.run(
        "retrieval_api:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )


