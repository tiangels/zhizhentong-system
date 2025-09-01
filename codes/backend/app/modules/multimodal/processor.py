"""
多模态处理器主类
协调各种模态的处理流程
"""

import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from .text_processor import TextProcessor
from .audio_processor import AudioProcessor
from .image_processor import ImageProcessor
from .fusion import ModalityFusion


class MultimodalInput(BaseModel):
    """多模态输入数据模型"""
    text: Optional[str] = None
    audio: Optional[bytes] = None
    image: Optional[bytes] = None
    metadata: Optional[Dict[str, Any]] = None


class MultimodalOutput(BaseModel):
    """多模态输出数据模型"""
    processed_text: str
    entities: List[Dict[str, Any]]
    sentiment: str
    confidence: float
    processing_time: float
    modality_info: Dict[str, Any]


class MultimodalProcessor:
    """多模态处理器主类"""
    
    def __init__(self):
        """初始化多模态处理器"""
        self.text_processor = TextProcessor()
        self.audio_processor = AudioProcessor()
        self.image_processor = ImageProcessor()
        self.fusion = ModalityFusion()
    
    def process_input(self, input_data: MultimodalInput) -> MultimodalOutput:
        """
        处理多模态输入
        
        Args:
            input_data: 多模态输入数据
            
        Returns:
            MultimodalOutput: 处理结果
        """
        start_time = time.time()
        
        # 初始化处理结果
        processed_results = {}
        modality_info = {}
        
        # 处理文本输入
        if input_data.text_data:
            text_result = self.text_processor.process_text(input_data.text_data)
            processed_results['text'] = text_result
            modality_info['text'] = {
                'processed': True,
                'confidence': text_result.get('confidence', 0.0)
            }
        
        # 处理音频输入
        if input_data.audio_data:
            audio_result = self.audio_processor.process_audio(input_data.audio_data)
            processed_results['audio'] = audio_result
            modality_info['audio'] = {
                'processed': True,
                'confidence': audio_result.get('confidence', 0.0)
            }
        
        # 处理图像输入
        if input_data.image_data:
            image_result = self.image_processor.process_image(input_data.image_data)
            processed_results['image'] = image_result
            modality_info['image'] = {
                'processed': True,
                'confidence': image_result.get('confidence', 0.0)
            }
        
        # 多模态融合
        if len(processed_results) > 1:
            fused_result = self.fusion.fuse_modalities(processed_results)
        else:
            # 单模态处理
            fused_result = list(processed_results.values())[0] if processed_results else {
                'text': '',
                'entities': [],
                'sentiment': 'neutral',
                'confidence': 0.0
            }
        
        processing_time = time.time() - start_time
        
        # 处理sentiment字段，确保是字符串
        sentiment_data = fused_result.get('sentiment', 'neutral')
        sentiment_str = sentiment_data.get('primary', 'neutral') if isinstance(sentiment_data, dict) else str(sentiment_data)
        
        return MultimodalOutput(
            processed_text=fused_result.get('text', ''),
            entities=fused_result.get('entities', []),
            sentiment=sentiment_str,
            confidence=fused_result.get('confidence', 0.0),
            processing_time=processing_time,
            modality_info=modality_info
        )
    
    def recognize_modality(self, input_data: MultimodalInput) -> List[str]:
        """
        识别输入数据的模态类型
        
        Args:
            input_data: 多模态输入数据
            
        Returns:
            List[str]: 识别出的模态类型列表
        """
        modalities = []
        
        if input_data.text:
            modalities.append('text')
        
        if input_data.audio:
            modalities.append('audio')
        
        if input_data.image:
            modalities.append('image')
        
        return modalities
    
    def validate_input(self, input_data: MultimodalInput) -> bool:
        """
        验证输入数据
        
        Args:
            input_data: 多模态输入数据
            
        Returns:
            bool: 验证是否通过
        """
        # 检查是否至少有一种模态
        modalities = self.recognize_modality(input_data)
        if not modalities:
            return False
        
        # 验证文本长度
        if input_data.text and len(input_data.text) > 5000:
            return False
        
        # 验证音频大小
        if input_data.audio and len(input_data.audio) > 10 * 1024 * 1024:  # 10MB
            return False
        
        # 验证图像大小
        if input_data.image and len(input_data.image) > 10 * 1024 * 1024:  # 10MB
            return False
        
        return True
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        获取处理统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            'text_processor': self.text_processor.get_stats(),
            'audio_processor': self.audio_processor.get_stats(),
            'image_processor': self.image_processor.get_stats(),
            'fusion': self.fusion.get_stats()
        }
