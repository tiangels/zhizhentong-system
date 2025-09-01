"""
知识库API路由
处理医疗知识检索和管理
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from ..database import get_db
from ..auth import get_current_user
from ..models.user import User
from ..models.knowledge import (
    MedicalKnowledge, MedicalKnowledgeCreate, MedicalKnowledgeResponse,
    KnowledgeRetrievalRequest, KnowledgeRetrievalResponse
)
from ..modules.rag import RAGRetrieval, RetrievalInput

router = APIRouter(prefix="/knowledge", tags=["知识库"])

# 创建RAG检索实例
rag_retrieval = RAGRetrieval()


@router.post("/retrieve", response_model=KnowledgeRetrievalResponse, summary="检索知识")
async def retrieve_knowledge(
    retrieval_request: KnowledgeRetrievalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    检索相关知识
    
    - **query**: 查询文本
    - **limit**: 返回结果数量限制
    - **context**: 上下文信息（可选）
    """
    # 准备检索输入
    retrieval_input = RetrievalInput(
        query=retrieval_request.query,
        limit=retrieval_request.limit,
        context=retrieval_request.context
    )
    
    # 执行检索
    retrieval_output = rag_retrieval.retrieve(retrieval_input)
    
    # 转换为响应格式
    retrieved_knowledge = []
    for item in retrieval_output.retrieved_knowledge:
        retrieved_knowledge.append(MedicalKnowledgeResponse(
            id=item.get('id', ''),
            title=item.get('title', ''),
            content=item.get('content', ''),
            category=item.get('category', ''),
            tags=item.get('tags', []),
            source=item.get('source', ''),
            vector_id=item.get('vector_id', ''),
            created_at=item.get('created_at', datetime.now()),
            updated_at=item.get('updated_at', datetime.now())
        ))
    
    return KnowledgeRetrievalResponse(
        query=retrieval_output.query,
        retrieved_knowledge=retrieved_knowledge,
        relevance_scores=retrieval_output.relevance_scores,
        processing_time=retrieval_output.processing_time
    )


@router.get("/", response_model=List[MedicalKnowledgeResponse], summary="获取知识列表")
async def get_knowledge_list(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回记录数"),
    category: Optional[str] = Query(None, description="分类过滤"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取知识列表
    
    - **skip**: 跳过记录数（分页用）
    - **limit**: 返回记录数（最大100）
    - **category**: 分类过滤（可选）
    """
    query = db.query(MedicalKnowledge)
    
    if category:
        query = query.filter(MedicalKnowledge.category == category)
    
    knowledge_items = query.order_by(MedicalKnowledge.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        MedicalKnowledgeResponse(
            id=str(item.id),
            title=item.title,
            content=item.content,
            category=item.category,
            tags=item.tags,
            source=item.source,
            vector_id=item.vector_id,
            created_at=item.created_at,
            updated_at=item.updated_at
        )
        for item in knowledge_items
    ]


# 将具体路径放在参数化路径之前
@router.get("/categories/list", summary="获取知识分类列表")
async def get_knowledge_categories(
    db: Session = Depends(get_db)
):
    """
    获取所有知识分类列表
    """
    categories = db.query(MedicalKnowledge.category).distinct().all()
    
    return {
        "categories": [cat[0] for cat in categories if cat[0]],
        "total": len(categories)
    }


@router.get("/tags/list", summary="获取知识标签列表")
async def get_knowledge_tags(
    db: Session = Depends(get_db)
):
    """
    获取所有知识标签列表
    """
    # 获取所有标签
    all_tags = []
    knowledge_items = db.query(MedicalKnowledge.tags).all()
    
    for item in knowledge_items:
        if item.tags:
            all_tags.extend(item.tags)
    
    # 去重并统计
    unique_tags = list(set(all_tags))
    tag_counts = {}
    
    for tag in unique_tags:
        # 使用字符串包含查询而不是数组包含查询
        count = db.query(MedicalKnowledge).filter(
            func.array_to_string(MedicalKnowledge.tags, ',').contains(tag)
        ).count()
        tag_counts[tag] = count
    
    return {
        "tags": unique_tags,
        "tag_counts": tag_counts,
        "total": len(unique_tags)
    }


@router.get("/stats/summary", summary="获取知识库统计摘要")
async def get_knowledge_stats(
    db: Session = Depends(get_db)
):
    """
    获取知识库统计摘要
    """
    # 总知识数量
    total_knowledge = db.query(MedicalKnowledge).count()
    
    # 分类统计
    category_stats = db.query(
        MedicalKnowledge.category,
        func.count(MedicalKnowledge.id)
    ).group_by(MedicalKnowledge.category).all()
    
    # 来源统计
    source_stats = db.query(
        MedicalKnowledge.source,
        func.count(MedicalKnowledge.id)
    ).group_by(MedicalKnowledge.source).all()
    
    return {
        "total_knowledge": total_knowledge,
        "category_distribution": dict(category_stats),
        "source_distribution": dict(source_stats),
        "categories_count": len(category_stats),
        "sources_count": len(source_stats)
    }


@router.get("/{knowledge_id}", response_model=MedicalKnowledgeResponse, summary="获取知识详情")
async def get_knowledge_detail(
    knowledge_id: str,
    db: Session = Depends(get_db)
):
    """
    获取指定知识的详情
    
    - **knowledge_id**: 知识ID
    """
    knowledge = db.query(MedicalKnowledge).filter(MedicalKnowledge.id == knowledge_id).first()
    
    if not knowledge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识不存在"
        )
    
    return MedicalKnowledgeResponse(
        id=str(knowledge.id),
        title=knowledge.title,
        content=knowledge.content,
        category=knowledge.category,
        tags=knowledge.tags,
        source=knowledge.source,
        vector_id=knowledge.vector_id,
        created_at=knowledge.created_at,
        updated_at=knowledge.updated_at
    )


@router.put("/{knowledge_id}", response_model=MedicalKnowledgeResponse, summary="更新知识")
async def update_knowledge(
    knowledge_id: str,
    knowledge_update: MedicalKnowledgeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新知识信息
    
    - **knowledge_id**: 知识ID
    - **knowledge_update**: 更新的知识信息
    """
    knowledge = db.query(MedicalKnowledge).filter(MedicalKnowledge.id == knowledge_id).first()
    
    if not knowledge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识不存在"
        )
    
    # 更新知识信息
    knowledge.title = knowledge_update.title
    knowledge.content = knowledge_update.content
    knowledge.category = knowledge_update.category
    knowledge.tags = knowledge_update.tags
    knowledge.source = knowledge_update.source
    
    db.commit()
    db.refresh(knowledge)
    
    return MedicalKnowledgeResponse(
        id=str(knowledge.id),
        title=knowledge.title,
        content=knowledge.content,
        category=knowledge.category,
        tags=knowledge.tags,
        source=knowledge.source,
        vector_id=knowledge.vector_id,
        created_at=knowledge.created_at,
        updated_at=knowledge.updated_at
    )


@router.delete("/{knowledge_id}", summary="删除知识")
async def delete_knowledge(
    knowledge_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除知识
    
    - **knowledge_id**: 知识ID
    """
    knowledge = db.query(MedicalKnowledge).filter(MedicalKnowledge.id == knowledge_id).first()
    
    if not knowledge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识不存在"
        )
    
    db.delete(knowledge)
    db.commit()
    
    return {"message": "知识删除成功"}