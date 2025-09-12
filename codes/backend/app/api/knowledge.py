"""
知识管理API路由
处理知识库文档的增删改查和RAG系统管理
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from ..database import get_db
from ..auth import get_current_user
from ..models.user import User
from ..services.rag_service import get_rag_service
import json
import logging

router = APIRouter(prefix="/knowledge", tags=["知识管理"])
logger = logging.getLogger(__name__)


@router.get("/status", summary="获取RAG服务状态")
async def get_rag_status():
    """
    获取RAG服务的运行状态
    
    Returns:
        RAG服务状态信息
    """
    try:
        rag_service = get_rag_service()
        service_info = rag_service.get_service_info()
        
        return {
            "status": "success",
            "data": service_info
        }
        
    except Exception as e:
        logger.error(f"获取RAG服务状态失败: {e}")
        return {
            "status": "error",
            "message": f"获取服务状态失败: {str(e)}"
        }


@router.post("/documents", summary="添加知识文档")
async def add_knowledge_documents(
    documents: List[dict],
    current_user: User = Depends(get_current_user)
):
    """
    添加知识文档到RAG系统
    
    - **documents**: 文档列表，每个文档包含title, content, source等字段
    
    Returns:
        添加结果
    """
    try:
        if not documents:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文档列表不能为空"
            )
        
        # 验证文档格式
        for doc in documents:
            if not doc.get('content'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="文档内容不能为空"
                )
        
        rag_service = get_rag_service()
        
        if not rag_service.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="RAG服务不可用"
            )
        
        # 添加文档到RAG系统
        success = await rag_service.add_knowledge_documents(documents)
        
        if success:
            return {
                "status": "success",
                "message": f"成功添加 {len(documents)} 个文档",
                "document_count": len(documents)
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="添加文档失败"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加知识文档失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"添加文档失败: {str(e)}"
        )


@router.post("/query", summary="查询知识库")
async def query_knowledge(
    question: str,
    top_k: int = Query(5, ge=1, le=20, description="返回文档数量"),
    current_user: User = Depends(get_current_user)
):
    """
    查询知识库
    
    - **question**: 查询问题
    - **top_k**: 返回文档数量（1-20）
    
    Returns:
        查询结果
    """
    try:
        if not question.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="查询问题不能为空"
            )
        
        rag_service = get_rag_service()
        
        if not rag_service.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="RAG服务不可用"
            )
        
        # 查询知识库
        result = await rag_service.query_knowledge(question, top_k=top_k)
        
        if result.get('success'):
            return {
                "status": "success",
                "data": result.get('result', {})
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"查询失败: {result.get('error', 'Unknown error')}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询知识库失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询失败: {str(e)}"
        )


@router.post("/upload", summary="上传知识文档文件")
async def upload_knowledge_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    上传知识文档文件（支持JSON格式）
    
    - **file**: 上传的文件（JSON格式）
    
    Returns:
        上传结果
    """
    try:
        if not file.filename.endswith('.json'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只支持JSON格式文件"
            )
        
        # 读取文件内容
        content = await file.read()
        
        try:
            documents = json.loads(content.decode('utf-8'))
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"JSON格式错误: {str(e)}"
            )
        
        if not isinstance(documents, list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文档格式错误，应为数组格式"
            )
        
        # 验证文档格式
        for i, doc in enumerate(documents):
            if not isinstance(doc, dict):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"第{i+1}个文档格式错误，应为对象格式"
                )
            if not doc.get('content'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"第{i+1}个文档缺少content字段"
                )
        
        rag_service = get_rag_service()
        
        if not rag_service.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="RAG服务不可用"
            )
        
        # 添加文档到RAG系统
        success = await rag_service.add_knowledge_documents(documents)
        
        if success:
            return {
                "status": "success",
                "message": f"成功上传并添加 {len(documents)} 个文档",
                "filename": file.filename,
                "document_count": len(documents)
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="添加文档失败"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传知识文档失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上传失败: {str(e)}"
        )


@router.get("/test", summary="测试RAG服务")
async def test_rag_service(
    question: str = Query("什么是感冒？", description="测试问题"),
    current_user: User = Depends(get_current_user)
):
    """
    测试RAG服务功能
    
    - **question**: 测试问题
    
    Returns:
        测试结果
    """
    try:
        rag_service = get_rag_service()
        
        if not rag_service.is_available():
            return {
                "status": "error",
                "message": "RAG服务不可用",
                "service_info": rag_service.get_service_info()
            }
        
        # 测试查询
        result = await rag_service.query_knowledge(question, top_k=3)
        
        # 测试对话生成
        chat_result = await rag_service.generate_response(question)
        
        return {
            "status": "success",
            "message": "RAG服务测试完成",
            "service_info": rag_service.get_service_info(),
            "query_test": result,
            "chat_test": chat_result
        }
        
    except Exception as e:
        logger.error(f"测试RAG服务失败: {e}")
        return {
            "status": "error",
            "message": f"测试失败: {str(e)}",
            "service_info": get_rag_service().get_service_info() if get_rag_service() else None
        }