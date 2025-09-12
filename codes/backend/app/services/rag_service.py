"""
RAG服务模块
通过HTTP API调用知识检索服务，为对话系统提供智能回复
"""

import os
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
import asyncio
import httpx
from datetime import datetime
import time
import json

# 配置日志
logger = logging.getLogger(__name__)

class RAGService:
    """RAG服务类，通过HTTP API调用知识检索和生成功能"""
    
    def __init__(self):
        """初始化RAG服务"""
        self.rag_service_url = os.getenv("RAG_SERVICE_URL", "http://localhost:8001")
        # 配置更合理的超时设置
        self.timeout = httpx.Timeout(
            connect=10.0,  # 连接超时10秒
            read=120.0,    # 读取超时120秒
            write=10.0,    # 写入超时10秒
            pool=5.0       # 连接池超时5秒
        )
        # 配置HTTP客户端，禁用连接池限制
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
        self.is_available_flag = None
        self.max_retries = 3  # 最大重试次数
        self.retry_delay = 1.0  # 重试延迟（秒）
        self._check_service_availability()
    
    def _check_service_availability(self):
        """检查RAG服务是否可用"""
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环正在运行，创建任务
                asyncio.create_task(self._async_check_availability())
            else:
                # 如果事件循环没有运行，直接运行
                loop.run_until_complete(self._async_check_availability())
        except Exception as e:
            logger.error(f"检查RAG服务可用性失败: {e}")
            self.is_available_flag = False
    
    async def _async_check_availability(self):
        """异步检查服务可用性"""
        try:
            logger.info(f"🔍 开始检查RAG服务可用性...")
            logger.info(f"🌐 服务URL: {self.rag_service_url}/health")
            
            response = await self.client.get(f"{self.rag_service_url}/health")
            logger.info(f"📡 健康检查响应状态: {response.status_code}")
            
            if response.status_code == 200:
                self.is_available_flag = True
                logger.info("✅ RAG服务可用")
                try:
                    health_data = response.json()
                    logger.info(f"📊 服务健康状态: {health_data}")
                except:
                    logger.info(f"📄 健康检查响应内容: {response.text[:200]}...")
            else:
                self.is_available_flag = False
                logger.error(f"❌ RAG服务健康检查失败: {response.status_code}")
                logger.error(f"📄 错误响应内容: {response.text[:200]}...")
        except Exception as e:
            self.is_available_flag = False
            logger.error(f"❌ RAG服务不可用: {e}")
            logger.error(f"🔍 错误类型: {type(e).__name__}")
            logger.error(f"📋 错误详情: {str(e)}")
    
    async def _ensure_service_available(self):
        """确保服务可用"""
        logger.info(f"🔍 检查服务可用性状态: {self.is_available_flag}")
        # 总是重新检查服务可用性，确保状态是最新的
        logger.info(f"🔄 重新检查RAG服务可用性...")
        await self._async_check_availability()
        return self.is_available_flag
    
    async def _make_request_with_retry(self, method: str, url: str, **kwargs) -> httpx.Response:
        """
        带重试机制的HTTP请求
        
        Args:
            method: HTTP方法
            url: 请求URL
            **kwargs: 其他请求参数
            
        Returns:
            HTTP响应对象
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    delay = self.retry_delay * (2 ** (attempt - 1))  # 指数退避
                    logger.info(f"🔄 第 {attempt + 1} 次尝试，等待 {delay:.1f} 秒后重试...")
                    await asyncio.sleep(delay)
                
                logger.info(f"🚀 发送 {method.upper()} 请求到 {url} (尝试 {attempt + 1}/{self.max_retries + 1})")
                
                if method.upper() == "GET":
                    response = await self.client.get(url, **kwargs)
                elif method.upper() == "POST":
                    response = await self.client.post(url, **kwargs)
                else:
                    raise ValueError(f"不支持的HTTP方法: {method}")
                
                logger.info(f"✅ 请求成功，状态码: {response.status_code}")
                return response
                
            except httpx.TimeoutException as e:
                last_exception = e
                logger.warning(f"⏰ 请求超时 (尝试 {attempt + 1}/{self.max_retries + 1}): {e}")
                if attempt == self.max_retries:
                    logger.error(f"❌ 所有重试尝试都超时了")
                    break
                    
            except httpx.ConnectError as e:
                last_exception = e
                logger.warning(f"🔌 连接错误 (尝试 {attempt + 1}/{self.max_retries + 1}): {e}")
                if attempt == self.max_retries:
                    logger.error(f"❌ 所有重试尝试都连接失败")
                    break
                    
            except httpx.HTTPStatusError as e:
                last_exception = e
                logger.warning(f"📊 HTTP状态错误 (尝试 {attempt + 1}/{self.max_retries + 1}): {e}")
                # HTTP状态错误通常不需要重试，直接返回
                return e.response
                
            except Exception as e:
                last_exception = e
                logger.warning(f"❌ 请求异常 (尝试 {attempt + 1}/{self.max_retries + 1}): {e}")
                if attempt == self.max_retries:
                    logger.error(f"❌ 所有重试尝试都失败了")
                    break
        
        # 如果所有重试都失败了，抛出最后一个异常
        if last_exception:
            raise last_exception
        else:
            raise Exception("请求失败，原因未知")
    
    async def generate_response(self, 
                              user_message: str, 
                              conversation_history: List[Dict[str, str]] = None,
                              top_k: int = 5) -> Dict[str, Any]:
        """
        生成AI回复
        
        Args:
            user_message: 用户消息
            conversation_history: 对话历史
            top_k: 检索文档数量
            
        Returns:
            包含回复和相关信息的字典
        """
        try:
            logger.info(f"🔍 RAG服务开始处理用户消息")
            logger.info(f"📝 用户消息: {user_message[:100]}...")
            logger.info(f"📊 消息长度: {len(user_message)} 字符")
            
            # 检查服务是否可用
            logger.info(f"🔍 开始检查RAG服务可用性...")
            if not await self._ensure_service_available():
                logger.error("❌ RAG服务不可用，无法处理请求")
                return self._get_fallback_response("RAG服务不可用")
            logger.info(f"✅ RAG服务可用性检查通过")
            
            # 构建对话历史
            logger.info(f"📚 开始构建对话历史...")
            if conversation_history is None:
                conversation_history = []
                logger.info(f"📝 对话历史为空，初始化为空列表")
            else:
                logger.info(f"📝 接收到 {len(conversation_history)} 条历史消息")
            
            # 添加当前用户消息
            conversation_history.append({
                'role': 'user',
                'content': user_message
            })
            logger.info(f"✅ 当前用户消息已添加到对话历史")
            
            logger.info(f"📊 对话历史统计:")
            logger.info(f"   - 总消息数: {len(conversation_history)}")
            logger.info(f"   - 检索参数: top_k={top_k}")
            
            # 记录对话历史详情
            for i, msg in enumerate(conversation_history):
                logger.debug(f"📄 消息 {i+1}: {msg['role']} - {msg['content'][:50]}...")
            
            # 调用RAG服务的chat接口
            payload = {
                "messages": conversation_history,
                "top_k": top_k
            }
            
            logger.info(f"🚀 准备发送请求到RAG服务")
            logger.info(f"🌐 目标URL: {self.rag_service_url}/chat")
            logger.info(f"📤 请求载荷大小: {len(str(payload))} 字符")
            logger.debug(f"📤 完整请求载荷: {payload}")
            
            # 记录请求开始时间
            request_start_time = time.time()
            logger.info(f"⏰ 请求开始时间: {request_start_time}")
            
            # 使用带重试机制的请求
            response = await self._make_request_with_retry(
                "POST",
                f"{self.rag_service_url}/chat",
                json=payload
            )
            
            request_end_time = time.time()
            request_duration = request_end_time - request_start_time
            logger.info(f"⏰ 请求结束时间: {request_end_time}")
            logger.info(f"⏱️ 请求耗时: {request_duration:.3f} 秒")
            logger.info(f"📥 RAG服务响应状态: {response.status_code}")
            
            if response.status_code == 200:
                logger.info(f"✅ RAG服务HTTP请求成功")
                logger.info(f"📄 开始解析响应JSON...")
                
                try:
                    result = response.json()
                    logger.info(f"✅ JSON解析成功")
                    logger.info(f"📊 响应数据结构: {list(result.keys())}")
                except Exception as e:
                    logger.error(f"❌ JSON解析失败: {e}")
                    logger.error(f"📄 原始响应内容: {response.text[:500]}...")
                    return self._get_fallback_response(f"响应解析失败: {e}")
                
                logger.info(f"📈 RAG服务处理结果: {result.get('success', False)}")
                
                if result.get("success"):
                    logger.info(f"✅ RAG服务处理成功")
                    data = result.get("data", {})
                    logger.info(f"📊 数据字段: {list(data.keys())}")
                    
                    # 详细记录检索结果
                    retrieved_docs = data.get('retrieved_documents', [])
                    logger.info(f"📚 检索到 {len(retrieved_docs)} 个相关文档")
                    
                    if retrieved_docs:
                        logger.info(f"📄 检索文档详情:")
                        for i, doc in enumerate(retrieved_docs):
                            logger.info(f"   📄 文档 {i+1}:")
                            logger.info(f"      - 标题: {doc.get('title', 'N/A')}")
                            logger.info(f"      - 相关性: {doc.get('score', 0):.3f}")
                            logger.info(f"      - 内容长度: {len(doc.get('content', ''))} 字符")
                            logger.debug(f"      - 内容预览: {doc.get('content', '')[:200]}...")
                    else:
                        logger.info(f"📄 未检索到相关文档")
                    
                    # 记录处理时间
                    processing_time = data.get('processing_time', 0)
                    logger.info(f"⏱️ RAG服务处理时间: {processing_time:.3f}秒")
                    
                    # 记录最终答案
                    answer = data.get('answer', '抱歉，我暂时无法回答您的问题。')
                    logger.info(f"💬 AI回复内容:")
                    logger.info(f"   - 长度: {len(answer)} 字符")
                    logger.info(f"   - 预览: {answer[:200]}...")
                    
                    # 构建返回结果
                    result_data = {
                        'success': True,
                        'answer': answer,
                        'retrieved_documents': retrieved_docs,
                        'processing_time': processing_time,
                        'timestamp': data.get('timestamp', ''),
                        'rag_used': True
                    }
                    
                    logger.info(f"📦 返回结果构建完成")
                    logger.info(f"📊 返回数据统计:")
                    logger.info(f"   - 成功: {result_data['success']}")
                    logger.info(f"   - 使用RAG: {result_data['rag_used']}")
                    logger.info(f"   - 检索文档数: {len(result_data['retrieved_documents'])}")
                    logger.info(f"   - 处理时间: {result_data['processing_time']:.3f}秒")
                    logger.info(f"   - 回复长度: {len(result_data['answer'])} 字符")
                    
                    return result_data
                else:
                    error_msg = result.get('message', 'Unknown error')
                    logger.error(f"❌ RAG服务处理失败")
                    logger.error(f"📋 错误信息: {error_msg}")
                    logger.error(f"📊 完整响应: {result}")
                    return self._get_fallback_response(f"RAG服务返回错误: {error_msg}")
            else:
                logger.error(f"❌ RAG服务HTTP请求失败")
                logger.error(f"📊 状态码: {response.status_code}")
                logger.error(f"📄 响应头: {dict(response.headers)}")
                logger.error(f"📄 响应内容: {response.text[:500]}...")
                return self._get_fallback_response(f"RAG服务HTTP错误: {response.status_code}")
            
        except httpx.TimeoutException as e:
            logger.error(f"❌ RAG服务请求超时")
            logger.error(f"🔍 错误类型: {type(e).__name__}")
            logger.error(f"📋 错误详情: {str(e)}")
            logger.error(f"⏰ 超时配置: 连接={self.timeout.connect}s, 读取={self.timeout.read}s")
            logger.error(f"🔄 重试次数: {self.max_retries}")
            return self._get_fallback_response(f"RAG服务请求超时: {str(e)}")
            
        except httpx.ConnectError as e:
            logger.error(f"❌ RAG服务连接失败")
            logger.error(f"🔍 错误类型: {type(e).__name__}")
            logger.error(f"📋 错误详情: {str(e)}")
            logger.error(f"🌐 服务URL: {self.rag_service_url}")
            return self._get_fallback_response(f"RAG服务连接失败: {str(e)}")
            
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ RAG服务HTTP状态错误")
            logger.error(f"🔍 错误类型: {type(e).__name__}")
            logger.error(f"📊 状态码: {e.response.status_code}")
            logger.error(f"📋 错误详情: {str(e)}")
            logger.error(f"📄 响应内容: {e.response.text[:500]}...")
            return self._get_fallback_response(f"RAG服务HTTP错误 {e.response.status_code}: {str(e)}")
            
        except Exception as e:
            logger.error(f"❌ RAG服务生成回复失败")
            logger.error(f"🔍 错误类型: {type(e).__name__}")
            logger.error(f"📋 错误详情: {str(e)}")
            logger.error(f"📍 错误位置: {e.__traceback__.tb_frame.f_code.co_filename}:{e.__traceback__.tb_lineno}")
            return self._get_fallback_response(str(e))
    
    
    def _get_fallback_response(self, error_msg: str) -> Dict[str, Any]:
        """获取备用回复"""
        logger.info(f"🔄 开始生成备用回复...")
        logger.info(f"📋 错误原因: {error_msg}")
        
        fallback_responses = [
            "您好！我是您的AI医生助手。请详细描述您的症状，我会尽力帮助您。",
            "感谢您的咨询。请提供更多详细信息，我会为您提供专业的建议。",
            "我理解您的担心。请详细描述您的情况，我会尽力协助您。",
            "您好！请详细说明您的症状或问题，我会为您提供专业的医疗建议。",
            "感谢您的信任。请提供更多信息，我会尽力帮助您解决问题。"
        ]
        
        import random
        selected_response = random.choice(fallback_responses)
        logger.info(f"✅ 备用回复已选择: {selected_response[:100]}...")
        
        fallback_data = {
            'success': False,
            'answer': selected_response,
            'retrieved_documents': [],
            'processing_time': 0,
            'timestamp': '',
            'rag_used': False,
            'error': error_msg,
            'fallback_used': True
        }
        
        logger.info(f"📦 备用回复数据构建完成")
        logger.info(f"📊 备用回复统计:")
        logger.info(f"   - 成功: {fallback_data['success']}")
        logger.info(f"   - 使用RAG: {fallback_data['rag_used']}")
        logger.info(f"   - 使用备用: {fallback_data['fallback_used']}")
        logger.info(f"   - 错误信息: {fallback_data['error']}")
        
        return fallback_data
    
    async def add_knowledge_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """
        添加知识文档到RAG系统
        
        Args:
            documents: 文档列表
            
        Returns:
            是否添加成功
        """
        try:
            # 检查服务是否可用
            if not await self._ensure_service_available():
                logger.error("RAG服务不可用，无法添加文档")
                return False
            
            # 调用RAG服务的documents接口
            response = await self._make_request_with_retry(
                "POST",
                f"{self.rag_service_url}/documents",
                json=documents
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("success", False)
            else:
                logger.error(f"添加文档失败: HTTP {response.status_code}")
                return False
            
        except Exception as e:
            logger.error(f"添加知识文档失败: {e}")
            return False
    
    async def query_knowledge(self, question: str, top_k: int = 5) -> Dict[str, Any]:
        """
        查询知识库
        
        Args:
            question: 查询问题
            top_k: 返回文档数量
            
        Returns:
            查询结果
        """
        try:
            # 检查服务是否可用
            if not await self._ensure_service_available():
                return {
                    'success': False,
                    'error': 'RAG服务不可用'
                }
            
            # 调用RAG服务的query接口
            payload = {
                "question": question,
                "top_k": top_k
            }
            
            response = await self._make_request_with_retry(
                "POST",
                f"{self.rag_service_url}/query",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    return {
                        'success': True,
                        'result': result.get("data", {})
                    }
                else:
                    return {
                        'success': False,
                        'error': result.get('message', 'Unknown error')
                    }
            else:
                return {
                    'success': False,
                    'error': f'HTTP错误: {response.status_code}'
                }
            
        except Exception as e:
            logger.error(f"查询知识库失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def is_available(self) -> bool:
        """检查RAG服务是否可用"""
        return self.is_available_flag is True
    
    async def generate_response_stream(self, 
                                     user_message: str, 
                                     conversation_history: List[Dict[str, str]] = None,
                                     top_k: int = 5) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式生成AI回复
        
        Args:
            user_message: 用户消息
            conversation_history: 对话历史
            top_k: 检索文档数量
            
        Yields:
            包含流式回复片段的字典
        """
        try:
            logger.info(f"🌊 RAG服务开始流式处理用户消息")
            logger.info(f"📝 用户消息: {user_message[:100]}...")
            logger.info(f"📊 消息长度: {len(user_message)} 字符")
            
            # 检查服务是否可用
            logger.info(f"🔍 开始检查RAG服务可用性...")
            if not await self._ensure_service_available():
                logger.error("❌ RAG服务不可用，无法处理请求")
                yield self._get_fallback_response("RAG服务不可用")
                return
            logger.info(f"✅ RAG服务可用性检查通过")
            
            # 构建对话历史
            logger.info(f"📚 开始构建对话历史...")
            if conversation_history is None:
                conversation_history = []
                logger.info(f"📝 对话历史为空，初始化为空列表")
            else:
                logger.info(f"📝 接收到 {len(conversation_history)} 条历史消息")
            
            # 添加当前用户消息
            conversation_history.append({
                'role': 'user',
                'content': user_message
            })
            logger.info(f"✅ 当前用户消息已添加到对话历史")
            
            logger.info(f"📊 对话历史统计:")
            logger.info(f"   - 总消息数: {len(conversation_history)}")
            logger.info(f"   - 检索参数: top_k={top_k}")
            
            # 记录对话历史详情
            for i, msg in enumerate(conversation_history):
                logger.debug(f"📄 消息 {i+1}: {msg['role']} - {msg['content'][:50]}...")
            
            # 调用RAG服务的chat接口
            payload = {
                "messages": conversation_history,
                "top_k": top_k
            }
            
            logger.info(f"🚀 准备发送流式请求到RAG服务")
            logger.info(f"🌐 目标URL: {self.rag_service_url}/chat")
            logger.info(f"📤 请求载荷大小: {len(str(payload))} 字符")
            logger.debug(f"📤 完整请求载荷: {payload}")
            
            # 记录请求开始时间
            request_start_time = time.time()
            logger.info(f"⏰ 流式请求开始时间: {request_start_time}")
            
            # 由于RAG服务的/chat端点不是流式的，我们先获取完整回复，然后模拟流式输出
            logger.info(f"📥 调用RAG服务获取完整回复...")
            
            # 使用普通请求获取完整回复
            response = await self._make_request_with_retry(
                "POST",
                f"{self.rag_service_url}/chat",
                json=payload
            )
            
            logger.info(f"📥 RAG服务响应状态: {response.status_code}")
            
            if response.status_code == 200:
                logger.info(f"✅ RAG服务请求成功")
                
                # 发送开始信号
                yield {
                    'type': 'start',
                    'message': '开始生成回复...',
                    'timestamp': datetime.now().isoformat()
                }
                
                try:
                    result = response.json()
                    logger.info(f"✅ JSON解析成功")
                    logger.info(f"📊 响应数据结构: {list(result.keys())}")
                except Exception as e:
                    logger.error(f"❌ JSON解析失败: {e}")
                    yield {
                        'type': 'error',
                        'message': f'响应解析失败: {e}',
                        'timestamp': datetime.now().isoformat()
                    }
                    return
                
                if result.get("success"):
                    logger.info(f"✅ RAG服务处理成功")
                    data = result.get("data", {})
                    answer = data.get('answer', '抱歉，我暂时无法回答您的问题。')
                    
                    logger.info(f"💬 完整AI回复: {answer[:200]}...")
                    logger.info(f"📊 回复长度: {len(answer)} 字符")
                    
                    # 模拟流式输出：将回复分成小块逐步发送
                    chunk_size = 20  # 每次发送20个字符
                    full_response = ""
                    
                    for i in range(0, len(answer), chunk_size):
                        chunk = answer[i:i + chunk_size]
                        full_response += chunk
                        
                        # 发送内容片段
                        yield {
                            'type': 'content',
                            'content': chunk,
                            'full_content': full_response,
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        # 添加小延迟模拟真实流式输出
                        await asyncio.sleep(0.1)
                    
                    # 发送完成信号
                    yield {
                        'type': 'done',
                        'full_content': full_response,
                        'message': '回复生成完成',
                        'timestamp': datetime.now().isoformat()
                    }
                    
                else:
                    error_msg = result.get('message', 'Unknown error')
                    logger.error(f"❌ RAG服务处理失败: {error_msg}")
                    yield {
                        'type': 'error',
                        'message': f'RAG服务返回错误: {error_msg}',
                        'timestamp': datetime.now().isoformat()
                    }
            else:
                logger.error(f"❌ RAG服务请求失败")
                logger.error(f"📊 状态码: {response.status_code}")
                yield {
                    'type': 'error',
                    'message': f'RAG服务HTTP错误: {response.status_code}',
                    'timestamp': datetime.now().isoformat()
                }
            
        except httpx.TimeoutException as e:
            logger.error(f"❌ RAG服务流式请求超时")
            logger.error(f"🔍 错误类型: {type(e).__name__}")
            logger.error(f"📋 错误详情: {str(e)}")
            yield {
                'type': 'error',
                'message': f'RAG服务请求超时: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
            
        except httpx.ConnectError as e:
            logger.error(f"❌ RAG服务流式连接失败")
            logger.error(f"🔍 错误类型: {type(e).__name__}")
            logger.error(f"📋 错误详情: {str(e)}")
            yield {
                'type': 'error',
                'message': f'RAG服务连接失败: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ RAG服务流式生成回复失败")
            logger.error(f"🔍 错误类型: {type(e).__name__}")
            logger.error(f"📋 错误详情: {str(e)}")
            yield {
                'type': 'error',
                'message': f'流式生成失败: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }

    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息"""
        return {
            'available': self.is_available(),
            'service_type': 'RAG',
            'description': '知识检索和生成服务',
            'version': '1.0.0',
            'service_url': self.rag_service_url
        }


# 全局RAG服务实例
rag_service = RAGService()


def get_rag_service() -> RAGService:
    """获取RAG服务实例"""
    return rag_service
