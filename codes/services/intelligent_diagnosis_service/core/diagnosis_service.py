"""
智能诊断服务核心模块
整合文本摘要和大语言模型服务，提供统一的智能诊断接口
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Generator
from pathlib import Path

# 使用统一日志配置
import sys
from pathlib import Path

# 添加common模块到路径
current_file = Path(__file__)
common_dir = current_file.parent.parent.parent.parent / "common"
sys.path.insert(0, str(common_dir))

# 添加项目根目录到路径
import sys
from pathlib import Path
current_file = Path(__file__)
project_root = current_file.parent.parent.parent.parent  # 回到codes目录
sys.path.insert(0, str(project_root))

from common.log_config import setup_logging, get_logger
setup_logging("diagnosis_service")
logger = get_logger(__name__)

# 导入服务模块
from .services.medical_text_summarization_service import MedicalTextSummarizationService, create_medical_summarization_service
from .services.diagnosis_llm_service import DiagnosisLLMService, DiagnosisLLMServiceFactory


class IntelligentDiagnosisService:
    """智能诊断服务核心类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化智能诊断服务
        
        Args:
            config: 配置字典
        """
        self.config = config or self._load_default_config()
        
        # 初始化子服务
        self.summarization_service = None
        self.llm_service = None
        
        # 初始化服务
        self._initialize_services()
        
        logger.info("智能诊断服务初始化完成")
    
    def _load_default_config(self) -> Dict[str, Any]:
        """加载默认配置"""
        try:
            # 尝试从配置文件加载
            config_path = Path(__file__).parent.parent / "config" / "diagnosis_config.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"加载配置文件失败: {e}")
        
        # 返回默认配置
        return {
            'summarization_service': {
                'model_path': None,  # 使用默认路径
                'max_length': 300,
                'min_length': 50
            },
            'llm_service': {
                'device': 'cuda',
                'model_path': 'FreedomIntelligence/Apollo-0.5B',
                'max_length': 2048,
                'temperature': 0.7,
                'top_p': 0.9,
                'top_k': 50,
                'repetition_penalty': 1.1,
                'timeout': 600
            },
            'service_mode': 'optimized'
        }
    
    def _initialize_services(self):
        """初始化子服务"""
        try:
            logger.info("正在初始化智能诊断子服务...")
            
            # 初始化文本摘要服务
            logger.info("初始化医学文本摘要服务...")
            summarization_config = self.config.get('summarization_service', {})
            self.summarization_service = create_medical_summarization_service(
                summarization_config.get('model_path')
            )
            logger.info("医学文本摘要服务初始化完成")
            
            # 初始化大语言模型服务
            logger.info("初始化智能诊断大语言模型服务...")
            llm_config = self.config.get('llm_service', {})
            service_mode = self.config.get('service_mode', 'optimized')
            self.llm_service = DiagnosisLLMServiceFactory.create_diagnosis_llm_service(
                mode=service_mode
            )
            logger.info("智能诊断大语言模型服务初始化完成")
            
            logger.info("所有子服务初始化完成")
            
        except Exception as e:
            logger.error(f"初始化子服务失败: {e}")
            raise
    
    def process_diagnosis_request(self, query: str, context: str = "", 
                                 response_type: str = "diagnosis",
                                 enable_summary: bool = True) -> Dict[str, Any]:
        """
        处理诊断请求
        
        Args:
            query: 用户查询
            context: 检索到的上下文
            response_type: 响应类型 (diagnosis, advice, explanation)
            enable_summary: 是否启用摘要
            
        Returns:
            诊断结果字典
        """
        try:
            logger.info("=" * 50)
            logger.info("🔬 开始智能诊断处理流程")
            logger.info("=" * 50)
            logger.info(f"输入参数: query='{query}', context长度={len(context)}, response_type='{response_type}', enable_summary={enable_summary}")
            
            result = {
                'query': query,
                'context': context,
                'response_type': response_type,
                'summary': '',
                'diagnosis_response': '',
                'success': False,
                'error': None
            }
            
            # 步骤1: 文本摘要处理（如果启用）
            if enable_summary and context:
                logger.info("步骤1: 开始文本摘要处理")
                try:
                    summary = self.summarization_service.summarize_medical_text(
                        context, 
                        max_length=200,
                        retrieval_content=context
                    )
                    result['summary'] = summary
                    logger.info(f"文本摘要完成，摘要长度: {len(summary)} 字符")
                    logger.info(f"摘要内容: {summary}")
                except Exception as e:
                    logger.warning(f"文本摘要处理失败: {e}")
                    result['summary'] = context[:200] + "..." if len(context) > 200 else context
                logger.info("步骤1: 文本摘要处理完成")
            else:
                logger.info("步骤1: 跳过文本摘要处理")
                result['summary'] = context
            
            # 步骤2: 生成诊断响应
            logger.info("步骤2: 开始生成诊断响应")
            try:
                diagnosis_response = self.llm_service.generate_diagnosis_response(
                    query, 
                    result['summary'], 
                    response_type
                )
                result['diagnosis_response'] = diagnosis_response
                result['success'] = True
                logger.info(f"诊断响应生成完成，响应长度: {len(diagnosis_response)} 字符")
                logger.info(f"诊断响应内容: {diagnosis_response}")
            except Exception as e:
                logger.error(f"生成诊断响应失败: {e}")
                result['error'] = str(e)
                result['diagnosis_response'] = "抱歉，生成诊断建议时出现错误。请咨询专业医生。"
            logger.info("步骤2: 生成诊断响应完成")
            
            logger.info("=" * 50)
            logger.info("🔬 智能诊断处理流程完成")
            logger.info("=" * 50)
            
            return result
            
        except Exception as e:
            logger.error(f"智能诊断处理流程失败: {e}")
            return {
                'query': query,
                'context': context,
                'response_type': response_type,
                'summary': '',
                'diagnosis_response': "抱歉，智能诊断服务出现错误。请咨询专业医生。",
                'success': False,
                'error': str(e)
            }
    
    def process_diagnosis_request_stream(self, query: str, context: str = "", 
                                       response_type: str = "diagnosis",
                                       enable_summary: bool = True) -> Generator[str, None, None]:
        """
        流式处理诊断请求
        
        Args:
            query: 用户查询
            context: 检索到的上下文
            response_type: 响应类型
            enable_summary: 是否启用摘要
            
        Yields:
            诊断结果文本块
        """
        try:
            logger.info("=" * 50)
            logger.info("🌊 开始智能诊断流式处理流程")
            logger.info("=" * 50)
            logger.info(f"输入参数: query='{query}', context长度={len(context)}, response_type='{response_type}', enable_summary={enable_summary}")
            
            # 步骤1: 文本摘要处理（如果启用）
            summary = ""
            if enable_summary and context:
                logger.info("步骤1: 开始文本摘要处理")
                try:
                    summary = self.summarization_service.summarize_medical_text(
                        context, 
                        max_length=200,
                        retrieval_content=context
                    )
                    logger.info(f"文本摘要完成，摘要长度: {len(summary)} 字符")
                    logger.info(f"摘要内容: {summary}")
                except Exception as e:
                    logger.warning(f"文本摘要处理失败: {e}")
                    summary = context[:200] + "..." if len(context) > 200 else context
                logger.info("步骤1: 文本摘要处理完成")
            else:
                logger.info("步骤1: 跳过文本摘要处理")
                summary = context
            
            # 步骤2: 流式生成诊断响应
            logger.info("步骤2: 开始流式生成诊断响应")
            try:
                for chunk in self.llm_service.generate_diagnosis_response_stream(
                    query, 
                    summary, 
                    response_type
                ):
                    yield chunk
                logger.info("步骤2: 流式生成诊断响应完成")
            except Exception as e:
                logger.error(f"流式生成诊断响应失败: {e}")
                yield f"生成诊断建议时出现错误：{str(e)}"
            
            logger.info("=" * 50)
            logger.info("🌊 智能诊断流式处理流程完成")
            logger.info("=" * 50)
                
        except Exception as e:
            logger.error(f"智能诊断流式处理流程失败: {e}")
            yield f"智能诊断服务出现错误：{str(e)}"
    
    def get_service_info(self) -> Dict[str, Any]:
        """
        获取服务信息
        
        Returns:
            服务信息字典
        """
        try:
            info = {
                'service_name': 'intelligent_diagnosis_service',
                'service_version': '1.0.0',
                'service_status': 'running',
                'summarization_service': {},
                'llm_service': {},
                'config': self.config
            }
            
            # 获取摘要服务信息
            if self.summarization_service:
                info['summarization_service'] = self.summarization_service.get_model_info()
            
            # 获取LLM服务信息
            if self.llm_service:
                info['llm_service'] = self.llm_service.get_model_info()
            
            return info
            
        except Exception as e:
            logger.error(f"获取服务信息失败: {e}")
            return {
                'service_name': 'intelligent_diagnosis_service',
                'service_version': '1.0.0',
                'service_status': 'error',
                'error': str(e)
            }
    
    def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            健康状态字典
        """
        try:
            health_status = {
                'service': 'intelligent_diagnosis_service',
                'status': 'healthy',
                'timestamp': str(Path(__file__).stat().st_mtime),
                'components': {}
            }
            
            # 检查摘要服务
            if self.summarization_service:
                try:
                    # 简单测试
                    test_summary = self.summarization_service.summarize_medical_text("测试文本", max_length=10)
                    health_status['components']['summarization_service'] = {
                        'status': 'healthy',
                        'model_loaded': True
                    }
                except Exception as e:
                    health_status['components']['summarization_service'] = {
                        'status': 'unhealthy',
                        'error': str(e)
                    }
            else:
                health_status['components']['summarization_service'] = {
                    'status': 'not_initialized'
                }
            
            # 检查LLM服务
            if self.llm_service:
                try:
                    # 简单测试
                    test_response = self.llm_service.generate_text("测试", max_new_tokens=5)
                    health_status['components']['llm_service'] = {
                        'status': 'healthy',
                        'model_loaded': True
                    }
                except Exception as e:
                    health_status['components']['llm_service'] = {
                        'status': 'unhealthy',
                        'error': str(e)
                    }
            else:
                health_status['components']['llm_service'] = {
                    'status': 'not_initialized'
                }
            
            # 检查整体状态
            component_statuses = [comp['status'] for comp in health_status['components'].values()]
            if 'unhealthy' in component_statuses:
                health_status['status'] = 'degraded'
            elif 'not_initialized' in component_statuses:
                health_status['status'] = 'partial'
            
            return health_status
            
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {
                'service': 'intelligent_diagnosis_service',
                'status': 'unhealthy',
                'error': str(e)
            }


def create_intelligent_diagnosis_service(config: Dict[str, Any] = None) -> IntelligentDiagnosisService:
    """
    创建智能诊断服务实例
    
    Args:
        config: 配置字典
        
    Returns:
        智能诊断服务实例
    """
    return IntelligentDiagnosisService(config)


if __name__ == "__main__":
    # 测试智能诊断服务
    try:
        # 创建服务
        service = create_intelligent_diagnosis_service()
        
        # 测试诊断请求
        query = "我最近经常感到胸痛，这是什么原因？"
        context = "胸痛可能由多种原因引起，包括心血管疾病、肺部疾病、消化系统疾病等。需要根据具体症状和检查结果进行诊断。"
        
        print("测试智能诊断服务...")
        print(f"查询: {query}")
        print(f"上下文: {context}")
        
        # 普通诊断请求
        result = service.process_diagnosis_request(query, context, "diagnosis")
        print(f"\n诊断结果: {result}")
        
        # 流式诊断请求
        print("\n流式诊断结果:")
        for chunk in service.process_diagnosis_request_stream(query, context, "diagnosis"):
            print(chunk, end='', flush=True)
        
        # 服务信息
        service_info = service.get_service_info()
        print(f"\n\n服务信息: {service_info}")
        
        # 健康检查
        health_status = service.health_check()
        print(f"\n健康状态: {health_status}")
        
    except Exception as e:
        print(f"测试失败: {e}")
        print("Please ensure the models are properly downloaded and configured.")
