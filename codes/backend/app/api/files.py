"""
文件服务API路由
提供文件访问和下载功能
"""

import os
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from ..config import settings

router = APIRouter(prefix="/files", tags=["文件服务"])


@router.get("/image_data/raw/{filename}", summary="获取原始图片文件")
async def get_raw_image(filename: str):
    """
    获取原始图片文件
    
    - **filename**: 文件名
    """
    try:
        # 构建文件路径
        file_path = os.path.join(settings.UPLOAD_DIR, "image_data", "raw", filename)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在"
            )
        
        # 检查文件类型
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不支持的文件类型"
            )
        
        # 返回文件
        return FileResponse(
            path=file_path,
            media_type="image/*",
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件访问失败: {str(e)}"
        )


@router.get("/voice_data/raw/{filename}", summary="获取原始音频文件")
async def get_raw_audio(filename: str):
    """
    获取原始音频文件
    
    - **filename**: 文件名
    """
    try:
        # 构建文件路径
        file_path = os.path.join(settings.UPLOAD_DIR, "voice_data", "raw", filename)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在"
            )
        
        # 检查文件类型
        if not filename.lower().endswith(('.wav', '.mp3', '.mpeg', '.ogg', '.flac', '.m4a', '.aac')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不支持的文件类型"
            )
        
        # 返回文件
        return FileResponse(
            path=file_path,
            media_type="audio/*",
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件访问失败: {str(e)}"
        )


@router.get("/processed/image/{filename}", summary="获取处理后的图片文件")
async def get_processed_image(filename: str):
    """
    获取处理后的图片文件
    
    - **filename**: 文件名
    """
    try:
        # 构建文件路径
        file_path = os.path.join(settings.UPLOAD_DIR, "image_data", "processed", filename)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在"
            )
        
        # 返回文件
        return FileResponse(
            path=file_path,
            media_type="image/*",
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件访问失败: {str(e)}"
        )


@router.get("/processed/voice/{filename}", summary="获取处理后的音频文件")
async def get_processed_audio(filename: str):
    """
    获取处理后的音频文件
    
    - **filename**: 文件名
    """
    try:
        # 构建文件路径
        file_path = os.path.join(settings.UPLOAD_DIR, "voice_data", "processed", filename)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在"
            )
        
        # 返回文件
        return FileResponse(
            path=file_path,
            media_type="audio/*",
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件访问失败: {str(e)}"
        )
