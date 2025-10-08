"""
智诊通向量化服务API
提供文本、图像、多模态向量化服务
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
import asyncio
import logging
from datetime import datetime
import sys
import os

# 添加向量化服务路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'services', 'embedding_service'))

from core.embedding_service import EmbeddingService

# 使用统一日志管理器
import sys
from pathlib import Path

# 添加common模块到路径
current_file = Path(__file__)
common_dir = current_file.parent.parent.parent.parent / "common"
sys.path.insert(0, str(common_dir))

from log_config import setup_embedding_service_logging
logger = setup_embedding_service_logging()

# 创建FastAPI应用
app = FastAPI(
    title="智诊通向量化服务API",
    description="提供文本、图像、多模态向量化服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 创建API路由器，添加路径前缀
from fastapi import APIRouter
api_router = APIRouter(prefix="/api/v1")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局向量化服务实例
embedding_service = None

# 请求模型
class TextVectorizeRequest(BaseModel):
    """文本向量化请求"""
    texts: List[str] = Field(..., description="待向量化的文本列表")
    chunk_strategy: str = Field(default="medical_structured", description="文档切分策略")
    preprocessing: bool = Field(default=True, description="是否进行预处理")
    model_name: Optional[str] = Field(default=None, description="指定模型名称")

class ImageVectorizeRequest(BaseModel):
    """图像向量化请求"""
    image_paths: List[str] = Field(..., description="图像文件路径列表")
    extract_text: bool = Field(default=True, description="是否提取图像中的文本")
    model_name: Optional[str] = Field(default=None, description="指定模型名称")

class MultimodalVectorizeRequest(BaseModel):
    """多模态向量化请求"""
    texts: Optional[List[str]] = Field(default=None, description="文本列表")
    image_paths: Optional[List[str]] = Field(default=None, description="图像路径列表")
    fusion_method: str = Field(default="concat", description="融合方法: concat, add, multiply")
    model_name: Optional[str] = Field(default=None, description="指定模型名称")

class BatchVectorizeRequest(BaseModel):
    """批量向量化请求"""
    data: List[Dict[str, Any]] = Field(..., description="批量数据列表")
    model_name: Optional[str] = Field(default=None, description="指定模型名称")

# 响应模型
class VectorizeResponse(BaseModel):
    """向量化响应"""
    success: bool
    message: str
    data: Dict[str, Any]
    error: Optional[str] = None

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    timestamp: str
    version: str
    services: Dict[str, str]

# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化服务"""
    global embedding_service
    
    try:
        logger.info("🚀 向量化服务启动中...")
        
        # 初始化向量化服务
        embedding_service = EmbeddingService(device="cpu")
        logger.info("✅ 向量化服务初始化完成")
        
        logger.info("🎉 所有服务启动完成")
        
    except Exception as e:
        logger.error(f"❌ 服务启动失败: {str(e)}")
        raise

# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    global embedding_service
    
    try:
        logger.info("🔄 向量化服务关闭中...")
        
        if embedding_service:
            await embedding_service.cleanup()
            logger.info("✅ 向量化服务清理完成")
        
        logger.info("👋 所有服务已关闭")
        
    except Exception as e:
        logger.error(f"❌ 服务关闭失败: {str(e)}")

# API端点
@app.get("/", response_model=HealthResponse)
async def root():
    """根路径健康检查"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0",
        services={
            "embedding": "running" if embedding_service else "stopped"
        }
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查端点"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0",
        services={
            "embedding": "running" if embedding_service else "stopped"
        }
    )

@api_router.post("/vectorize/text", response_model=VectorizeResponse)
async def vectorize_text(request: TextVectorizeRequest):
    """文本向量化"""
    start_time = datetime.now()
    request_id = f"req_{start_time.strftime('%Y%m%d_%H%M%S_%f')}"
    
    try:
        logger.info(f"🔤 [{request_id}] 开始文本向量化请求")
        logger.info(f"📊 [{request_id}] 请求参数: texts_count={len(request.texts)}, chunk_strategy={request.chunk_strategy}, preprocessing={request.preprocessing}")
        
        # 记录输入文本详情
        for i, text in enumerate(request.texts):
            logger.info(f"📝 [{request_id}] 文本 {i+1}: 长度={len(text)} 字符, 内容='{text[:100]}{'...' if len(text) > 100 else ''}'")
        
        if not embedding_service:
            logger.error(f"❌ [{request_id}] 向量化服务未初始化")
            raise HTTPException(status_code=503, detail="向量化服务未初始化")
        
        logger.info(f"🚀 [{request_id}] 开始执行向量化处理")
        
        # 执行向量化
        result = embedding_service.vectorize_text(
            texts=request.texts,
            chunk_strategy=request.chunk_strategy,
            preprocessing=request.preprocessing
        )
        
        # 记录处理结果详情
        processing_time = (datetime.now() - start_time).total_seconds()
        vectors_count = len(result.get('vectors', []))
        dimension = result.get('dimension', 0)
        
        logger.info(f"✅ [{request_id}] 文本向量化完成")
        logger.info(f"📈 [{request_id}] 处理结果: vectors_count={vectors_count}, dimension={dimension}, processing_time={processing_time:.3f}s")
        
        # 记录每个向量的基本信息
        if vectors_count > 0:
            logger.info(f"🔍 [{request_id}] 向量详情:")
            for i, vector in enumerate(result.get('vectors', [])[:3]):  # 只记录前3个向量的详情
                if hasattr(vector, '__len__'):
                    logger.info(f"   📊 [{request_id}] 向量 {i+1}: 维度={len(vector)}, 范围=[{min(vector):.4f}, {max(vector):.4f}]")
                else:
                    logger.info(f"   📊 [{request_id}] 向量 {i+1}: 类型={type(vector)}")
        
        return VectorizeResponse(
            success=True,
            message="文本向量化成功",
            data=result
        )
        
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"❌ [{request_id}] 文本向量化失败: {str(e)}")
        logger.error(f"⏱️ [{request_id}] 失败时间: {processing_time:.3f}s")
        return VectorizeResponse(
            success=False,
            message="文本向量化失败",
            data={},
            error=str(e)
        )

@api_router.post("/vectorize/image", response_model=VectorizeResponse)
async def vectorize_image(request: ImageVectorizeRequest):
    """图像向量化"""
    try:
        if not embedding_service:
            raise HTTPException(status_code=503, detail="向量化服务未初始化")
        
        logger.info(f"🖼️ 开始图像向量化: {len(request.image_paths)} 个图像")
        
        # 执行向量化
        vectors = []
        for image_path in request.image_paths:
            image_result = embedding_service.vectorize_image(
                image_path=image_path,
                preprocessing=True
            )
            if image_result["success"]:
                vectors.append(image_result["vector"])
            else:
                raise Exception(f"图像向量化失败: {image_result.get('error', '未知错误')}")
        
        result = {
            "success": True,
            "vectors": vectors,
            "image_paths": request.image_paths,
            "model_name": "biomedclip",
            "dimension": len(vectors[0]) if vectors else 0,
            "count": len(vectors)
        }
        
        logger.info(f"✅ 图像向量化完成: {len(result.get('vectors', []))} 个向量")
        
        return VectorizeResponse(
            success=True,
            message="图像向量化成功",
            data=result
        )
        
    except Exception as e:
        logger.error(f"❌ 图像向量化失败: {str(e)}")
        return VectorizeResponse(
            success=False,
            message="图像向量化失败",
            data={},
            error=str(e)
        )

@api_router.post("/vectorize/multimodal", response_model=VectorizeResponse)
async def vectorize_multimodal(request: MultimodalVectorizeRequest):
    """多模态向量化"""
    try:
        if not embedding_service:
            raise HTTPException(status_code=503, detail="向量化服务未初始化")
        
        logger.info(f"🔀 开始多模态向量化: 文本={len(request.texts or [])}, 图像={len(request.image_paths or [])}")
        
        # 执行多模态向量化
        result = embedding_service.vectorize_multimodal(
            texts=request.texts,
            image_paths=request.image_paths,
            chunk_strategy="medical_structured",
            preprocessing=True
        )
        
        logger.info(f"✅ 多模态向量化完成: {len(result.get('combined_vectors', []))} 个向量")
        
        return VectorizeResponse(
            success=True,
            message="多模态向量化成功",
            data=result
        )
        
    except Exception as e:
        logger.error(f"❌ 多模态向量化失败: {str(e)}")
        return VectorizeResponse(
            success=False,
            message="多模态向量化失败",
            data={},
            error=str(e)
        )

@api_router.get("/models", response_model=VectorizeResponse)
async def get_models():
    """获取可用模型列表"""
    try:
        if not embedding_service:
            raise HTTPException(status_code=503, detail="向量化服务未初始化")
        
        result = embedding_service.get_available_models()
        
        return VectorizeResponse(
            success=True,
            message="模型列表获取成功",
            data=result
        )
        
    except Exception as e:
        logger.error(f"❌ 获取模型列表失败: {str(e)}")
        return VectorizeResponse(
            success=False,
            message="获取模型列表失败",
            data={},
            error=str(e)
        )

@api_router.get("/stats", response_model=VectorizeResponse)
async def get_stats():
    """获取服务统计信息"""
    try:
        if not embedding_service:
            raise HTTPException(status_code=503, detail="向量化服务未初始化")
        
        stats = embedding_service.get_stats()
        
        return VectorizeResponse(
            success=True,
            message="统计信息获取成功",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"❌ 统计信息获取失败: {str(e)}")
        return VectorizeResponse(
            success=False,
            message="统计信息获取失败",
            data={},
            error=str(e)
        )

# 检索请求模型
class RetrieveRequest(BaseModel):
    """检索请求"""
    query: str = Field(..., description="查询文本")
    top_k: int = Field(default=5, description="返回结果数量")
    retrieval_type: str = Field(default="text", description="检索类型: text, image, multimodal")
    similarity_threshold: float = Field(default=0.3, description="相似度阈值")

@api_router.post("/retrieve", response_model=VectorizeResponse)
async def retrieve_documents(request: RetrieveRequest):
    """文档检索"""
    start_time = datetime.now()
    request_id = f"ret_{start_time.strftime('%Y%m%d_%H%M%S_%f')}"
    
    try:
        logger.info(f"🔍 [{request_id}] 开始文档检索请求")
        logger.info(f"📊 [{request_id}] 检索参数: query='{request.query}', top_k={request.top_k}, retrieval_type={request.retrieval_type}, similarity_threshold={request.similarity_threshold}")
        
        if not embedding_service:
            logger.error(f"❌ [{request_id}] 向量化服务未初始化")
            raise HTTPException(status_code=503, detail="向量化服务未初始化")
        
        logger.info(f"🚀 [{request_id}] 开始执行检索处理")
        
        # 执行检索
        result = embedding_service.retrieve_documents(
            query=request.query,
            top_k=request.top_k,
            retrieval_type=request.retrieval_type,
            similarity_threshold=request.similarity_threshold
        )
        
        # 记录检索结果详情
        processing_time = (datetime.now() - start_time).total_seconds()
        results_count = len(result.get('results', []))
        
        logger.info(f"✅ [{request_id}] 文档检索完成")
        logger.info(f"📈 [{request_id}] 检索结果: results_count={results_count}, processing_time={processing_time:.3f}s")
        
        # 记录每个检索结果的详情
        if results_count > 0:
            logger.info(f"🔍 [{request_id}] 检索结果详情:")
            for i, doc in enumerate(result.get('results', [])[:3]):  # 只记录前3个结果的详情
                similarity = doc.get('similarity_score', 0)
                content_preview = doc.get('content', '')[:50]
                logger.info(f"   📄 [{request_id}] 结果 {i+1}: 相似度={similarity:.4f}, 内容='{content_preview}...'")
        
        return VectorizeResponse(
            success=True,
            message="文档检索成功",
            data=result
        )
        
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"❌ [{request_id}] 文档检索失败: {str(e)}")
        logger.error(f"⏱️ [{request_id}] 失败时间: {processing_time:.3f}s")
        return VectorizeResponse(
            success=False,
            message="文档检索失败",
            data={},
            error=str(e)
        )

# 注册API路由器
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
