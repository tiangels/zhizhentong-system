"""
图像向量化模块
提供统一的图像嵌入功能，确保与文本向量在同一向量空间中
"""

from .image_embedder import ImageEmbedderFactory, batch_embed_images

__all__ = ['ImageEmbedderFactory', 'batch_embed_images']
