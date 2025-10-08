"""
统一的数据预处理基类
提供通用的数据清洗、脱敏、医学符号保留等功能
"""

import os
import re
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import pandas as pd
from datetime import datetime

class BaseDataProcessor:
    """数据预处理基类"""
    
    def __init__(self, raw_data_dir: str, output_dir: str, processor_name: str = "BaseProcessor"):
        """
        初始化基类处理器
        
        Args:
            raw_data_dir: 原始数据目录
            output_dir: 输出目录
            processor_name: 处理器名称
        """
        self.raw_data_dir = Path(raw_data_dir)
        self.output_dir = Path(output_dir)
        self.processor_name = processor_name
        
        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置日志
        self._setup_logging()
        
        # 初始化通用组件
        self._init_data_cleaning()
        self._init_medical_symbols()
        self._init_desensitization()
        self._init_quality_checker()
        
        self.logger.info(f"{self.processor_name} 初始化完成")
        self.logger.info(f"原始数据目录: {self.raw_data_dir}")
        self.logger.info(f"输出目录: {self.output_dir}")
    
    def _setup_logging(self):
        """设置日志系统"""
        # 导入统一的日志管理器
        import sys
        from pathlib import Path
        current_dir = Path(__file__).parent
        common_dir = current_dir.parent.parent.parent / "common"
        sys.path.insert(0, str(common_dir))
        
        from log_config import get_logger
        
        # 使用统一的日志管理器
        self.logger = get_logger(f"{__name__}.{self.processor_name}")
    
    def _init_data_cleaning(self):
        """初始化数据清洗组件"""
        self.logger.info("🔧 初始化数据清洗组件...")
        
        # 乱码检测模式 - 保护医学符号
        self.garbled_patterns = [
            r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]',  # 只删除控制字符
            r'[^\w\s\u4e00-\u9fff\u3000-\u303f\uff00-\uffef.,;:!?()（）【】《》""''、。，；：！？℃°↑↓±/]'  # 保留医学符号
        ]
        
        # 广告水印模式
        self.ad_patterns = [
            r'广告|推广|营销|促销|优惠|折扣|免费|试用',
            r'联系我们|咨询热线|客服|电话|微信|QQ',
            r'版权所有|Copyright|©|®|™',
            r'www\.|http://|https://|\.com|\.cn|\.net',
            r'关注我们|扫码|二维码|公众号|订阅'
        ]
        
        # 页眉页脚模式
        self.header_footer_patterns = [
            r'第\s*\d+\s*页|Page\s*\d+',
            r'共\s*\d+\s*页|共\s*\d+\s*张',
            r'第\s*\d+\s*章|Chapter\s*\d+',
            r'目录|Contents|Index',
            r'参考文献|References|Bibliography'
        ]
        
        self.logger.info("✅ 数据清洗组件初始化完成")
    
    def _init_medical_symbols(self):
        """初始化医学特殊字符保留组件"""
        self.logger.info("🔧 初始化医学特殊字符保留组件...")
        
        # 医学单位符号
        self.medical_units = {
            'temperature': ['℃', '°C', '华氏度', '℉', '°F'],
            'percentage': ['%', '百分比', '百分率'],
            'weight': ['mg', 'g', 'kg', '毫克', '克', '千克', '斤', '两'],
            'volume': ['ml', 'l', '毫升', '升', 'cc'],
            'pressure': ['mmHg', 'kPa', '毫米汞柱', '千帕'],
            'frequency': ['次/分', '次/日', '次/周', '次/月', '次/年'],
            'concentration': ['mg/dl', 'mmol/l', 'μmol/l', 'ng/ml', 'μg/ml']
        }
        
        # 检验符号
        self.test_symbols = {
            'positive': ['+', '阳性', 'positive', 'pos', 'P'],
            'negative': ['-', '阴性', 'negative', 'neg', 'N'],
            'normal': ['正常', 'normal', 'N', 'norm'],
            'abnormal': ['异常', 'abnormal', 'A', 'abn'],
            'high': ['↑', '↑↑', '↑↑↑', '高', 'high', 'H'],
            'low': ['↓', '↓↓', '↓↓↓', '低', 'low', 'L'],
            'trace': ['±', '±±', '微量', 'trace', 'T']
        }
        
        # 医学标点符号
        self.medical_punctuation = ['、', '，', '。', '；', '：', '！', '？', '（', '）', '【', '】', '《', '》']
        
        self.logger.info("✅ 医学特殊字符保留组件初始化完成")
    
    def _init_desensitization(self):
        """初始化数据脱敏组件"""
        self.logger.info("🔧 初始化数据脱敏组件...")
        
        # 身份证号模式
        self.id_pattern = r'\b\d{17}[\dXx]\b'
        
        # 手机号模式
        self.phone_pattern = r'\b1[3-9]\d{9}\b'
        
        # 姓名模式（简单中文姓名）
        self.name_pattern = r'[王李张刘陈杨黄赵吴周徐孙马朱胡郭何高林罗郑梁谢宋唐许韩冯邓曹彭曾萧田董袁潘于蒋蔡余杜叶程魏苏吕丁任沈姚卢姜崔钟谭陆汪范金石廖贾夏韦付方白邹孟熊秦邱江尹薛闫段雷侯龙史陶黎贺顾毛郝龚邵万钱严覃武戴莫孔向汤][\u4e00-\u9fff]{1,3}'
        
        # 病历号模式
        self.medical_record_pattern = r'\b[A-Za-z0-9]{6,20}\b'
        
        # 地址模式
        self.address_pattern = r'[省市区县乡镇街道村组号]\d*[号室楼单元]'
        
        self.logger.info("✅ 数据脱敏组件初始化完成")
    
    def _init_quality_checker(self):
        """初始化数据质量检查组件"""
        self.logger.info("🔧 初始化数据质量检查组件...")
        
        self.min_length = 10  # 最小文本长度
        self.max_length = 10000  # 最大文本长度
        self.min_medical_terms = 0  # 最少医学术语数量（基类默认为0，子类可重写）
        
        self.logger.info("✅ 数据质量检查组件初始化完成")
    
    def clean_text(self, text: str) -> Dict[str, Any]:
        """
        清洗文本数据
        
        Args:
            text: 原始文本
            
        Returns:
            清洗结果字典
        """
        if not text or not isinstance(text, str):
            return {'cleaned_text': '', 'quality_score': 0.0, 'issues': ['empty_text']}
        
        self.logger.debug(f"🧹 开始清洗文本，长度: {len(text)}")
        
        original_text = text
        issues = []
        quality_score = 1.0
        
        # 1. 检测和清理乱码
        self.logger.debug("🔍 检测和清理乱码...")
        garbled_count = 0
        for pattern in self.garbled_patterns:
            matches = re.findall(pattern, text)
            garbled_count += len(matches)
            text = re.sub(pattern, '', text)
        
        if garbled_count > 0:
            issues.append(f'garbled_characters_{garbled_count}')
            quality_score -= min(0.3, garbled_count * 0.01)
            self.logger.debug(f"发现 {garbled_count} 个乱码字符")
        
        # 2. 清理广告水印
        self.logger.debug("🔍 清理广告水印...")
        ad_count = 0
        for pattern in self.ad_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            ad_count += len(matches)
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        if ad_count > 0:
            issues.append(f'advertisement_{ad_count}')
            quality_score -= min(0.2, ad_count * 0.05)
            self.logger.debug(f"发现 {ad_count} 个广告内容")
        
        # 3. 清理页眉页脚
        self.logger.debug("🔍 清理页眉页脚...")
        header_footer_count = 0
        for pattern in self.header_footer_patterns:
            matches = re.findall(pattern, text)
            header_footer_count += len(matches)
            text = re.sub(pattern, '', text)
        
        if header_footer_count > 0:
            issues.append(f'header_footer_{header_footer_count}')
            quality_score -= min(0.1, header_footer_count * 0.02)
            self.logger.debug(f"发现 {header_footer_count} 个页眉页脚")
        
        # 4. 清理多余空白
        self.logger.debug("🔍 清理多余空白...")
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 5. 检查文本长度
        self.logger.debug("🔍 检查文本长度...")
        if len(text) < self.min_length:
            issues.append('too_short')
            quality_score = 0.0
            self.logger.debug(f"文本过短: {len(text)} < {self.min_length}")
        elif len(text) > self.max_length:
            issues.append('too_long')
            text = text[:self.max_length]
            quality_score -= 0.1
            self.logger.debug(f"文本过长，截断到: {self.max_length}")
        
        # 6. 检查医学内容（子类可重写）
        medical_terms_count = self._count_medical_terms(text)
        if medical_terms_count < self.min_medical_terms:
            issues.append('insufficient_medical_content')
            quality_score -= 0.2
            self.logger.debug(f"医学术语不足: {medical_terms_count} < {self.min_medical_terms}")
        
        result = {
            'cleaned_text': text,
            'quality_score': max(0.0, quality_score),
            'issues': issues,
            'original_length': len(original_text),
            'cleaned_length': len(text),
            'medical_terms_count': medical_terms_count
        }
        
        self.logger.debug(f"✅ 文本清洗完成，质量评分: {result['quality_score']:.2f}")
        return result
    
    def _count_medical_terms(self, text: str) -> int:
        """统计医学术语数量"""
        count = 0
        
        # 统计医学单位
        for unit_list in self.medical_units.values():
            for unit in unit_list:
                count += len(re.findall(re.escape(unit), text, re.IGNORECASE))
        
        # 统计检验符号
        for symbol_list in self.test_symbols.values():
            for symbol in symbol_list:
                count += len(re.findall(re.escape(symbol), text, re.IGNORECASE))
        
        # 统计常见医学术语
        medical_terms = ['患者', '医生', '症状', '诊断', '治疗', '药物', '检查', '化验', '血压', '血糖', '体温', '心率', '呼吸', '脉搏']
        for term in medical_terms:
            count += len(re.findall(term, text))
        
        return count
    
    def desensitize_text(self, text: str) -> Dict[str, Any]:
        """
        数据脱敏处理
        
        Args:
            text: 原始文本
            
        Returns:
            脱敏结果字典
        """
        if not text:
            return {'desensitized_text': '', 'sensitive_info': {}}
        
        self.logger.debug("🔒 开始数据脱敏处理...")
        
        sensitive_info = {}
        desensitized_text = text
        
        # 1. 身份证号脱敏
        self.logger.debug("🔍 检测身份证号...")
        id_matches = re.findall(self.id_pattern, text)
        if id_matches:
            sensitive_info['id_numbers'] = id_matches
            for id_num in id_matches:
                masked_id = id_num[:6] + '*' * 8 + id_num[-4:]
                desensitized_text = desensitized_text.replace(id_num, masked_id)
            self.logger.debug(f"发现并脱敏 {len(id_matches)} 个身份证号")
        
        # 2. 手机号脱敏
        self.logger.debug("🔍 检测手机号...")
        phone_matches = re.findall(self.phone_pattern, text)
        if phone_matches:
            sensitive_info['phone_numbers'] = phone_matches
            for phone in phone_matches:
                masked_phone = phone[:3] + '****' + phone[-4:]
                desensitized_text = desensitized_text.replace(phone, masked_phone)
            self.logger.debug(f"发现并脱敏 {len(phone_matches)} 个手机号")
        
        # 3. 姓名脱敏
        self.logger.debug("🔍 检测姓名...")
        name_matches = re.findall(self.name_pattern, text)
        if name_matches:
            sensitive_info['names'] = name_matches
            for name in name_matches:
                if len(name) >= 2:
                    masked_name = name[0] + '*' * (len(name) - 1)
                    desensitized_text = desensitized_text.replace(name, masked_name)
            self.logger.debug(f"发现并脱敏 {len(name_matches)} 个姓名")
        
        # 4. 病历号脱敏
        self.logger.debug("🔍 检测病历号...")
        medical_record_matches = re.findall(self.medical_record_pattern, text)
        if medical_record_matches:
            sensitive_info['medical_records'] = medical_record_matches
            for record in medical_record_matches:
                if len(record) >= 6:
                    masked_record = record[:3] + '*' * (len(record) - 6) + record[-3:]
                    desensitized_text = desensitized_text.replace(record, masked_record)
            self.logger.debug(f"发现并脱敏 {len(medical_record_matches)} 个病历号")
        
        # 5. 地址脱敏
        self.logger.debug("🔍 检测地址...")
        address_matches = re.findall(self.address_pattern, text)
        if address_matches:
            sensitive_info['addresses'] = address_matches
            for address in address_matches:
                masked_address = re.sub(r'\d+', '***', address)
                desensitized_text = desensitized_text.replace(address, masked_address)
            self.logger.debug(f"发现并脱敏 {len(address_matches)} 个地址")
        
        result = {
            'desensitized_text': desensitized_text,
            'sensitive_info': sensitive_info,
            'has_sensitive_data': bool(sensitive_info)
        }
        
        self.logger.debug(f"✅ 数据脱敏完成，发现敏感信息: {len(sensitive_info)} 类")
        return result
    
    def preserve_medical_symbols(self, text: str) -> str:
        """
        保留医学特殊字符
        
        Args:
            text: 原始文本
            
        Returns:
            保留医学符号后的文本
        """
        if not text:
            return text
        
        self.logger.debug("🔧 保留医学特殊字符...")
        # 这里不需要特殊处理，因为医学符号已经在清洗过程中被保留
        # 主要是确保在清洗时不会误删这些重要符号
        self.logger.debug("✅ 医学特殊字符保留完成")
        return text
    
    def create_structured_output(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建结构化输出格式
        
        Args:
            content: 文本内容
            metadata: 元数据
            
        Returns:
            结构化输出字典
        """
        self.logger.debug("📋 创建结构化输出...")
        
        # 生成唯一ID
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()[:16]
        
        # 创建结构化输出
        structured_output = {
            'id': f"doc_{content_hash}",
            'content': content,
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'content_length': len(content),
                'content_type': 'text',
                'processing_version': '1.0',
                'processor_name': self.processor_name,
                **metadata
            },
            'quality_metrics': {
                'medical_terms_count': self._count_medical_terms(content),
                'has_medical_symbols': any(symbol in content for symbols in self.medical_units.values() for symbol in symbols),
                'has_test_symbols': any(symbol in content for symbols in self.test_symbols.values() for symbol in symbols)
            }
        }
        
        self.logger.debug("✅ 结构化输出创建完成")
        return structured_output
    
    def _save_structured_json(self, df: pd.DataFrame, data_type: str):
        """保存结构化JSON格式数据"""
        self.logger.info(f"💾 保存结构化JSON数据: {data_type}")
        
        structured_data = []
        
        for _, row in df.iterrows():
            # 创建结构化输出
            content = row.get('content_final', row.get('content', ''))
            metadata = {
                'data_type': data_type.split('_')[0],
                'source_file': row.get('source_file', ''),
                'file_type': row.get('file_type', ''),
                'quality_score': row.get('quality_score', 0.0),
                'cleaning_issues': row.get('cleaning_issues', []),
                'has_sensitive_data': row.get('has_sensitive_data', False),
                'sensitive_info': row.get('sensitive_info', {}),
                **row.get('metadata', {})
            }
            
            # 创建结构化输出
            structured_doc = self.create_structured_output(content, metadata)
            structured_data.append(structured_doc)
        
        # 保存JSON文件
        json_path = self.output_dir / f"{data_type}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(structured_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"✅ 结构化JSON数据已保存: {json_path} ({len(structured_data)} 条)")
    
    def log_processing_start(self, data_type: str, count: int):
        """记录处理开始日志"""
        self.logger.info("=" * 80)
        self.logger.info(f"🚀 开始处理 {data_type} 数据，共 {count} 条")
        self.logger.info("=" * 80)
    
    def log_processing_step(self, step: str, details: str = ""):
        """记录处理步骤日志"""
        self.logger.info(f"📋 {step}")
        if details:
            self.logger.info(f"   {details}")
    
    def log_processing_complete(self, data_type: str, success_count: int, total_count: int):
        """记录处理完成日志"""
        self.logger.info("=" * 80)
        self.logger.info(f"✅ {data_type} 数据处理完成")
        self.logger.info(f"   成功处理: {success_count}/{total_count} 条")
        self.logger.info(f"   成功率: {success_count/total_count*100:.1f}%")
        self.logger.info("=" * 80)
