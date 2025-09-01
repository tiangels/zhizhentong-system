"""
多模态处理模块
处理文本、语音、图像等多种模态的输入
"""

from .processor import MultimodalProcessor, MultimodalInput, MultimodalOutput
from .text_processor import TextProcessor
from .audio_processor import AudioProcessor
from .image_processor import ImageProcessor
from .fusion import ModalityFusion

__all__ = [
    "MultimodalProcessor",
    "MultimodalInput",
    "MultimodalOutput",
    "TextProcessor", 
    "AudioProcessor",
    "ImageProcessor",
    "ModalityFusion"
]
