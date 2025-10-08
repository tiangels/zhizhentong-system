#!/usr/bin/env python3
"""
语音数据预处理模块
专门处理语音文件转文本功能

功能:
1. 支持多种音频格式 (WAV, MP3, M4A, FLAC)
2. 使用Whisper模型进行语音转文本
3. 语音数据清洗和预处理
4. 批量处理语音文件
5. 生成结构化输出

作者: AI Assistant
创建时间: 2025-09-17
版本: 1.0.0
"""

import os
import sys
import json
import logging
import traceback
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

try:
    import whisper
    import librosa
    import soundfile as sf
    import warnings
    
    # 过滤librosa的弃用警告
    warnings.filterwarnings("ignore", category=FutureWarning, module="librosa")
    # 过滤whisper的FP16警告
    warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")
    
    VOICE_LIBRARIES_AVAILABLE = True
except ImportError as e:
    VOICE_LIBRARIES_AVAILABLE = False
    print(f"警告: 语音处理库未安装: {e}")
    print("请安装: pip install openai-whisper librosa soundfile")

try:
    from .base_processor import BaseDataProcessor
except ImportError:
    from base_processor import BaseDataProcessor


class VoicePreprocessor(BaseDataProcessor):
    """语音数据预处理器
    功能：
    1. 语音转文本处理
    2. 语音数据清洗和预处理
    3. 生成供文档切分使用的JSON格式数据
    
    注意：不包含文档切分和向量化功能，只负责数据预处理
    """
    
    def __init__(self, 
                 raw_data_dir: str,
                 output_dir: str,
                 whisper_model_path: str = None,
                 sample_rate: int = None):
        """
        初始化语音预处理器
        
        Args:
            raw_data_dir: 原始语音数据目录
            output_dir: 输出目录
            whisper_model_path: Whisper模型路径（可选，将从配置中获取）
            sample_rate: 音频采样率（可选，将从配置中获取）
        """
        # 调用父类初始化
        super().__init__(raw_data_dir, output_dir, "VoicePreprocessor")
        
        # 从配置中获取模型信息
        try:
            import sys
            from pathlib import Path
            current_dir = Path(__file__).parent
            sys.path.append(str(current_dir.parent.parent.parent / "llm_models"))
            
            from model_config_reader import get_model_config_reader
            
            reader = get_model_config_reader()
            voice_model_info = reader.get_voice_to_text_model()
            
            # 设置模型参数
            self.sample_rate = sample_rate or voice_model_info.get('sample_rate', 16000)
            self.whisper_model_name = voice_model_info.get('model_name', 'whisper-tiny')
            self.whisper_model_path = voice_model_info.get('model_path', '')
            
        except Exception as e:
            self.logger.warning(f"无法从配置加载模型信息: {e}")
            # 使用默认值
            self.sample_rate = sample_rate or 16000
            self.whisper_model_name = "tiny"
            self.whisper_model_path = whisper_model_path or ""
        
        # 支持的音频格式
        self.supported_formats = {
            '.wav': 'WAV音频文件',
            '.mp3': 'MP3音频文件', 
            '.m4a': 'M4A音频文件',
            '.flac': 'FLAC音频文件',
            '.aac': 'AAC音频文件',
            '.ogg': 'OGG音频文件'
        }
        
        # 初始化Whisper模型
        self.whisper_model = None
        self._load_whisper_model()
        
        # 处理统计
        self.processed_files = []
        self.failed_files = []
        self.total_duration = 0.0
        
        self.logger.info(f"🎤 语音预处理器初始化完成")
        self.logger.info(f"Whisper模型名称: {self.whisper_model_name}")
        self.logger.info(f"支持格式: {list(self.supported_formats.keys())}")
    
    def _load_whisper_model(self):
        """加载Whisper模型"""
        if not VOICE_LIBRARIES_AVAILABLE:
            self.logger.warning("语音处理库不可用，跳过Whisper模型加载")
            return
        
        try:
            self.logger.info(f"🔧 加载Whisper模型: {self.whisper_model_name}")
            self.whisper_model = whisper.load_model(self.whisper_model_name)
            self.logger.info("✅ Whisper模型加载成功")
        except Exception as e:
            self.logger.error(f"❌ Whisper模型加载失败: {e}")
            self.whisper_model = None
    
    def _is_audio_file(self, file_path: Path) -> bool:
        """检查是否为支持的音频文件"""
        return file_path.suffix.lower() in self.supported_formats
    
    def _detect_voice_type_from_filename(self, filename: str) -> str:
        """根据文件名判断语音类型"""
        filename_lower = filename.lower()
        
        # 医疗对话语音
        if any(keyword in filename_lower for keyword in ['dialogue', '对话', 'chat', 'conversation', 'consultation']):
            return 'medical_dialogue'
        
        # 医疗讲座/培训
        elif any(keyword in filename_lower for keyword in ['lecture', '讲座', 'training', '培训', 'course']):
            return 'medical_lecture'
        
        # 医疗咨询
        elif any(keyword in filename_lower for keyword in ['consultation', '咨询', 'advice', '建议']):
            return 'medical_consultation'
        
        # 病历录音
        elif any(keyword in filename_lower for keyword in ['record', '病历', 'case', '病例']):
            return 'medical_record'
        
        # 健康宣教
        elif any(keyword in filename_lower for keyword in ['education', '宣教', 'health', '健康']):
            return 'health_education'
        
        # 默认为通用语音
        else:
            return 'general_voice'
    
    def _preprocess_audio(self, audio_path: Path) -> Tuple[np.ndarray, int]:
        """预处理音频文件"""
        try:
            # 使用librosa加载音频，添加警告过滤
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                audio, sr = librosa.load(str(audio_path), sr=self.sample_rate)
            
            # 音频预处理
            # 1. 去除静音段
            audio, _ = librosa.effects.trim(audio, top_db=20)
            
            # 2. 归一化
            audio = librosa.util.normalize(audio)
            
            return audio, sr
        except Exception as e:
            self.logger.error(f"音频预处理失败 {audio_path}: {e}")
            raise
    
    def _transcribe_audio(self, audio_path: Path) -> Dict[str, Any]:
        """使用Whisper转录音频"""
        if self.whisper_model is None:
            raise RuntimeError("Whisper模型未加载")
        
        try:
            # 预处理音频
            audio, sr = self._preprocess_audio(audio_path)
            
            # 使用Whisper转录音频，添加警告过滤
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                result = self.whisper_model.transcribe(
                    audio,
                    language="zh",  # 指定中文
                    task="transcribe",
                    verbose=False
                )
            
            # 提取转录结果
            transcription = {
                'text': result['text'].strip(),
                'language': result.get('language', 'zh'),
                'duration': len(audio) / sr,
                'segments': []
            }
            
            # 处理分段信息
            if 'segments' in result:
                for segment in result['segments']:
                    transcription['segments'].append({
                        'start': segment['start'],
                        'end': segment['end'],
                        'text': segment['text'].strip(),
                        'confidence': segment.get('no_speech_prob', 0.0)
                    })
            
            return transcription
            
        except Exception as e:
            self.logger.error(f"音频转录失败 {audio_path}: {e}")
            raise
    
    def _clean_transcription_text(self, text: str) -> str:
        """清洗转录文本"""
        if not text:
            return ""
        
        # 使用基类清洗方法进行清洗
        cleaned_result = self.clean_text(text)
        cleaned_text = cleaned_result.get('cleaned_text', text)
        
        # 语音特有的清洗规则
        # 1. 移除重复的标点符号
        import re
        cleaned_text = re.sub(r'([。！？，；：])\1+', r'\1', cleaned_text)
        
        # 2. 修复常见的语音识别错误
        corrections = {
            '嗯': '嗯',
            '啊': '啊',
            '呃': '呃',
            '这个': '这个',
            '那个': '那个',
            '就是': '就是',
            '然后': '然后',
            '所以': '所以',
            '因为': '因为',
            '但是': '但是'
        }
        
        for wrong, correct in corrections.items():
            cleaned_text = cleaned_text.replace(wrong, correct)
        
        return cleaned_text
    
    def process_single_voice_file(self, file_path: Path) -> Dict[str, Any]:
        """处理单个语音文件"""
        try:
            self.logger.info(f"🎤 处理语音文件: {file_path.name}")
            
            # 检测语音类型
            voice_type = self._detect_voice_type_from_filename(file_path.name)
            
            # 转录音频
            transcription = self._transcribe_audio(file_path)
            
            # 1. 调用基类的文本清洗功能，保留医学符号
            cleaned_result = self.clean_text(transcription['text'])
            
            # 2. 调用数据脱敏功能
            desensitized_result = self.desensitize_text(cleaned_result['cleaned_text'])
            
            # 3. 创建结构化输出
            metadata = {
                'file_name': file_path.name,
                'file_path': str(file_path),
                'data_type': 'voice',
                'voice_type': voice_type,
                'duration': transcription['duration'],
                'language': transcription['language'],
                'file_size': file_path.stat().st_size,
                'quality_score': cleaned_result['quality_score'],
                'medical_terms_count': cleaned_result['medical_terms_count'],
                'sensitive_info': desensitized_result['sensitive_info'],
                'has_sensitive_data': desensitized_result['has_sensitive_data']
            }
            
            structured_doc = self.create_structured_output(
                desensitized_result['desensitized_text'], 
                metadata
            )
            
            # 构建结果（保持向后兼容）
            result = {
                'file_name': file_path.name,
                'file_path': str(file_path),
                'voice_type': voice_type,
                'duration': transcription['duration'],
                'language': transcription['language'],
                'original_text': transcription['text'],
                'cleaned_text': desensitized_result['desensitized_text'],
                'segments': transcription['segments'],
                'processed_time': datetime.now().isoformat(),
                'file_size': file_path.stat().st_size,
                'structured_doc': structured_doc  # 添加结构化文档
            }
            
            # 更新统计
            self.total_duration += transcription['duration']
            self.processed_files.append(result)
            
            self.logger.info(f"✅ 语音文件处理完成: {file_path.name} (时长: {transcription['duration']:.2f}s)")
            return result
            
        except Exception as e:
            error_info = {
                'file_name': file_path.name,
                'file_path': str(file_path),
                'error': str(e),
                'processed_time': datetime.now().isoformat()
            }
            self.failed_files.append(error_info)
            self.logger.error(f"❌ 语音文件处理失败: {file_path.name} - {e}")
            return None
    
    def scan_voice_files(self) -> List[Path]:
        """扫描语音文件"""
        voice_files = []
        
        # 扫描原始数据目录
        if self.raw_data_dir.exists():
            for file_path in self.raw_data_dir.rglob('*'):
                if file_path.is_file() and self._is_audio_file(file_path):
                    voice_files.append(file_path)
        
        # 扫描专门的语音数据目录
        voice_data_dir = self.raw_data_dir.parent / 'voice_data' / 'raw'
        if voice_data_dir.exists():
            for file_path in voice_data_dir.rglob('*'):
                if file_path.is_file() and self._is_audio_file(file_path):
                    voice_files.append(file_path)
        
        self.logger.info(f"🔍 发现 {len(voice_files)} 个语音文件")
        return voice_files
    
    def save_results(self, results: List[Dict[str, Any]]):
        """保存处理结果"""
        if not results:
            self.logger.warning("没有结果需要保存")
            return
        
        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存为CSV格式
        csv_path = self.output_dir / 'voice_transcriptions.csv'
        try:
            import pandas as pd
            
            # 准备CSV数据
            csv_data = []
            for result in results:
                csv_data.append({
                    'file_name': result['file_name'],
                    'voice_type': result['voice_type'],
                    'duration': result['duration'],
                    'language': result['language'],
                    'cleaned_text': result['cleaned_text'],
                    'processed_time': result['processed_time']
                })
            
            df = pd.DataFrame(csv_data)
            df.to_csv(csv_path, index=False, encoding='utf-8')
            self.logger.info(f"✅ CSV结果已保存: {csv_path}")
            
        except Exception as e:
            self.logger.error(f"❌ CSV保存失败: {e}")
        
        # 保存为JSON格式
        json_path = self.output_dir / 'voice_transcriptions.json'
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            self.logger.info(f"✅ JSON结果已保存: {json_path}")
            
        except Exception as e:
            self.logger.error(f"❌ JSON保存失败: {e}")
        
        # 保存处理统计
        stats_path = self.output_dir / 'voice_processing_stats.json'
        try:
            stats = {
                'total_files': len(results),
                'successful_files': len([r for r in results if r is not None]),
                'failed_files': len(self.failed_files),
                'total_duration': self.total_duration,
                'average_duration': self.total_duration / len(results) if results else 0,
                'voice_types': {},
                'processed_time': datetime.now().isoformat()
            }
            
            # 统计语音类型
            for result in results:
                if result and 'voice_type' in result:
                    voice_type = result['voice_type']
                    stats['voice_types'][voice_type] = stats['voice_types'].get(voice_type, 0) + 1
            
            with open(stats_path, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            self.logger.info(f"✅ 处理统计已保存: {stats_path}")
            
        except Exception as e:
            self.logger.error(f"❌ 统计保存失败: {e}")
        
        # 生成供文档切分使用的JSON格式数据
        self._save_json_data(results)
    
    def _save_json_data(self, results: List[Dict[str, Any]]):
        """生成供文档切分使用的JSON格式数据"""
        try:
            # 准备JSON数据 - 使用结构化文档
            json_data = []
            for result in results:
                if result and 'structured_doc' in result:  # 只处理成功的结果
                    json_data.append(result['structured_doc'])
            
            # 保存为JSON格式
            json_path = self.output_dir / 'voice_documents.json'
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"✅ 语音JSON数据文件已保存: {json_path}")
            
        except Exception as e:
            self.logger.error(f"❌ 语音JSON数据文件保存失败: {e}")
    
    def run(self, sample_size: Optional[int] = None, process_all_files: bool = True):
        """运行语音处理"""
        self.logger.info("🚀 开始语音处理")
        
        # 检查语音处理库
        if not VOICE_LIBRARIES_AVAILABLE:
            self.logger.error("❌ 语音处理库不可用，无法处理语音文件")
            return
        
        # 检查Whisper模型
        if self.whisper_model is None:
            self.logger.error("❌ Whisper模型未加载，无法处理语音文件")
            return
        
        # 扫描语音文件
        voice_files = self.scan_voice_files()
        
        if not voice_files:
            self.logger.warning("⚠️ 未发现语音文件")
            return
        
        # 限制处理数量
        if sample_size and sample_size > 0:
            voice_files = voice_files[:sample_size]
            self.logger.info(f"📊 限制处理数量: {len(voice_files)} 个文件")
        
        # 处理语音文件
        results = []
        for i, file_path in enumerate(voice_files, 1):
            self.logger.info(f"📁 处理进度: {i}/{len(voice_files)} - {file_path.name}")
            
            result = self.process_single_voice_file(file_path)
            if result:
                results.append(result)
        
        # 保存结果
        if results:
            self.save_results(results)
            self.logger.info(f"🎉 语音处理完成! 成功处理 {len(results)} 个文件")
            self.logger.info("📄 语音数据预处理完成，JSON文件已保存供文档切分使用")
        else:
            self.logger.warning("⚠️ 没有成功处理任何文件")
        
        # 输出失败信息
        if self.failed_files:
            self.logger.warning(f"⚠️ {len(self.failed_files)} 个文件处理失败")
            for failed in self.failed_files:
                self.logger.warning(f"  - {failed['file_name']}: {failed['error']}")
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        return {
            'total_files': len(self.processed_files),
            'failed_files': len(self.failed_files),
            'total_duration': self.total_duration,
            'average_duration': self.total_duration / len(self.processed_files) if self.processed_files else 0,
            'voice_types': self._get_voice_type_stats(),
            'supported_formats': list(self.supported_formats.keys()),
            'whisper_model_loaded': self.whisper_model is not None
        }
    
    def _get_voice_type_stats(self) -> Dict[str, int]:
        """获取语音类型统计"""
        stats = {}
        for result in self.processed_files:
            voice_type = result.get('voice_type', 'unknown')
            stats[voice_type] = stats.get(voice_type, 0) + 1
        return stats


def setup_logging():
    """设置统一日志配置"""
    import sys
    from pathlib import Path
    current_dir = Path(__file__).parent
    sys.path.append(str(current_dir.parent / "core"))
    
    from log_manager import get_logger
    
    # 使用统一的日志管理器
    logger = get_logger(__name__)
    logger.info("🎤 开始语音预处理运行")
    logger.info("🎯 智诊通语音预处理系统启动")
    
    return logger

def main():
    """主函数"""
    # 设置统一日志配置
    logger = setup_logging()
    
    # 创建语音预处理器
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
    raw_data_dir = os.path.join(project_root, "datas", "medical_knowledge", "voice_data", "raw")
    output_dir = os.path.join(project_root, "datas", "medical_knowledge", "voice_data", "processed")
    
    processor = VoicePreprocessor(raw_data_dir, output_dir)
    
    # 运行处理
    processor.run(sample_size=5, process_all_files=True)
    
    # 输出统计信息
    stats = processor.get_processing_stats()
    logger.info("\n📊 语音数据预处理统计:")
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")
    
    logger.info("\n🎯 语音数据预处理完成！")
    logger.info("📄 生成的JSON文件可供文档切分模块使用")


if __name__ == "__main__":
    main()
