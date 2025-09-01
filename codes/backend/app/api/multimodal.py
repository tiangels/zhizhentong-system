"""
多模态处理API路由
处理文本、音频、图像等多种模态的输入
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from ..database import get_db
from ..auth import get_current_user
from ..models.user import User
from ..models.multimodal import (
    MultimodalInput, MultimodalOutput, MultimodalInputCreate, MultimodalOutputResponse,
    TextProcessingRequest, TextProcessingResponse, AudioProcessingRequest, 
    AudioProcessingResponse, ImageProcessingRequest, ImageProcessingResponse,
    FusionRequest, FusionResponse
)
from ..modules.multimodal import MultimodalProcessor, TextProcessor, AudioProcessor, ImageProcessor, ModalityFusion

router = APIRouter(prefix="/multimodal", tags=["多模态处理"])

# 创建处理器实例
multimodal_processor = MultimodalProcessor()
text_processor = TextProcessor()
audio_processor = AudioProcessor()
image_processor = ImageProcessor()
fusion_processor = ModalityFusion()


@router.post("/process", response_model=MultimodalOutputResponse, summary="多模态综合处理")
async def process_multimodal(
    multimodal_input: MultimodalInputCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    处理多模态输入（文本、音频、图像）
    
    - **text_data**: 文本数据（可选）
    - **audio_data**: 音频数据（可选）
    - **image_data**: 图像数据（可选）
    - **user_id**: 用户ID
    - **session_id**: 会话ID（可选）
    """
    # 创建多模态输入记录
    db_input = MultimodalInput(
        user_id=current_user.id,
        session_id=multimodal_input.session_id,
        text_data=multimodal_input.text_data,
        audio_data=multimodal_input.audio_data,
        image_data=multimodal_input.image_data,
        input_type="multimodal"
    )
    
    db.add(db_input)
    db.commit()
    db.refresh(db_input)
    
    # 执行多模态处理
    try:
        # 准备输入数据
        input_data = MultimodalInput(
            text_data=multimodal_input.text_data,
            audio_data=multimodal_input.audio_data,
            image_data=multimodal_input.image_data
        )
        
        # 处理多模态数据
        output = multimodal_processor.process_input(input_data)
        
        # 创建输出记录
        db_output = MultimodalOutput(
            input_id=db_input.id,
            user_id=current_user.id,
            session_id=multimodal_input.session_id,
            text_result=output.dict() if hasattr(output, 'dict') else {},
            audio_result=None,
            image_result=None,
            fusion_result=output.dict() if hasattr(output, 'dict') else {},
            confidence_score=output.confidence,
            processing_time=output.processing_time
        )
        
        db.add(db_output)
        db.commit()
        db.refresh(db_output)
        
        return MultimodalOutputResponse(
            id=str(db_output.id),
            input_id=str(db_input.id),
            user_id=str(db_output.user_id),
            session_id=db_output.session_id,
            text_result=db_output.text_result,
            audio_result=db_output.audio_result,
            image_result=db_output.image_result,
            fusion_result=db_output.fusion_result,
            confidence_score=db_output.confidence_score,
            processing_time=db_output.processing_time,
            created_at=db_output.created_at
        )
        
    except Exception as e:
        # 如果处理失败，记录错误信息
        db_output = MultimodalOutput(
            input_id=db_input.id,
            user_id=current_user.id,
            session_id=multimodal_input.session_id,
            text_result={"error": str(e)},
            audio_result={"error": str(e)},
            image_result={"error": str(e)},
            fusion_result={"error": str(e)},
            confidence_score=0.0,
            processing_time=0.0
        )
        
        db.add(db_output)
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"多模态处理失败: {str(e)}"
        )


@router.post("/text", response_model=TextProcessingResponse, summary="文本处理")
async def process_text(
    text_request: TextProcessingRequest,
    current_user: User = Depends(get_current_user)
):
    """
    处理文本输入
    
    - **text**: 输入文本
    - **language**: 语言（可选，默认中文）
    - **processing_type**: 处理类型（可选）
    """
    try:
        # 执行文本处理
        result = text_processor.process_text(
            text=text_request.text
        )
        
        # 处理sentiment字段，如果是字典则提取主要情感
        sentiment_data = result.get('sentiment', {})
        sentiment_str = sentiment_data.get('primary', 'neutral') if isinstance(sentiment_data, dict) else str(sentiment_data)
        
        return TextProcessingResponse(
            processed_text=result.get('cleaned_text', text_request.text),
            entities=result.get('entities', []),
            sentiment=sentiment_str,
            confidence=result.get('confidence', 0.0),
            processing_time=result.get('processing_time', 0.0)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文本处理失败: {str(e)}"
        )


@router.post("/audio", response_model=AudioProcessingResponse, summary="音频处理")
async def process_audio(
    audio_request: AudioProcessingRequest,
    current_user: User = Depends(get_current_user)
):
    """
    处理音频输入
    
    - **audio_data**: 音频数据（base64编码）
    - **audio_format**: 音频格式
    - **sample_rate**: 采样率（可选）
    - **processing_type**: 处理类型（可选）
    """
    try:
        # 执行音频处理
        result = audio_processor.process_audio(
            audio_data=audio_request.audio_data,
            audio_format=audio_request.audio_format,
            sample_rate=audio_request.sample_rate,
            processing_type=audio_request.processing_type
        )
        
        return AudioProcessingResponse(
            transcription=result.transcription,
            speaker_id=result.speaker_id,
            emotion=result.emotion,
            confidence_score=result.confidence_score,
            processing_time=result.processing_time
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"音频处理失败: {str(e)}"
        )


@router.post("/audio/upload", response_model=AudioProcessingResponse, summary="音频文件上传处理")
async def process_audio_file(
    audio_file: UploadFile = File(..., description="音频文件"),
    processing_type: Optional[str] = Form(None, description="处理类型"),
    current_user: User = Depends(get_current_user)
):
    """
    上传并处理音频文件
    
    - **audio_file**: 音频文件（支持多种格式）
    - **processing_type**: 处理类型（可选）
    """
    # 检查文件类型
    allowed_types = ["audio/wav", "audio/mp3", "audio/mpeg", "audio/ogg", "audio/flac"]
    if audio_file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不支持的音频文件格式"
        )
    
    try:
        # 读取文件内容
        audio_content = await audio_file.read()
        
        # 转换为base64
        import base64
        audio_data = base64.b64encode(audio_content).decode('utf-8')
        
        # 执行音频处理
        result = audio_processor.process_audio(
            audio_data=audio_data,
            audio_format=audio_file.content_type,
            processing_type=processing_type
        )
        
        return AudioProcessingResponse(
            transcription=result.transcription,
            speaker_id=result.speaker_id,
            emotion=result.emotion,
            confidence_score=result.confidence_score,
            processing_time=result.processing_time
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"音频文件处理失败: {str(e)}"
        )


@router.post("/image", response_model=ImageProcessingResponse, summary="图像处理")
async def process_image(
    image_request: ImageProcessingRequest,
    current_user: User = Depends(get_current_user)
):
    """
    处理图像输入
    
    - **image_data**: 图像数据（base64编码）
    - **image_format**: 图像格式
    - **processing_type**: 处理类型（可选）
    """
    try:
        # 执行图像处理
        result = image_processor.process_image(
            image_data=image_request.image_data,
            image_format=image_request.image_format,
            processing_type=image_request.processing_type
        )
        
        return ImageProcessingResponse(
            features=result.features,
            symptoms=result.symptoms,
            quality_score=result.quality_score,
            confidence_score=result.confidence_score,
            processing_time=result.processing_time
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"图像处理失败: {str(e)}"
        )


@router.post("/image/upload", response_model=ImageProcessingResponse, summary="图像文件上传处理")
async def process_image_file(
    image_file: UploadFile = File(..., description="图像文件"),
    processing_type: Optional[str] = Form(None, description="处理类型"),
    current_user: User = Depends(get_current_user)
):
    """
    上传并处理图像文件
    
    - **image_file**: 图像文件（支持多种格式）
    - **processing_type**: 处理类型（可选）
    """
    # 检查文件类型
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/bmp", "image/webp"]
    if image_file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不支持的图像文件格式"
        )
    
    try:
        # 读取文件内容
        image_content = await image_file.read()
        
        # 转换为base64
        import base64
        image_data = base64.b64encode(image_content).decode('utf-8')
        
        # 执行图像处理
        result = image_processor.process_image(
            image_data=image_data,
            image_format=image_file.content_type,
            processing_type=processing_type
        )
        
        return ImageProcessingResponse(
            features=result.features,
            symptoms=result.symptoms,
            quality_score=result.quality_score,
            confidence_score=result.confidence_score,
            processing_time=result.processing_time
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"图像文件处理失败: {str(e)}"
        )


@router.post("/fusion", response_model=FusionResponse, summary="模态融合")
async def fuse_modalities(
    fusion_request: FusionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    融合多种模态的信息
    
    - **text_result**: 文本处理结果
    - **audio_result**: 音频处理结果
    - **image_result**: 图像处理结果
    - **fusion_strategy**: 融合策略
    """
    try:
        # 执行模态融合
        result = fusion_processor.fuse_modalities(
            text_result=fusion_request.text_result,
            audio_result=fusion_request.audio_result,
            image_result=fusion_request.image_result,
            fusion_strategy=fusion_request.fusion_strategy
        )
        
        return FusionResponse(
            fused_result=result.fused_result,
            confidence_score=result.confidence_score,
            modality_weights=result.modality_weights,
            conflicts_resolved=result.conflicts_resolved,
            processing_time=result.processing_time
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"模态融合失败: {str(e)}"
        )


@router.get("/history/{user_id}", response_model=List[MultimodalOutputResponse], summary="获取用户处理历史")
async def get_processing_history(
    user_id: str,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户的多模态处理历史
    
    - **user_id**: 用户ID
    - **skip**: 跳过记录数
    - **limit**: 返回记录数
    """
    # 检查权限（只能查看自己的历史）
    if str(current_user.id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问其他用户的历史记录"
        )
    
    outputs = db.query(MultimodalOutput).filter(
        MultimodalOutput.user_id == user_id
    ).offset(skip).limit(limit).all()
    
    return [
        MultimodalOutputResponse(
            id=str(output.id),
            input_id=str(output.input_id),
            text_result=output.text_result,
            audio_result=output.audio_result,
            image_result=output.image_result,
            fusion_result=output.fusion_result,
            confidence_score=output.confidence_score,
            processing_time=output.processing_time,
            created_at=output.created_at
        )
        for output in outputs
    ]


@router.get("/output/{output_id}", response_model=MultimodalOutputResponse, summary="获取处理结果详情")
async def get_processing_output(
    output_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取指定的处理结果详情
    
    - **output_id**: 输出ID
    """
    output = db.query(MultimodalOutput).filter(MultimodalOutput.id == output_id).first()
    
    if not output:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="处理结果不存在"
        )
    
    # 检查权限
    if str(output.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此处理结果"
        )
    
    return MultimodalOutputResponse(
        id=str(output.id),
        input_id=str(output.input_id),
        text_result=output.text_result,
        audio_result=output.audio_result,
        image_result=output.image_result,
        fusion_result=output.fusion_result,
        confidence_score=output.confidence_score,
        processing_time=output.processing_time,
        created_at=output.created_at
    )


@router.delete("/output/{output_id}", summary="删除处理结果")
async def delete_processing_output(
    output_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除指定的处理结果
    
    - **output_id**: 输出ID
    """
    output = db.query(MultimodalOutput).filter(MultimodalOutput.id == output_id).first()
    
    if not output:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="处理结果不存在"
        )
    
    # 检查权限
    if str(output.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此处理结果"
        )
    
    db.delete(output)
    db.commit()
    
    return {"message": "处理结果删除成功"}


@router.get("/stats/{user_id}", summary="获取用户处理统计")
async def get_processing_stats(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户的多模态处理统计
    
    - **user_id**: 用户ID
    """
    # 检查权限
    if str(current_user.id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问其他用户的统计信息"
        )
    
    # 统计各种处理类型
    total_processings = db.query(MultimodalOutput).filter(
        MultimodalOutput.user_id == user_id
    ).count()
    
    text_processings = db.query(MultimodalOutput).filter(
        MultimodalOutput.user_id == user_id,
        MultimodalOutput.text_result.isnot(None)
    ).count()
    
    audio_processings = db.query(MultimodalOutput).filter(
        MultimodalOutput.user_id == user_id,
        MultimodalOutput.audio_result.isnot(None)
    ).count()
    
    image_processings = db.query(MultimodalOutput).filter(
        MultimodalOutput.user_id == user_id,
        MultimodalOutput.image_result.isnot(None)
    ).count()
    
    # 计算平均置信度
    avg_confidence = db.query(db.func.avg(MultimodalOutput.confidence_score)).filter(
        MultimodalOutput.user_id == user_id
    ).scalar() or 0.0
    
    return {
        "user_id": user_id,
        "total_processings": total_processings,
        "text_processings": text_processings,
        "audio_processings": audio_processings,
        "image_processings": image_processings,
        "avg_confidence_score": float(avg_confidence)
    }
