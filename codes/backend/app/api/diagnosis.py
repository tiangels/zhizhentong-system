"""
诊断API路由
处理智能诊断相关功能
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..auth import get_current_user
from ..models.user import User
from ..models.diagnosis import (
    Diagnosis, DiagnosisCreate, DiagnosisResponse, DiagnosisRequest,
    DiagnosisAnalysisResponse
)
from ..modules.diagnosis import DiagnosisEngine, DiagnosisInput, DiagnosisOutput

router = APIRouter(prefix="/diagnosis", tags=["诊断"])

# 创建诊断引擎实例
diagnosis_engine = DiagnosisEngine()


@router.post("/analyze", response_model=DiagnosisAnalysisResponse, summary="智能诊断分析")
async def analyze_diagnosis(
    diagnosis_request: DiagnosisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    执行智能诊断分析
    
    - **symptoms**: 症状描述
    - **user_context**: 用户上下文信息（可选）
    - **conversation_id**: 对话ID（可选）
    """
    # 准备诊断输入
    diagnosis_input = DiagnosisInput(
        symptoms=diagnosis_request.symptoms,
        user_context=diagnosis_request.user_context,
        conversation_id=diagnosis_request.conversation_id
    )
    
    # 执行诊断
    diagnosis_output = diagnosis_engine.diagnose(diagnosis_input)
    
    # 保存诊断记录到数据库
    diagnosis_record = Diagnosis(
        user_id=current_user.id,
        conversation_id=diagnosis_request.conversation_id,
        symptoms=diagnosis_request.symptoms,
        diagnosis_result=diagnosis_output.model_dump(),
        confidence_score=diagnosis_output.overall_confidence,
        risk_level=diagnosis_output.risk_assessment.get('disease_risk', 'low'),
        recommendations=str(diagnosis_output.recommendations)
    )
    
    db.add(diagnosis_record)
    db.commit()
    db.refresh(diagnosis_record)
    
    # 构建响应
    diagnosis_results = []
    for result in diagnosis_output.results:
        diagnosis_results.append({
            "disease": result.get('disease', ''),
            "confidence": result.get('confidence', 0.0),
            "severity": result.get('severity', 'moderate'),
            "risk_level": result.get('risk_level', 'low'),
            "urgency": result.get('urgency', 'normal'),
            "recommendations": result.get('differential_diagnosis', [])
        })
    
    return DiagnosisAnalysisResponse(
        diagnosis_id=str(diagnosis_record.id),
        results=diagnosis_results,
        overall_confidence=diagnosis_output.overall_confidence,
        risk_assessment=diagnosis_output.risk_assessment,
        recommendations=diagnosis_output.recommendations,
        processing_time=diagnosis_output.processing_time
    )


# 将具体路径放在参数化路径之前
@router.get("/stats/summary", summary="获取诊断统计摘要")
async def get_diagnosis_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取当前用户的诊断统计摘要
    """
    # 获取诊断记录总数
    total_diagnoses = db.query(Diagnosis).filter(Diagnosis.user_id == current_user.id).count()
    
    # 获取不同风险等级的统计
    risk_stats = db.query(Diagnosis.risk_level, func.count(Diagnosis.id)).filter(
        Diagnosis.user_id == current_user.id
    ).group_by(Diagnosis.risk_level).all()
    
    # 获取平均置信度
    avg_confidence = db.query(func.avg(Diagnosis.confidence_score)).filter(
        Diagnosis.user_id == current_user.id
    ).scalar() or 0.0
    
    # 获取最近的诊断记录
    recent_diagnoses = db.query(Diagnosis).filter(
        Diagnosis.user_id == current_user.id
    ).order_by(Diagnosis.created_at.desc()).limit(5).all()
    
    return {
        "total_diagnoses": total_diagnoses,
        "risk_distribution": dict(risk_stats),
        "average_confidence": float(avg_confidence),
        "recent_diagnoses": [
            {
                "id": str(diag.id),
                "symptoms": diag.symptoms,
                "risk_level": diag.risk_level,
                "confidence_score": diag.confidence_score,
                "created_at": diag.created_at
            }
            for diag in recent_diagnoses
        ]
    }


@router.get("/engine/stats", summary="获取诊断引擎统计")
async def get_diagnosis_engine_stats():
    """
    获取诊断引擎的统计信息
    """
    stats = diagnosis_engine.get_diagnosis_stats()
    
    return {
        "engine_stats": stats,
        "module_info": {
            "symptom_analyzer": "症状分析器",
            "risk_assessor": "风险评估器",
            "result_generator": "结果生成器"
        }
    }


@router.get("/", response_model=List[DiagnosisResponse], summary="获取诊断记录")
async def get_diagnoses(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回记录数"),
    conversation_id: Optional[str] = Query(None, description="对话ID过滤"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取当前用户的诊断记录列表
    
    - **skip**: 跳过记录数（分页用）
    - **limit**: 返回记录数（最大100）
    - **conversation_id**: 对话ID过滤（可选）
    """
    query = db.query(Diagnosis).filter(Diagnosis.user_id == current_user.id)
    
    if conversation_id:
        query = query.filter(Diagnosis.conversation_id == conversation_id)
    
    diagnoses = query.order_by(Diagnosis.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        DiagnosisResponse(
            id=str(diag.id),
            user_id=str(diag.user_id),
            conversation_id=str(diag.conversation_id) if diag.conversation_id else None,
            symptoms=diag.symptoms,
            diagnosis_result=diag.diagnosis_result,
            confidence_score=diag.confidence_score,
            risk_level=diag.risk_level,
            recommendations=diag.recommendations,
            created_at=diag.created_at
        )
        for diag in diagnoses
    ]


@router.get("/{diagnosis_id}", response_model=DiagnosisResponse, summary="获取诊断详情")
async def get_diagnosis(
    diagnosis_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取指定诊断记录的详情
    
    - **diagnosis_id**: 诊断记录ID
    """
    diagnosis = db.query(Diagnosis).filter(
        Diagnosis.id == diagnosis_id,
        Diagnosis.user_id == current_user.id
    ).first()
    
    if not diagnosis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="诊断记录不存在"
        )
    
    return DiagnosisResponse(
        id=str(diagnosis.id),
        user_id=str(diagnosis.user_id),
        conversation_id=str(diagnosis.conversation_id) if diagnosis.conversation_id else None,
        symptoms=diagnosis.symptoms,
        diagnosis_result=diagnosis.diagnosis_result,
        confidence_score=diagnosis.confidence_score,
        risk_level=diagnosis.risk_level,
        recommendations=diagnosis.recommendations,
        created_at=diagnosis.created_at
    )


@router.delete("/{diagnosis_id}", summary="删除诊断记录")
async def delete_diagnosis(
    diagnosis_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除诊断记录
    
    - **diagnosis_id**: 诊断记录ID
    """
    diagnosis = db.query(Diagnosis).filter(
        Diagnosis.id == diagnosis_id,
        Diagnosis.user_id == current_user.id
    ).first()
    
    if not diagnosis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="诊断记录不存在"
        )
    
    db.delete(diagnosis)
    db.commit()
    
    return {"message": "诊断记录删除成功"}