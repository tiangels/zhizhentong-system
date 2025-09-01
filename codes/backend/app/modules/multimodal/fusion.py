"""
多模态融合器
融合多种模态的信息
"""

import time
from typing import Dict, Any, List
from collections import defaultdict


class ModalityFusion:
    """多模态融合器"""
    
    def __init__(self):
        """初始化多模态融合器"""
        self.stats = defaultdict(int)
    
    def fuse_modalities(self, modality_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        融合多种模态的信息
        
        Args:
            modality_data: 各模态的处理结果
            
        Returns:
            Dict[str, Any]: 融合后的结果
        """
        start_time = time.time()
        self.stats['total_fused'] += 1
        
        # 模态对齐
        aligned_data = self._align_modalities(modality_data)
        
        # 信息融合
        fused_data = self._fuse_information(aligned_data)
        
        # 冲突处理
        resolved_data = self._resolve_conflicts(fused_data)
        
        # 结果优化
        optimized_data = self._optimize_result(resolved_data)
        
        processing_time = time.time() - start_time
        self.stats['total_processing_time'] += processing_time
        
        return optimized_data
    
    def _align_modalities(self, modality_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        模态对齐
        
        Args:
            modality_data: 各模态的数据
            
        Returns:
            Dict[str, Any]: 对齐后的数据
        """
        aligned_data = {
            'text': '',
            'entities': [],
            'sentiment': 'neutral',
            'confidence': 0.0,
            'modality_weights': {}
        }
        
        # 文本模态处理
        if 'text' in modality_data:
            text_result = modality_data['text']
            aligned_data['text'] = text_result.get('text', '')
            aligned_data['entities'].extend(text_result.get('entities', []))
            aligned_data['modality_weights']['text'] = 0.4
        
        # 音频模态处理
        if 'audio' in modality_data:
            audio_result = modality_data['audio']
            if audio_result.get('text'):
                # 如果音频识别出文本，与文本模态合并
                if aligned_data['text']:
                    aligned_data['text'] += ' ' + audio_result['text']
                else:
                    aligned_data['text'] = audio_result['text']
            
            # 音频情感分析
            audio_sentiment = audio_result.get('emotion', 'neutral')
            if audio_sentiment != 'neutral':
                aligned_data['sentiment'] = audio_sentiment
            
            aligned_data['modality_weights']['audio'] = 0.3
        
        # 图像模态处理
        if 'image' in modality_data:
            image_result = modality_data['image']
            # 将图像检测的症状转换为实体
            if 'symptoms' in image_result:
                for symptom in image_result['symptoms']:
                    aligned_data['entities'].append({
                        'text': symptom,
                        'type': 'symptom',
                        'source': 'image',
                        'confidence': image_result.get('confidence', 0.8)
                    })
            
            aligned_data['modality_weights']['image'] = 0.3
        
        return aligned_data
    
    def _fuse_information(self, aligned_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        信息融合
        
        Args:
            aligned_data: 对齐后的数据
            
        Returns:
            Dict[str, Any]: 融合后的信息
        """
        fused_data = aligned_data.copy()
        
        # 实体去重和合并
        unique_entities = {}
        for entity in fused_data['entities']:
            entity_text = entity['text']
            if entity_text not in unique_entities:
                unique_entities[entity_text] = entity
            else:
                # 合并相同实体的置信度
                existing_entity = unique_entities[entity_text]
                existing_entity['confidence'] = max(
                    existing_entity['confidence'], 
                    entity['confidence']
                )
        
        fused_data['entities'] = list(unique_entities.values())
        
        # 计算综合置信度
        total_confidence = 0.0
        total_weight = 0.0
        
        for modality, weight in fused_data['modality_weights'].items():
            if modality in aligned_data:
                total_confidence += weight * aligned_data.get('confidence', 0.0)
                total_weight += weight
        
        if total_weight > 0:
            fused_data['confidence'] = total_confidence / total_weight
        else:
            fused_data['confidence'] = 0.0
        
        return fused_data
    
    def _resolve_conflicts(self, fused_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        冲突处理
        
        Args:
            fused_data: 融合后的数据
            
        Returns:
            Dict[str, Any]: 冲突解决后的数据
        """
        resolved_data = fused_data.copy()
        
        # 处理情感冲突
        sentiments = []
        if 'text' in resolved_data.get('modality_weights', {}):
            sentiments.append(fused_data.get('sentiment', 'neutral'))
        
        if 'audio' in resolved_data.get('modality_weights', {}):
            # 音频情感分析结果
            pass
        
        # 简单的情感冲突解决策略
        if len(set(sentiments)) > 1:
            # 如果有冲突，选择最强烈的情感
            sentiment_strength = {
                'positive': 1,
                'negative': -1,
                'neutral': 0
            }
            
            strongest_sentiment = max(sentiments, key=lambda x: abs(sentiment_strength.get(x, 0)))
            resolved_data['sentiment'] = strongest_sentiment
        
        return resolved_data
    
    def _optimize_result(self, resolved_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        结果优化
        
        Args:
            resolved_data: 冲突解决后的数据
            
        Returns:
            Dict[str, Any]: 优化后的结果
        """
        optimized_data = resolved_data.copy()
        
        # 按置信度排序实体
        optimized_data['entities'] = sorted(
            optimized_data['entities'],
            key=lambda x: x.get('confidence', 0.0),
            reverse=True
        )
        
        # 限制实体数量
        optimized_data['entities'] = optimized_data['entities'][:10]
        
        # 确保置信度在合理范围内
        optimized_data['confidence'] = max(0.0, min(1.0, optimized_data['confidence']))
        
        return optimized_data
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取处理统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            'total_fused': self.stats['total_fused'],
            'total_processing_time': self.stats['total_processing_time'],
            'avg_processing_time': (
                self.stats['total_processing_time'] / self.stats['total_fused']
                if self.stats['total_fused'] > 0 else 0
            )
        }
