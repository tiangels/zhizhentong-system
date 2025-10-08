"""
多模态处理API路由
负责文件上传和存储，业务处理由检索服务完成
"""

import os
import uuid
import json
import httpx
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
from ..config import settings

router = APIRouter(prefix="/multimodal", tags=["多模态处理"])


@router.post("/unified", response_model=MultimodalOutputResponse, summary="统一多模态处理")
async def process_unified_multimodal(
    text: Optional[str] = Form(None, description="文本内容"),
    image_file: Optional[UploadFile] = File(None, description="图片文件"),
    audio_file: Optional[UploadFile] = File(None, description="音频文件"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    print("=== 统一多模态处理接口被调用 ===")
    print(f"text: {text}")
    print(f"image_file: {image_file}")
    print(f"audio_file: {audio_file}")
    
    # 写入日志文件
    with open("/tmp/multimodal_debug.log", "a") as f:
        f.write(f"=== 统一多模态处理接口被调用 ===\n")
        f.write(f"text: {text}\n")
        f.write(f"image_file: {image_file}\n")
        f.write(f"audio_file: {audio_file}\n")
        f.write("---\n")
    """
    统一处理多模态输入（文本、图片、语音）
    根据输入类型自动判断处理流程
    
    - **text**: 文本内容（可选）
    - **image_file**: 图片文件（可选）
    - **audio_file**: 音频文件（可选）
    """
    try:
        # 检查是否有任何输入
        if not text and not image_file and not audio_file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="至少需要提供文本、图片或音频中的一种输入"
            )

        # 处理图片文件
        image_data = None
        image_files_list = []
        
        print(f"=== 图片文件检查 ===")
        print(f"image_file: {image_file}")
        
        # 处理单个图片文件
        if image_file:
            print(f"添加单个图片文件: {image_file.filename}")
            # 检查文件大小
            if hasattr(image_file, 'size') and image_file.size > settings.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"文件 {image_file.filename} 大小超过限制 ({image_file.size} > {settings.MAX_FILE_SIZE} bytes)"
                )
            image_files_list.append(image_file)
        
        print(f"最终图片文件列表长度: {len(image_files_list)}")
        
        if image_files_list:
            print(f"=== 开始处理图片文件 ===")
            print(f"图片文件数量: {len(image_files_list)}")
            
            # 检查文件类型
            allowed_image_types = ["image/jpeg", "image/png", "image/gif", "image/bmp", "image/webp"]
            
            processed_images = []
            for img_file in image_files_list:
                print(f"处理图片文件: {img_file.filename}, 类型: {img_file.content_type}")
                if img_file.content_type not in allowed_image_types:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"不支持的图片文件格式: {img_file.content_type}"
                    )
                
                # 生成唯一文件名
                file_id = str(uuid.uuid4())
                file_extension = os.path.splitext(img_file.filename)[1]
                filename = f"{file_id}{file_extension}"
                
                # 确保目录存在
                image_raw_dir = os.path.join(settings.UPLOAD_DIR, "image_data", "raw")
                os.makedirs(image_raw_dir, exist_ok=True)
                
                # 读取文件内容（只能读取一次）
                content = await img_file.read()
                print(f"读取到内容大小: {len(content)} bytes")
                
                # 保存文件
                file_path = os.path.join(image_raw_dir, filename)
                print(f"保存文件到: {file_path}")
                with open(file_path, "wb") as buffer:
                    buffer.write(content)
                    print(f"文件保存成功")
                
                # 生成可访问的图片URL
                image_url = f"/api/v1/files/image_data/raw/{filename}"
                
                processed_images.append({
                    "filename": filename,
                    "file_path": file_path,
                    "content_type": img_file.content_type,
                    "size": len(content),
                    "url": image_url
                })
            
            # 如果只有一个图片，保持向后兼容
            if len(processed_images) == 1:
                image_data = processed_images[0]
            else:
                image_data = {
                    "files": processed_images,
                    "count": len(processed_images)
                }

        # 处理音频文件
        audio_data = None
        if audio_file:
            # 检查文件类型
            allowed_audio_types = ["audio/wav", "audio/mp3", "audio/mpeg", "audio/ogg", "audio/flac", "audio/m4a", "audio/aac"]
            if audio_file.content_type not in allowed_audio_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="不支持的音频文件格式"
                )
            
            # 生成唯一文件名
            file_id = str(uuid.uuid4())
            file_extension = os.path.splitext(audio_file.filename)[1]
            filename = f"{file_id}{file_extension}"
            
            # 确保目录存在
            voice_raw_dir = os.path.join(settings.UPLOAD_DIR, "voice_data", "raw")
            os.makedirs(voice_raw_dir, exist_ok=True)
            
            # 保存文件
            file_path = os.path.join(voice_raw_dir, filename)
            with open(file_path, "wb") as buffer:
                content = await audio_file.read()
                buffer.write(content)
            
            audio_data = {
                "filename": filename,
                "file_path": file_path,
                "content_type": audio_file.content_type,
                "size": len(content)
            }

        # 调用检索服务处理多模态数据
        async with httpx.AsyncClient() as client:
            # 构建请求数据
            rag_request = {
                "text": text,
                "image_data": image_data,
                "audio_data": audio_data,
                "user_id": str(current_user.id),
                "session_id": str(uuid.uuid4())
            }
            
            response = await client.post(
                f"{settings.RETRIEVAL_SERVICE_URL}/process/unified",
                json=rag_request,
                timeout=300.0
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"检索服务处理失败: {response.text}"
                )
            
            result = response.json()
            
            # 创建多模态输入记录
            db_input = MultimodalInput(
                user_id=current_user.id,
                session_id=rag_request["session_id"],
                text_data=text,
                audio_data=json.dumps(audio_data) if audio_data else None,
                image_data=json.dumps(image_data) if image_data else None,
                input_type="unified_multimodal"
            )
            
            db.add(db_input)
            db.commit()
            db.refresh(db_input)
            
            # 创建输出记录
            db_output = MultimodalOutput(
                input_id=db_input.id,
                user_id=current_user.id,
                session_id=rag_request["session_id"],
                text_result=result.get("text_result", {}),
                audio_result=result.get("audio_result", {}),
                image_result=result.get("image_result", image_data),  # 使用原始图片数据作为fallback
                fusion_result=result.get("fusion_result", {}),
                confidence_score=result.get("confidence_score", 0.0),
                processing_time=result.get("processing_time", 0.0)
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
            
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"检索服务不可用: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"多模态处理失败: {str(e)}"
        )


@router.post("/process", response_model=MultimodalOutputResponse, summary="多模态综合处理")
async def process_multimodal(
    multimodal_input: MultimodalInputCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    处理多模态输入（文本、音频、图像）
    将数据传递给检索服务进行处理
    
    - **text_data**: 文本数据（可选）
    - **audio_data**: 音频数据（可选）
    - **image_data**: 图像数据（可选）
    - **user_id**: 用户ID
    - **session_id**: 会话ID（可选）
    """
    try:
        # 调用检索服务处理多模态数据
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.RETRIEVAL_SERVICE_URL}/process/multimodal",
                json={
                    "text_data": multimodal_input.text_data,
                    "audio_data": multimodal_input.audio_data,
                    "image_data": multimodal_input.image_data,
                    "user_id": str(current_user.id),
                    "session_id": multimodal_input.session_id
                },
                timeout=300.0
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"检索服务处理失败: {response.text}"
                )
            
            result = response.json()
            
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
            
            # 创建输出记录
            db_output = MultimodalOutput(
                input_id=db_input.id,
                user_id=current_user.id,
                session_id=multimodal_input.session_id,
                text_result=result.get("text_result", {}),
                audio_result=result.get("audio_result", {}),
                image_result=result.get("image_result", {}),
                fusion_result=result.get("fusion_result", {}),
                confidence_score=result.get("confidence_score", 0.0),
                processing_time=result.get("processing_time", 0.0)
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
            
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"检索服务不可用: {str(e)}"
        )
    except Exception as e:
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
        # 调用检索服务处理文本
        async with httpx.AsyncClient() as client:
            # 使用检索服务的查询接口
            response = await client.post(
                f"{settings.RETRIEVAL_SERVICE_URL}/query",
                json={
                    "question": text_request.text,
                    "top_k": 5,
                    "response_type": "general",
                    "similarity_threshold": 0.5
                },
                timeout=300.0
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"检索服务处理失败: {response.text}"
                )
            
            result = response.json()
            
            # 提取处理结果
            data = result.get("data", {})
            answer = data.get("answer", text_request.text)
            retrieved_docs = data.get("retrieved_documents", [])
            
            # 提取实体和情感分析（简化处理）
            entities = []
            sentiment = "neutral"
            confidence = data.get("confidence", 0.0)
            
            return TextProcessingResponse(
                processed_text=answer,
                entities=entities,
                sentiment=sentiment,
                confidence=confidence,
                processing_time=data.get("processing_time", 0.0)
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
        # 调用检索服务处理音频数据
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.RETRIEVAL_SERVICE_URL}/query",
                json={
                    "question": f"请分析这段音频数据: {audio_request.audio_data[:100]}...",
                    "top_k": 5,
                    "response_type": "general",
                    "similarity_threshold": 0.5
                },
                timeout=300.0
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"检索服务处理失败: {response.text}"
                )
            
            result = response.json()
            data = result.get("data", {})
        
        return AudioProcessingResponse(
            transcription=data.get('answer', ''),
            audio_features={},
            confidence=data.get('confidence', 0.0),
            processing_time=data.get('processing_time', 0.0)
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
    上传音频文件并存储，业务处理由检索服务完成
    
    - **audio_file**: 音频文件（支持多种格式）
    - **processing_type**: 处理类型（可选）
    """
    # 检查文件类型
    allowed_types = ["audio/wav", "audio/mp3", "audio/mpeg", "audio/ogg", "audio/flac", "audio/m4a", "audio/aac"]
    if audio_file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不支持的音频文件格式"
        )
    
    try:
        # 生成唯一文件名
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(audio_file.filename)[1]
        filename = f"{file_id}{file_extension}"
        
        # 确保目录存在
        voice_raw_dir = os.path.join(settings.UPLOAD_DIR, "voice_data", "raw")
        os.makedirs(voice_raw_dir, exist_ok=True)
        
        # 保存文件到原始目录
        file_path = os.path.join(voice_raw_dir, filename)
        with open(file_path, "wb") as buffer:
            content = await audio_file.read()
            buffer.write(content)
        
        # 调用检索服务处理音频文件
        async with httpx.AsyncClient() as client:
            # 使用检索服务的文档上传接口
            with open(file_path, "rb") as audio_file_content:
                files = {"file": (filename, audio_file_content, audio_file.content_type)}
                data = {
                    "title": f"音频文件_{file_id}",
                    "category": "audio",
                    "source": "user_upload",
                    "type": "audio"
                }
                
                response = await client.post(
                    f"{settings.RETRIEVAL_SERVICE_URL}/documents",
                    files=files,
                    data=data,
                    timeout=300.0
                )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"检索服务处理失败: {response.text}"
                )
            
            result = response.json()
            
            # 返回处理结果
            return AudioProcessingResponse(
                transcription=result.get("data", {}).get("transcription", ""),
                audio_features=result.get("data", {}).get("audio_features", {}),
                confidence=result.get("data", {}).get("confidence", 0.0),
                processing_time=result.get("data", {}).get("processing_time", 0.0)
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
        # 调用检索服务处理图像数据
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.RETRIEVAL_SERVICE_URL}/query",
                json={
                    "question": f"请分析这段图像数据: {image_request.image_data[:100]}...",
                    "top_k": 5,
                    "response_type": "general",
                    "similarity_threshold": 0.5
                },
                timeout=300.0
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"检索服务处理失败: {response.text}"
                )
            
            result = response.json()
            data = result.get("data", {})
            
            return ImageProcessingResponse(
                detected_objects=[],
                image_features={},
                confidence=data.get('confidence', 0.0),
                processing_time=data.get('processing_time', 0.0)
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
    上传图像文件并存储，业务处理由检索服务完成
    
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
        # 生成唯一文件名
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(image_file.filename)[1]
        filename = f"{file_id}{file_extension}"
        
        # 确保目录存在
        image_raw_dir = os.path.join(settings.UPLOAD_DIR, "image_data", "raw")
        os.makedirs(image_raw_dir, exist_ok=True)
        
        # 保存文件到原始目录
        file_path = os.path.join(image_raw_dir, filename)
        with open(file_path, "wb") as buffer:
            content = await image_file.read()
            buffer.write(content)
        
        # 调用检索服务处理图像文件
        async with httpx.AsyncClient() as client:
            # 使用检索服务的图像文档上传接口
            with open(file_path, "rb") as image_file_content:
                files = {"file": (filename, image_file_content, image_file.content_type)}
                data = {
                    "title": f"图像文件_{file_id}",
                    "category": "image",
                    "source": "user_upload"
                }
                
                response = await client.post(
                    f"{settings.RETRIEVAL_SERVICE_URL}/documents/images",
                    files=files,
                    data=data,
                    timeout=300.0
                )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"检索服务处理失败: {response.text}"
                )
            
            result = response.json()
            
            # 返回处理结果
            return ImageProcessingResponse(
                detected_objects=result.get("data", {}).get("detected_objects", []),
                image_features=result.get("data", {}).get("image_features", {}),
                confidence=result.get("data", {}).get("confidence", 0.0),
                processing_time=result.get("data", {}).get("processing_time", 0.0)
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
        # 调用检索服务的聊天接口进行多模态融合
        async with httpx.AsyncClient() as client:
            # 构建多模态数据
            multimodal_data = {}
            if fusion_request.text_result:
                multimodal_data["text"] = fusion_request.text_result
            if fusion_request.audio_result:
                multimodal_data["audio"] = fusion_request.audio_result
            if fusion_request.image_result:
                multimodal_data["image"] = fusion_request.image_result
            
            # 构建对话历史
            messages = [
                {"role": "user", "content": "请融合以下多模态信息并给出综合分析"}
            ]
            
            response = await client.post(
                f"{settings.RETRIEVAL_SERVICE_URL}/chat",
                json={
                    "messages": messages,
                    "top_k": 5,
                    "multimodal_data": multimodal_data
                },
                timeout=300.0
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"检索服务处理失败: {response.text}"
                )
            
            result = response.json()
            data = result.get("data", {})
            
            return FusionResponse(
                fused_result=data.get("answer", "融合处理完成"),
                confidence_score=data.get("confidence", 0.0),
                modality_weights={"text": 0.4, "audio": 0.3, "image": 0.3},
                conflicts_resolved=True,
                processing_time=data.get("processing_time", 0.0)
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
