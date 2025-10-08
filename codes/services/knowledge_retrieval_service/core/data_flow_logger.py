"""
数据流向日志记录器
专门用于记录知识检索系统中完整的数据流向过程
"""

import logging
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
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

from common.log_config import get_logger

# 获取数据流日志记录器
data_flow_logger = get_logger("data_flow")


class DataFlowTracker:
    """数据流向追踪器"""
    
    def __init__(self, process_id: str, process_name: str):
        """
        初始化数据流追踪器
        
        Args:
            process_id: 处理过程ID
            process_name: 处理过程名称
        """
        self.process_id = process_id
        self.process_name = process_name
        self.start_time = time.time()
        self.steps = []
        self.current_step = 0
        
        data_flow_logger.info(f"🚀 数据流追踪开始: {process_name} (ID: {process_id})")
        data_flow_logger.info(f"⏰ 开始时间: {datetime.fromtimestamp(self.start_time).isoformat()}")
    
    def log_step(self, step_name: str, step_data: Dict[str, Any], step_type: str = "processing"):
        """
        记录处理步骤
        
        Args:
            step_name: 步骤名称
            step_data: 步骤数据
            step_type: 步骤类型 (input, processing, output, error)
        """
        self.current_step += 1
        step_time = time.time()
        duration = step_time - self.start_time
        
        step_info = {
            "step_number": self.current_step,
            "step_name": step_name,
            "step_type": step_type,
            "timestamp": datetime.fromtimestamp(step_time).isoformat(),
            "duration_from_start": f"{duration:.3f}s",
            "data": step_data
        }
        
        self.steps.append(step_info)
        
        data_flow_logger.info(f"📋 步骤 {self.current_step}: {step_name}")
        data_flow_logger.info(f"   ⏱️ 耗时: {duration:.3f}秒")
        data_flow_logger.info(f"   📊 类型: {step_type}")
        
        # 记录数据详情
        if step_type == "input":
            data_flow_logger.info(f"   📥 输入数据:")
            self._log_data_details(step_data, "输入")
        elif step_type == "processing":
            data_flow_logger.info(f"   ⚙️ 处理数据:")
            self._log_data_details(step_data, "处理")
        elif step_type == "output":
            data_flow_logger.info(f"   📤 输出数据:")
            self._log_data_details(step_data, "输出")
        elif step_type == "error":
            data_flow_logger.error(f"   ❌ 错误数据:")
            self._log_data_details(step_data, "错误")
    
    def _log_data_details(self, data: Dict[str, Any], data_type: str):
        """记录数据详情"""
        for key, value in data.items():
            if isinstance(value, str):
                if len(value) > 200:
                    data_flow_logger.info(f"      - {key}: {value[:200]}... (长度: {len(value)} 字符)")
                else:
                    data_flow_logger.info(f"      - {key}: {value}")
            elif isinstance(value, (list, tuple)):
                data_flow_logger.info(f"      - {key}: 列表/元组 (长度: {len(value)})")
                if len(value) > 0 and len(value) <= 5:
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            data_flow_logger.info(f"        [{i}]: 字典 (键: {list(item.keys())})")
                        else:
                            item_str = str(item)
                            if len(item_str) > 100:
                                data_flow_logger.info(f"        [{i}]: {item_str[:100]}...")
                            else:
                                data_flow_logger.info(f"        [{i}]: {item_str}")
            elif isinstance(value, dict):
                data_flow_logger.info(f"      - {key}: 字典 (键: {list(value.keys())})")
            elif isinstance(value, (int, float)):
                data_flow_logger.info(f"      - {key}: {value}")
            else:
                data_flow_logger.info(f"      - {key}: {type(value).__name__} - {str(value)[:100]}")
    
    def log_data_transformation(self, from_format: str, to_format: str, 
                              input_data: Any, output_data: Any, transformation_info: Dict[str, Any]):
        """
        记录数据转换过程
        
        Args:
            from_format: 原始格式
            to_format: 目标格式
            input_data: 输入数据
            output_data: 输出数据
            transformation_info: 转换信息
        """
        data_flow_logger.info(f"🔄 数据转换: {from_format} → {to_format}")
        data_flow_logger.info(f"   📥 输入数据类型: {type(input_data).__name__}")
        data_flow_logger.info(f"   📤 输出数据类型: {type(output_data).__name__}")
        
        if isinstance(input_data, (str, list)):
            data_flow_logger.info(f"   📏 输入大小: {len(input_data)}")
        if isinstance(output_data, (str, list)):
            data_flow_logger.info(f"   📏 输出大小: {len(output_data)}")
        
        # 记录转换信息
        for key, value in transformation_info.items():
            data_flow_logger.info(f"   🔧 {key}: {value}")
    
    def log_service_call(self, service_name: str, endpoint: str, 
                        request_data: Dict[str, Any], response_data: Dict[str, Any],
                        call_duration: float, success: bool):
        """
        记录服务调用
        
        Args:
            service_name: 服务名称
            endpoint: 调用端点
            request_data: 请求数据
            response_data: 响应数据
            call_duration: 调用耗时
            success: 是否成功
        """
        status_emoji = "✅" if success else "❌"
        data_flow_logger.info(f"{status_emoji} 服务调用: {service_name}/{endpoint}")
        data_flow_logger.info(f"   ⏱️ 调用耗时: {call_duration:.3f}秒")
        data_flow_logger.info(f"   📊 请求状态: {'成功' if success else '失败'}")
        
        # 记录请求数据摘要
        data_flow_logger.info(f"   📤 请求数据:")
        self._log_data_details(request_data, "请求")
        
        # 记录响应数据摘要
        data_flow_logger.info(f"   📥 响应数据:")
        self._log_data_details(response_data, "响应")
    
    def log_error(self, error_message: str, error_data: Dict[str, Any] = None):
        """
        记录错误信息
        
        Args:
            error_message: 错误消息
            error_data: 错误相关数据
        """
        error_data = error_data or {}
        error_data["error_message"] = error_message
        
        self.log_step(
            step_name="错误处理",
            step_data=error_data,
            step_type="error"
        )
        
        data_flow_logger.error(f"❌ 错误: {error_message}")
        if error_data:
            data_flow_logger.error(f"   📊 错误数据:")
            self._log_data_details(error_data, "错误")

    def finalize(self, final_result: Dict[str, Any], success: bool = True):
        """
        完成数据流追踪
        
        Args:
            final_result: 最终结果
            success: 是否成功
        """
        end_time = time.time()
        total_duration = end_time - self.start_time
        
        status_emoji = "🎉" if success else "💥"
        data_flow_logger.info(f"{status_emoji} 数据流追踪完成: {self.process_name}")
        data_flow_logger.info(f"⏰ 总耗时: {total_duration:.3f}秒")
        data_flow_logger.info(f"📊 总步骤数: {self.current_step}")
        data_flow_logger.info(f"📋 处理状态: {'成功' if success else '失败'}")
        
        # 记录最终结果
        data_flow_logger.info(f"📤 最终结果:")
        self._log_data_details(final_result, "最终")
        
        # 记录完整的数据流摘要
        self._log_flow_summary()
    
    def _log_flow_summary(self):
        """记录数据流摘要"""
        data_flow_logger.info(f"📋 数据流摘要 (ID: {self.process_id}):")
        for step in self.steps:
            data_flow_logger.info(f"   {step['step_number']}. {step['step_name']} ({step['step_type']}) - {step['duration_from_start']}")
    
    def get_flow_data(self) -> Dict[str, Any]:
        """获取完整的数据流数据"""
        return {
            "process_id": self.process_id,
            "process_name": self.process_name,
            "start_time": self.start_time,
            "steps": self.steps,
            "total_steps": self.current_step
        }


def create_data_flow_tracker(process_name: str) -> DataFlowTracker:
    """
    创建数据流追踪器
    
    Args:
        process_name: 处理过程名称
        
    Returns:
        数据流追踪器实例
    """
    process_id = f"{process_name}_{int(time.time() * 1000)}"
    return DataFlowTracker(process_id, process_name)


def log_vector_operation(operation_name: str, input_data: Any, output_data: Any, 
                        operation_params: Dict[str, Any]):
    """
    记录向量操作
    
    Args:
        operation_name: 操作名称
        input_data: 输入数据
        output_data: 输出数据
        operation_params: 操作参数
    """
    data_flow_logger.info(f"🧮 向量操作: {operation_name}")
    
    # 记录输入数据
    if isinstance(input_data, str):
        data_flow_logger.info(f"   📥 输入文本: {input_data[:100]}... (长度: {len(input_data)} 字符)")
    elif isinstance(input_data, list):
        data_flow_logger.info(f"   📥 输入列表: 长度={len(input_data)}")
        if len(input_data) > 0:
            first_item = input_data[0]
            if isinstance(first_item, str):
                data_flow_logger.info(f"      首项文本: {first_item[:50]}...")
    
    # 记录输出数据
    if isinstance(output_data, list) and len(output_data) > 0:
        if isinstance(output_data[0], (list, tuple)):
            data_flow_logger.info(f"   📤 输出向量: 数量={len(output_data)}, 维度={len(output_data[0])}")
        else:
            data_flow_logger.info(f"   📤 输出向量: 维度={len(output_data)}")
    
    # 记录操作参数
    data_flow_logger.info(f"   ⚙️ 操作参数:")
    for key, value in operation_params.items():
        data_flow_logger.info(f"      - {key}: {value}")


def log_retrieval_operation(query_vector: List[float], retrieved_docs: List[Dict[str, Any]], 
                          retrieval_params: Dict[str, Any]):
    """
    记录检索操作
    
    Args:
        query_vector: 查询向量
        retrieved_docs: 检索到的文档
        retrieval_params: 检索参数
    """
    data_flow_logger.info(f"🔍 检索操作")
    data_flow_logger.info(f"   📊 查询向量维度: {len(query_vector)}")
    data_flow_logger.info(f"   📚 检索到文档数: {len(retrieved_docs)}")
    
    # 记录检索参数
    data_flow_logger.info(f"   ⚙️ 检索参数:")
    for key, value in retrieval_params.items():
        data_flow_logger.info(f"      - {key}: {value}")
    
    # 记录检索结果详情
    data_flow_logger.info(f"   📄 检索结果详情:")
    for i, doc in enumerate(retrieved_docs):
        title = doc.get('title', f'文档{i+1}')
        similarity = doc.get('similarity', 0)
        content_length = len(doc.get('content', ''))
        data_flow_logger.info(f"      {i+1}. {title} (相似度: {similarity:.3f}, 长度: {content_length})")


def log_llm_generation(prompt: str, response: str, generation_params: Dict[str, Any], 
                      generation_time: float):
    """
    记录LLM生成操作
    
    Args:
        prompt: 输入提示词
        response: 生成的响应
        generation_params: 生成参数
        generation_time: 生成耗时
    """
    data_flow_logger.info(f"🤖 LLM生成操作")
    data_flow_logger.info(f"   ⏱️ 生成耗时: {generation_time:.3f}秒")
    data_flow_logger.info(f"   📥 提示词长度: {len(prompt)} 字符")
    data_flow_logger.info(f"   📤 响应长度: {len(response)} 字符")
    
    # 记录提示词预览
    data_flow_logger.info(f"   📝 提示词预览: {prompt[:200]}...")
    
    # 记录响应预览
    data_flow_logger.info(f"   💬 响应预览: {response[:200]}...")
    
    # 记录生成参数
    data_flow_logger.info(f"   ⚙️ 生成参数:")
    for key, value in generation_params.items():
        data_flow_logger.info(f"      - {key}: {value}")
