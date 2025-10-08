"""
对话API路由
处理对话会话和消息管理
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..auth import get_current_user
from ..models.user import User
from ..models.conversation import (
    Conversation, Message, ConversationCreate, ConversationUpdate, ConversationResponse,
    MessageCreate, MessageUpdate, MessageResponse, SendMessageRequest, SendMessageResponse,
    SimpleMessageCreate
)
from ..modules.conversation import ConversationManager, ConversationInput, ConversationOutput
from app.services.retrieval_service import get_retrieval_service
from app.services.diagnosis_service import get_diagnosis_service
import httpx
import asyncio
import logging

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["对话"])

# 创建对话管理器实例
conversation_manager = ConversationManager()


@router.post("/", response_model=ConversationResponse, summary="创建对话")
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建新的对话会话
    
    - **title**: 对话标题（可选）
    - **status**: 对话状态（默认为active）
    """
    # 调试信息：打印接收到的数据
    print(f"🔍 接收到的对话数据: {conversation_data}")
    print(f"🔍 数据类型: {type(conversation_data)}")
    print(f"🔍 数据内容: title={conversation_data.title}, conversation_type={conversation_data.conversation_type}")
    print(f"🔍 用户ID: {current_user.id}")
    print(f"🔍 用户名: {current_user.username}")
    new_conversation = Conversation(
        user_id=current_user.id,
        title=conversation_data.title,
        status=conversation_data.status,
        conversation_type=conversation_data.conversation_type,
        meta_data=conversation_data.meta_data
    )
    
    db.add(new_conversation)
    db.commit()
    db.refresh(new_conversation)
    
    return ConversationResponse(
        id=str(new_conversation.id),
        user_id=str(new_conversation.user_id),
        title=new_conversation.title,
        status=new_conversation.status,
        conversation_type=new_conversation.conversation_type,
        meta_data=new_conversation.meta_data,
        created_at=new_conversation.created_at,
        updated_at=new_conversation.updated_at
    )


@router.get("/", response_model=List[ConversationResponse], summary="获取对话列表")
async def get_conversations(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回记录数"),
    status: Optional[str] = Query(None, description="对话状态过滤"),
    conversation_type: Optional[str] = Query(None, description="对话类型过滤"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取当前用户的对话列表
    
    - **skip**: 跳过记录数（分页用）
    - **limit**: 返回记录数（最大100）
    - **status**: 对话状态过滤（可选）
    - **conversation_type**: 对话类型过滤（可选，如：chat, diagnosis, consultation）
    """
    query = db.query(Conversation).filter(Conversation.user_id == current_user.id)
    
    if status:
        query = query.filter(Conversation.status == status)
    
    if conversation_type:
        query = query.filter(Conversation.conversation_type == conversation_type)
    
    conversations = query.order_by(Conversation.updated_at.desc()).offset(skip).limit(limit).all()
    
    print(f"🔍 获取对话列表 - 用户ID: {current_user.id}, 类型过滤: {conversation_type}, 找到: {len(conversations)} 个对话")
    
    return [
        ConversationResponse(
            id=str(conv.id),
            user_id=str(conv.user_id),
            title=conv.title,
            status=conv.status,
            conversation_type=conv.conversation_type,
            meta_data=conv.meta_data,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=len(conv.messages)
        )
        for conv in conversations
    ]


@router.get("/{conversation_id}", response_model=ConversationResponse, summary="获取对话详情")
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取指定对话的详情
    
    - **conversation_id**: 对话ID
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    return ConversationResponse(
        id=str(conversation.id),
        user_id=str(conversation.user_id),
        title=conversation.title,
        status=conversation.status,
        conversation_type=conversation.conversation_type,
        meta_data=conversation.meta_data,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        message_count=len(conversation.messages)
    )


@router.put("/{conversation_id}", response_model=ConversationResponse, summary="更新对话")
async def update_conversation(
    conversation_id: str,
    conversation_data: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新对话信息
    
    - **conversation_id**: 对话ID
    - **title**: 新标题
    - **status**: 新状态
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    if conversation_data.title is not None:
        conversation.title = conversation_data.title
    
    if conversation_data.status is not None:
        conversation.status = conversation_data.status
    
    if conversation_data.conversation_type is not None:
        conversation.conversation_type = conversation_data.conversation_type
    
    if conversation_data.meta_data is not None:
        conversation.meta_data = conversation_data.meta_data
    
    db.commit()
    db.refresh(conversation)
    
    return ConversationResponse(
        id=str(conversation.id),
        user_id=str(conversation.user_id),
        title=conversation.title,
        status=conversation.status,
        conversation_type=conversation.conversation_type,
        meta_data=conversation.meta_data,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        message_count=len(conversation.messages)
    )


@router.delete("/{conversation_id}", summary="删除对话")
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除指定对话
    
    - **conversation_id**: 对话ID
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    db.delete(conversation)
    db.commit()
    
    return {"message": "对话已删除"}


@router.post("/send-message", response_model=SendMessageResponse, summary="发送消息")
async def send_message(
    message_data: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    发送消息到对话
    
    - **conversation_id**: 对话ID
    - **content**: 消息内容
    - **content_type**: 内容类型（默认为text）
    - **message_data**: 元数据（可选）
    """
    # 获取对话
    conversation = db.query(Conversation).filter(
        Conversation.id == message_data.conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    # 创建用户消息
    user_message = Message(
        conversation_id=message_data.conversation_id,
        user_id=current_user.id,
        content=message_data.content,
        content_type=message_data.content_type,
        role="user",
        message_data=message_data.message_data or {}
    )
    
    # 调用检索服务生成AI回复
    try:
        logger.info(f"🤖 开始为对话 {message_data.conversation_id} 生成AI回复")
        logger.info(f"👤 用户消息: {message_data.content[:100]}...")
        
        # 获取检索服务实例
        retrieval_service = get_retrieval_service()
        
        # 构建对话历史
        conversation_history = []
        for msg in conversation.messages[-5:]:  # 取最近5条消息作为上下文
            conversation_history.append({
                'role': msg.role,
                'content': msg.content,
                'content_type': msg.content_type,
                'message_data': msg.message_data or {}
            })
        
        logger.info(f"📚 对话历史: {len(conversation_history)} 条消息")
        for i, msg in enumerate(conversation_history):
            logger.debug(f"📝 历史消息 {i+1}: {msg['role']} - {msg['content'][:50]}...")
        
        # 调用检索服务生成回复
        logger.info("🚀 调用检索服务生成回复...")
        logger.info(f"📊 多模态数据: {message_data.message_data}")
        
        retrieval_result = await retrieval_service.generate_response(
            user_message=message_data.content,
            conversation_history=conversation_history,
            top_k=5,
            multimodal_data=message_data.message_data or {},
            user_id=current_user.id,
            patient_unique_ids=message_data.message_data.get('patient_unique_ids') if message_data.message_data else None,
        )
        
        ai_response = retrieval_result.get('answer', '抱歉，我暂时无法回答您的问题。')
        
        # 记录检索处理信息
        retrieval_metadata = {
            'retrieval_used': retrieval_result.get('rag_used', False),
            'retrieved_documents': len(retrieval_result.get('retrieved_documents', [])),
            'processing_time': retrieval_result.get('processing_time', 0),
            'timestamp': retrieval_result.get('timestamp', ''),
            'success': retrieval_result.get('success', False)
        }
        
        logger.info(f"✅ 检索服务处理完成:")
        logger.info(f"   - 成功: {retrieval_result.get('success', False)}")
        logger.info(f"   - 使用检索: {retrieval_result.get('rag_used', False)}")
        logger.info(f"   - 检索文档数: {len(retrieval_result.get('retrieved_documents', []))}")
        logger.info(f"   - 处理时间: {retrieval_result.get('processing_time', 0):.3f}秒")
        logger.info(f"   - AI回复长度: {len(ai_response)} 字符")
        
        if not retrieval_result.get('success', False):
            retrieval_metadata['error'] = retrieval_result.get('error', 'Unknown error')
            if retrieval_result.get('fallback_used', False):
                retrieval_metadata['fallback_used'] = True
            logger.warning(f"⚠️ 检索服务处理失败: {retrieval_metadata.get('error', 'Unknown error')}")
        
    except Exception as e:
        logger.error(f"❌ 检索服务调用失败: {e}")
        # 备用回复
        ai_response = "您好！我是您的AI医生助手。请详细描述您的症状，我会尽力帮助您。"
        retrieval_metadata = {
            'retrieval_used': False,
            'error': str(e),
            'fallback_used': True,
            'success': False
        }
    
    # 创建AI回复消息
    assistant_message = Message(
        conversation_id=message_data.conversation_id,
        user_id=None,
        content=ai_response,
        content_type="text",
        role="assistant",
        message_data=retrieval_metadata
    )
    
    # 更新对话的 updated_at 时间戳
    from datetime import datetime
    conversation.updated_at = datetime.utcnow()
    
    db.add(user_message)
    db.add(assistant_message)
    db.commit()
    db.refresh(user_message)
    db.refresh(assistant_message)
    db.refresh(conversation)
    
    return SendMessageResponse(
        message=MessageResponse(
            id=str(user_message.id),
            conversation_id=str(user_message.conversation_id),
            role=user_message.role,
            content=user_message.content,
            content_type=user_message.content_type,
            message_data=user_message.message_data,
            is_processed=user_message.is_processed,
            created_at=user_message.created_at
        ),
        conversation=ConversationResponse(
            id=str(conversation.id),
            user_id=str(conversation.user_id),
            title=conversation.title,
            status=conversation.status,
            conversation_type=conversation.conversation_type,
            meta_data=conversation.meta_data,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            message_count=len(conversation.messages) + 2
        ),
        ai_response=ai_response
    )


@router.post("/{conversation_id}/messages", response_model=SendMessageResponse, summary="发送消息到对话")
async def send_message_to_conversation(
    conversation_id: str,
    message_data: SimpleMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    发送消息到指定对话
    
    - **conversation_id**: 对话ID
    - **content**: 消息内容
    - **message_type**: 消息类型（默认为text）
    """
    logger.info(f"🎯 开始处理消息发送请求")
    logger.info(f"👤 用户ID: {current_user.id}")
    logger.info(f"💬 对话ID: {conversation_id}")
    logger.info(f"📝 消息内容: {message_data.content[:100]}...")
    logger.info(f"📋 消息类型: {message_data.message_type or 'text'}")
    
    # 验证对话存在且属于当前用户
    logger.info(f"🔍 开始验证对话存在性...")
    
    # 导入数据库日志记录器
    from ..utils.db_logger import db_logger
    
    # 记录查询操作
    db_logger.log_query(db, "SELECT", "conversations", 
                       {"id": conversation_id, "user_id": current_user.id})
    
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        logger.error(f"❌ 对话不存在或不属于当前用户: {conversation_id}")
        logger.error(f"👤 查询用户ID: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    logger.info(f"✅ 对话验证成功: {conversation.title}")
    logger.info(f"📊 对话状态: {conversation.status}")
    logger.info(f"📈 当前消息数: {len(conversation.messages)}")
    
    # 创建用户消息
    logger.info(f"📝 开始创建用户消息...")
    user_message = Message(
        conversation_id=conversation_id,
        user_id=current_user.id,
        content=message_data.content,
        content_type=message_data.message_type or "text",
        role="user",
        message_data={}
    )
    logger.info(f"✅ 用户消息创建完成: ID={user_message.id}")
    
    # 调用检索服务生成AI回复
    try:
        logger.info(f"🤖 开始调用检索服务生成AI回复...")
        
        # 获取检索服务实例
        logger.info(f"🔧 获取检索服务实例...")
        retrieval_service = get_retrieval_service()
        logger.info(f"✅ 检索服务实例获取成功")
        
        # 构建对话历史
        logger.info(f"📚 开始构建对话历史...")
        
        # 记录消息查询操作
        db_logger.log_query(db, "SELECT", "messages", 
                           {"conversation_id": conversation_id}, 
                           len(conversation.messages))
        
        conversation_history = []
        recent_messages = conversation.messages[-5:]  # 取最近5条消息作为上下文
        logger.info(f"📊 获取到 {len(recent_messages)} 条历史消息")
        
        for i, msg in enumerate(recent_messages):
            conversation_history.append({
                'role': msg.role,
                'content': msg.content
            })
            logger.debug(f"📄 历史消息 {i+1}: {msg.role} - {msg.content[:50]}...")
        
        logger.info(f"✅ 对话历史构建完成，共 {len(conversation_history)} 条消息")
        
        # 调用检索服务生成回复
        logger.info(f"🚀 开始调用检索服务生成回复...")
        logger.info(f"📤 用户消息: {message_data.content[:100]}...")
        logger.info(f"🎯 检索参数: top_k=5")
        
        retrieval_result = await retrieval_service.generate_response(
            user_message=message_data.content,
            conversation_history=conversation_history,
            top_k=5
        )
        
        logger.info(f"📥 检索服务调用完成")
        
        # 处理检索服务返回结果
        logger.info(f"📊 开始处理检索服务返回结果...")
        ai_response_content = retrieval_result.get('answer', '抱歉，我暂时无法回答您的问题。')
        logger.info(f"💬 AI回复内容: {ai_response_content[:200]}...")
        
        # 记录检索处理信息
        retrieval_metadata = {
            'retrieval_used': retrieval_result.get('rag_used', False),
            'retrieved_documents': len(retrieval_result.get('retrieved_documents', [])),
            'processing_time': retrieval_result.get('processing_time', 0),
            'timestamp': retrieval_result.get('timestamp', ''),
            'success': retrieval_result.get('success', False)
        }
        
        logger.info(f"📈 检索处理统计:")
        logger.info(f"   - 成功: {retrieval_result.get('success', False)}")
        logger.info(f"   - 使用检索: {retrieval_result.get('rag_used', False)}")
        logger.info(f"   - 检索文档数: {len(retrieval_result.get('retrieved_documents', []))}")
        logger.info(f"   - 处理时间: {retrieval_result.get('processing_time', 0):.3f}秒")
        
        if not retrieval_result.get('success', False):
            error_msg = retrieval_result.get('error', 'Unknown error')
            logger.warning(f"⚠️ 检索服务返回错误: {error_msg}")
            retrieval_metadata['error'] = error_msg
            if retrieval_result.get('fallback_used', False):
                logger.info(f"🔄 使用了备用回复")
                retrieval_metadata['fallback_used'] = True
        
    except Exception as e:
        logger.error(f"❌ 检索服务调用失败: {e}")
        logger.error(f"🔍 错误类型: {type(e).__name__}")
        logger.error(f"📋 错误详情: {str(e)}")
        
        # 备用回复
        ai_response_content = "您好！我是您的AI医生助手。请详细描述您的症状，我会尽力帮助您。"
        logger.info(f"🔄 使用备用回复: {ai_response_content}")
        
        retrieval_metadata = {
            'retrieval_used': False,
            'error': str(e),
            'fallback_used': True,
            'success': False
        }
    
    # 创建AI回复消息
    logger.info(f"📝 开始创建AI回复消息...")
    ai_message = Message(
        conversation_id=conversation_id,
        user_id=None,
        content=ai_response_content,
        content_type="text",
        role="assistant",
        message_data=retrieval_metadata
    )
    logger.info(f"✅ AI回复消息创建完成: ID={ai_message.id}")
    
    # 更新对话的 updated_at 时间戳
    logger.info(f"🕒 更新对话时间戳...")
    from datetime import datetime
    conversation.updated_at = datetime.utcnow()
    logger.info(f"✅ 对话时间戳更新完成: {conversation.updated_at}")
    
    # 保存到数据库
    logger.info(f"💾 开始保存消息到数据库...")
    
    # 导入数据库日志记录器
    from ..utils.db_logger import db_logger
    
    # 添加用户消息到数据库
    db_logger.log_insert(db, "messages", 1)
    db.add(user_message)
    logger.info(f"📝 用户消息已添加到数据库会话")
    
    # 添加AI回复消息到数据库
    db_logger.log_insert(db, "messages", 1)
    db.add(ai_message)
    logger.info(f"🤖 AI回复消息已添加到数据库会话")
    
    # 提交事务
    db_logger.log_commit(db, 2)
    logger.info(f"💾 开始提交数据库事务...")
    db.commit()
    logger.info(f"✅ 数据库事务提交成功")
    
    # 刷新数据库对象
    logger.info(f"🔄 开始刷新数据库对象...")
    db_logger.log_refresh(db, "messages", 1)
    db.refresh(user_message)
    db_logger.log_refresh(db, "messages", 1)
    db.refresh(ai_message)
    db_logger.log_refresh(db, "conversations", 1)
    db.refresh(conversation)
    logger.info(f"✅ 数据库对象刷新完成")
    
    logger.info(f"📊 最终统计:")
    logger.info(f"   - 用户消息ID: {user_message.id}")
    logger.info(f"   - AI回复ID: {ai_message.id}")
    logger.info(f"   - 对话总消息数: {len(conversation.messages) + 2}")
    logger.info(f"   - 对话更新时间: {conversation.updated_at}")
    
    # 构建响应数据
    logger.info(f"📦 开始构建响应数据...")
    
    message_response = MessageResponse(
        id=str(user_message.id),
        conversation_id=str(user_message.conversation_id),
        role=user_message.role,
        content=user_message.content,
        content_type=user_message.content_type,
        message_data=user_message.message_data,
        is_processed=user_message.is_processed,
        created_at=user_message.created_at
    )
    logger.info(f"✅ 用户消息响应构建完成")
    
    conversation_response = ConversationResponse(
        id=str(conversation.id),
        user_id=str(conversation.user_id),
        title=conversation.title,
        status=conversation.status,
        conversation_type=conversation.conversation_type,
        meta_data=conversation.meta_data,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        message_count=len(conversation.messages) + 2
    )
    logger.info(f"✅ 对话响应构建完成")
    
    response = SendMessageResponse(
        message=message_response,
        conversation=conversation_response,
        ai_response=ai_response_content
    )
    
    logger.info(f"🎉 消息处理流程完成!")
    logger.info(f"📤 准备返回响应给客户端")
    logger.info(f"💬 AI回复长度: {len(ai_response_content)} 字符")
    logger.info(f"📊 对话消息总数: {len(conversation.messages) + 2}")
    
    return response


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse], summary="获取对话消息")
async def get_conversation_messages(
    conversation_id: str,
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(50, ge=1, le=100, description="返回记录数"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取指定对话的消息列表
    
    - **conversation_id**: 对话ID
    - **skip**: 跳过记录数（分页用）
    - **limit**: 返回记录数（最大100）
    """
    # 验证对话所有权
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    # 获取消息
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at.asc()).offset(skip).limit(limit).all()
    
    return [
        MessageResponse(
            id=str(msg.id),
            conversation_id=str(msg.conversation_id),
            role=msg.role,
            content=msg.content,
            content_type=msg.content_type,
            message_data=msg.message_data,
            is_processed=msg.is_processed,
            created_at=msg.created_at
        )
        for msg in messages
    ]


@router.get("/{conversation_id}/history", summary="获取对话历史")
async def get_conversation_history(
    conversation_id: str,
    limit: int = Query(50, ge=1, le=100, description="返回记录数"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取指定对话的历史记录
    
    - **conversation_id**: 对话ID
    - **limit**: 返回记录数（最大100）
    """
    # 验证对话所有权
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    # 获取消息历史
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at.desc()).limit(limit).all()
    
    return {
        "conversation_id": conversation_id,
        "title": conversation.title,
        "message_count": len(messages),
        "messages": [
            {
                "id": str(msg.id),
                "role": msg.role,
                "content": msg.content,
                "content_type": msg.content_type,
                "created_at": msg.created_at.isoformat()
            }
            for msg in messages
        ]
    }


@router.post("/chat", response_model=SendMessageResponse, summary="智能聊天")
async def chat_with_ai(
    content: str = Form(..., description="消息内容"),
    message_type: str = Form("text", description="消息类型"),
    conversation_id: Optional[str] = Form(None, description="对话ID"),
    image_files: List[UploadFile] = File(default=[], description="图片文件列表"),
    audio_files: List[UploadFile] = File(default=[], description="音频文件列表"),
    document_files: List[UploadFile] = File(default=[], description="文档文件列表"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    与AI进行智能聊天（自动创建或使用现有对话）
    
    - **content**: 消息内容
    - **message_type**: 消息类型（默认为text）
    - **conversation_id**: 对话ID（可选，如果不提供则自动创建新对话）
    """
    logger.info(f"🤖 开始智能聊天处理")
    logger.info(f"👤 用户: {current_user.username}")
    logger.info(f"📝 消息内容: {content[:100]}...")
    logger.info(f"📁 图片文件数量: {len(image_files) if image_files else 0}")
    logger.info(f"🎵 音频文件数量: {len(audio_files) if audio_files else 0}")
    logger.info(f"📄 文档文件数量: {len(document_files) if document_files else 0}")
    
    # 如果没有提供conversation_id，创建一个新的对话
    if not conversation_id:
        logger.info(f"📝 创建新对话...")
        new_conversation = Conversation(
            user_id=current_user.id,
            title=content[:50] + "..." if len(content) > 50 else content,
            status="active",
            conversation_type="chat",
            meta_data={"auto_created": True}
        )
        
        db.add(new_conversation)
        db.commit()
        db.refresh(new_conversation)
        
        conversation_id = str(new_conversation.id)
        logger.info(f"✅ 新对话创建完成: {conversation_id}")
    else:
        logger.info(f"📝 使用现有对话: {conversation_id}")
    
    # 验证对话存在且属于当前用户
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        logger.error(f"❌ 对话不存在或无权限访问")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    logger.info(f"✅ 对话验证通过: {conversation.title}")
    
    # 处理多模态文件
    message_data_dict = {}
    if image_files:
        # 处理图片文件
        processed_images = []
        for img_file in image_files:
            # 这里可以调用多模态API处理图片
            processed_images.append({
                "filename": img_file.filename,
                "content_type": img_file.content_type,
                "size": img_file.size if hasattr(img_file, 'size') else 0
            })
        message_data_dict["image_files"] = processed_images
    
    if audio_files:
        # 处理音频文件
        processed_audio = []
        for audio_file in audio_files:
            processed_audio.append({
                "filename": audio_file.filename,
                "content_type": audio_file.content_type,
                "size": audio_file.size if hasattr(audio_file, 'size') else 0
            })
        message_data_dict["audio_files"] = processed_audio
    
    if document_files:
        # 处理文档文件
        processed_docs = []
        for doc_file in document_files:
            processed_docs.append({
                "filename": doc_file.filename,
                "content_type": doc_file.content_type,
                "size": doc_file.size if hasattr(doc_file, 'size') else 0
            })
        message_data_dict["document_files"] = processed_docs
    
    # 创建用户消息
    logger.info(f"📝 开始创建用户消息...")
    user_message = Message(
        conversation_id=conversation_id,
        user_id=current_user.id,
        content=content,
        content_type=message_type or "text",
        role="user",
        message_data=message_data_dict
    )
    logger.info(f"✅ 用户消息创建完成: ID={user_message.id}")
    
    # 调用知识检索服务获取上下文，然后调用智能诊断服务生成AI回复
    try:
        logger.info(f"🤖 开始调用知识检索和智能诊断服务生成AI回复...")
        
        # 获取服务实例
        logger.info(f"🔧 获取服务实例...")
        retrieval_service = get_retrieval_service()
        diagnosis_service = get_diagnosis_service()
        logger.info(f"✅ 服务实例获取成功")
        
        # 构建对话历史
        logger.info(f"📚 开始构建对话历史...")
        conversation_history = []
        recent_messages = conversation.messages[-5:]  # 取最近5条消息作为上下文
        logger.info(f"📊 获取到 {len(recent_messages)} 条历史消息")
        
        for i, msg in enumerate(recent_messages):
            conversation_history.append({
                'role': msg.role,
                'content': msg.content
            })
            logger.debug(f"📄 历史消息 {i+1}: {msg.role} - {msg.content[:50]}...")
        
        logger.info(f"✅ 对话历史构建完成，共 {len(conversation_history)} 条消息")
        
        # 步骤1: 调用知识检索服务获取上下文
        logger.info(f"🔍 步骤1: 开始调用知识检索服务获取上下文...")
        logger.info(f"📤 用户消息: {content[:100]}...")
        logger.info(f"🎯 检索参数: top_k=5")
        
        retrieval_result = await retrieval_service.search_knowledge(
            query=content,
            top_k=5
        )
        
        logger.info(f"📥 知识检索服务调用完成")
        
        # 处理检索结果，提取上下文
        context = ""
        if retrieval_result.get('success', False) and retrieval_result.get('data', {}).get('documents'):
            documents = retrieval_result['data']['documents']
            context_parts = []
            for doc in documents:
                if 'content' in doc:
                    context_parts.append(doc['content'])
                elif 'text' in doc:
                    context_parts.append(doc['text'])
            context = "\n\n".join(context_parts)
            logger.info(f"📚 成功获取上下文，长度: {len(context)} 字符")
        else:
            logger.info(f"📚 未获取到相关上下文")
        
        # 步骤2: 调用智能诊断服务生成诊断建议
        logger.info(f"🧠 步骤2: 开始调用智能诊断服务生成诊断建议...")
        
        diagnosis_result = await diagnosis_service.generate_diagnosis(
            query=content,
            context=context,
            response_type="diagnosis",
            enable_summary=True
        )
        
        logger.info(f"📥 智能诊断服务调用完成")
        
        # 处理智能诊断服务返回结果
        logger.info(f"📊 开始处理智能诊断服务返回结果...")
        ai_response_content = diagnosis_result.get('diagnosis_response', '抱歉，我暂时无法回答您的问题。')
        logger.info(f"💬 AI回复内容: {ai_response_content[:200]}...")
        
        # 记录处理信息
        retrieval_metadata = {
            'retrieval_used': retrieval_result.get('success', False),
            'retrieved_documents': len(retrieval_result.get('data', {}).get('documents', [])),
            'context_length': len(context),
            'diagnosis_success': diagnosis_result.get('success', False),
            'summary': diagnosis_result.get('summary', ''),
            'success': diagnosis_result.get('success', False)
        }
        
        logger.info(f"📈 处理统计:")
        logger.info(f"   - 检索成功: {retrieval_result.get('success', False)}")
        logger.info(f"   - 检索文档数: {len(retrieval_result.get('data', {}).get('documents', []))}")
        logger.info(f"   - 上下文长度: {len(context)} 字符")
        logger.info(f"   - 诊断成功: {diagnosis_result.get('success', False)}")
        
        if not diagnosis_result.get('success', False):
            error_msg = diagnosis_result.get('error', 'Unknown error')
            logger.warning(f"⚠️ 智能诊断服务返回错误: {error_msg}")
            retrieval_metadata['error'] = error_msg
        
    except Exception as e:
        logger.error(f"❌ 服务调用失败: {e}")
        logger.error(f"🔍 错误类型: {type(e).__name__}")
        logger.error(f"📋 错误详情: {str(e)}")
        
        # 备用回复
        ai_response_content = "您好！我是您的AI医生助手。请详细描述您的症状，我会尽力帮助您。"
        logger.info(f"🔄 使用备用回复: {ai_response_content}")
        
        retrieval_metadata = {
            'retrieval_used': False,
            'error': str(e),
            'fallback_used': True,
            'success': False
        }
    
    # 创建AI回复消息
    logger.info(f"📝 开始创建AI回复消息...")
    ai_message = Message(
        conversation_id=conversation_id,
        user_id=None,
        content=ai_response_content,
        content_type="text",
        role="assistant",
        message_data=retrieval_metadata
    )
    logger.info(f"✅ AI回复消息创建完成: ID={ai_message.id}")
    
    # 更新对话的 updated_at 时间戳
    logger.info(f"🕒 更新对话时间戳...")
    from datetime import datetime
    conversation.updated_at = datetime.utcnow()
    logger.info(f"✅ 对话时间戳更新完成: {conversation.updated_at}")
    
    # 保存到数据库
    logger.info(f"💾 开始保存消息到数据库...")
    
    # 导入数据库日志记录器
    from ..utils.db_logger import db_logger
    
    # 添加用户消息到数据库
    db_logger.log_insert(db, "messages", 1)
    db.add(user_message)
    logger.info(f"📝 用户消息已添加到数据库会话")
    
    # 添加AI回复消息到数据库
    db_logger.log_insert(db, "messages", 1)
    db.add(ai_message)
    logger.info(f"🤖 AI回复消息已添加到数据库会话")
    
    # 提交事务
    db_logger.log_commit(db, 2)
    logger.info(f"💾 开始提交数据库事务...")
    db.commit()
    logger.info(f"✅ 数据库事务提交成功")
    
    # 刷新数据库对象
    logger.info(f"🔄 开始刷新数据库对象...")
    db_logger.log_refresh(db, "messages", 1)
    db.refresh(user_message)
    db_logger.log_refresh(db, "messages", 1)
    db.refresh(ai_message)
    db_logger.log_refresh(db, "conversations", 1)
    db.refresh(conversation)
    logger.info(f"✅ 数据库对象刷新完成")
    
    logger.info(f"📊 最终统计:")
    logger.info(f"   - 用户消息ID: {user_message.id}")
    logger.info(f"   - AI回复ID: {ai_message.id}")
    logger.info(f"   - 对话总消息数: {len(conversation.messages) + 2}")
    logger.info(f"   - 对话更新时间: {conversation.updated_at}")
    
    # 构建响应数据
    logger.info(f"📦 开始构建响应数据...")
    
    message_response = MessageResponse(
        id=str(user_message.id),
        conversation_id=str(user_message.conversation_id),
        role=user_message.role,
        content=user_message.content,
        content_type=user_message.content_type,
        message_data=user_message.message_data,
        is_processed=user_message.is_processed,
        created_at=user_message.created_at
    )
    logger.info(f"✅ 用户消息响应构建完成")
    
    conversation_response = ConversationResponse(
        id=str(conversation.id),
        user_id=str(conversation.user_id),
        title=conversation.title,
        status=conversation.status,
        conversation_type=conversation.conversation_type,
        meta_data=conversation.meta_data,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        message_count=len(conversation.messages) + 2
    )
    logger.info(f"✅ 对话响应构建完成")
    
    response = SendMessageResponse(
        message=message_response,
        conversation=conversation_response,
        ai_response=ai_response_content
    )
    
    logger.info(f"🎉 智能聊天处理完成!")
    logger.info(f"📤 准备返回响应给客户端")
    logger.info(f"💬 AI回复长度: {len(ai_response_content)} 字符")
    logger.info(f"📊 对话消息总数: {len(conversation.messages) + 2}")
    
    return response


@router.post("/chat/stream", summary="流式智能聊天")
async def chat_with_ai_stream_fixed(
    message_data: SimpleMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    与AI进行流式智能聊天（自动创建或使用现有对话）
    
    - **content**: 消息内容
    - **message_type**: 消息类型（默认为text）
    - **conversation_id**: 对话ID（可选，如果不提供则自动创建新对话）
    
    Returns:
        流式响应，包含AI回复的实时生成过程
    """
    import json
    from datetime import datetime
    
    logger.info(f"🌊 开始流式智能聊天处理")
    logger.info(f"👤 用户: {current_user.username}")
    logger.info(f"📝 消息内容: {message_data.content[:100]}...")
    
    # 如果没有提供conversation_id，创建一个新的对话
    if not hasattr(message_data, 'conversation_id') or not message_data.conversation_id:
        logger.info(f"📝 创建新对话...")
        new_conversation = Conversation(
            user_id=current_user.id,
            title=message_data.content[:50] + "..." if len(message_data.content) > 50 else message_data.content,
            status="active",
            conversation_type="chat",
            meta_data={"auto_created": True}
        )
        
        db.add(new_conversation)
        db.commit()
        db.refresh(new_conversation)
        
        conversation_id = str(new_conversation.id)
        logger.info(f"✅ 新对话创建完成: {conversation_id}")
    else:
        conversation_id = message_data.conversation_id
        logger.info(f"📝 使用现有对话: {conversation_id}")
    
    # 验证对话存在性和所有权
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        logger.error(f"❌ 对话不存在或无权限访问")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    logger.info(f"✅ 对话验证通过: {conversation.title}")
    
    # 创建用户消息
    logger.info(f"📝 开始创建用户消息...")
    user_message = Message(
        conversation_id=conversation_id,
        user_id=current_user.id,
        content=message_data.content,
        content_type=message_data.message_type or "text",
        role="user",
        message_data={}
    )
    logger.info(f"✅ 用户消息创建完成: ID={user_message.id}")
    
    # 构建对话历史
    logger.info(f"📚 开始构建对话历史...")
    conversation_history = []
    recent_messages = conversation.messages[-5:]  # 取最近5条消息作为上下文
    logger.info(f"📊 获取到 {len(recent_messages)} 条历史消息")
    
    for i, msg in enumerate(recent_messages):
        conversation_history.append({
            'role': msg.role,
            'content': msg.content
        })
        logger.debug(f"📄 历史消息 {i+1}: {msg.role} - {msg.content[:50]}...")
    
    logger.info(f"✅ 对话历史构建完成，共 {len(conversation_history)} 条消息")
    
    # 获取检索服务实例
    logger.info(f"🔧 获取检索服务实例...")
    retrieval_service = get_retrieval_service()
    logger.info(f"✅ 检索服务实例获取成功")
    
    async def generate_stream():
        """生成流式响应"""
        try:
            # 发送开始信号
            yield f"data: {json.dumps({'type': 'start', 'message': '开始生成回复...', 'timestamp': datetime.now().isoformat()}, ensure_ascii=False)}\n\n"
            
            # 发送检索开始信号
            yield f"data: {json.dumps({'type': 'start', 'message': '开始检索相关文档...', 'timestamp': datetime.now().isoformat()}, ensure_ascii=False)}\n\n"
            
            # 步骤1: 先调用检索服务获取上下文
            logger.info(f"🔍 步骤1: 开始调用知识检索服务获取上下文...")
            retrieval_result = await retrieval_service.search_knowledge(
                query=message_data.content,
                top_k=5
            )
            
            # 处理检索结果
            context = ""
            retrieved_docs_count = 0
            if retrieval_result.get('success', False) and retrieval_result.get('data', {}).get('documents'):
                documents = retrieval_result['data']['documents']
                context_parts = []
                for doc in documents:
                    if 'content' in doc:
                        context_parts.append(doc['content'])
                    elif 'text' in doc:
                        context_parts.append(doc['text'])
                context = "\n\n".join(context_parts)
                retrieved_docs_count = len(documents)
                logger.info(f"📚 成功获取上下文，长度: {len(context)} 字符")
                
                # 发送进度信息
                yield f"data: {json.dumps({'type': 'progress', 'message': f'查询文本向量化完成', 'step': 1}, ensure_ascii=False)}\n\n"
            else:
                logger.info(f"📚 未获取到相关上下文")
                # 发送警告信息
                yield f"data: {json.dumps({'type': 'warning', 'message': '未找到相关文档'}, ensure_ascii=False)}\n\n"
            
            # 步骤2: 调用智能诊断服务生成诊断建议
            logger.info(f"🧠 步骤2: 开始调用智能诊断服务生成诊断建议...")
            
            # 获取智能诊断服务实例
            from ..services.diagnosis_service import DiagnosisServiceClient
            diagnosis_service = DiagnosisServiceClient()
            
            diagnosis_result = await diagnosis_service.generate_diagnosis(
                query=message_data.content,
                context=context,
                response_type="diagnosis",
                enable_summary=True
            )
            
            logger.info(f"📥 智能诊断服务调用完成")
            
            # 处理智能诊断服务返回结果
            ai_response_content = diagnosis_result.get('diagnosis_response', '抱歉，我暂时无法回答您的问题。')
            logger.info(f"💬 AI回复内容: {ai_response_content[:200]}...")
            
            # 发送最终答案
            yield f"data: {json.dumps({'type': 'answer', 'content': ai_response_content}, ensure_ascii=False)}\n\n"
            
            # 保存消息到数据库
            logger.info(f"✅ 开始保存消息到数据库...")
            
            # 保存用户消息
            db.add(user_message)
            db.flush()  # 获取ID但不提交
            
            # 创建AI回复消息
            ai_message = Message(
                conversation_id=conversation_id,
                user_id=None,  # AI消息没有用户ID
                content=ai_response_content,
                content_type="text",
                role="assistant",
                message_data={
                    'retrieval_used': retrieval_result.get('success', False),
                    'retrieved_documents': retrieved_docs_count,
                    'context_length': len(context),
                    'diagnosis_success': diagnosis_result.get('success', False),
                    'summary': diagnosis_result.get('summary', ''),
                    'streaming': True,
                    'timestamp': datetime.now().isoformat()
                }
            )
            db.add(ai_message)
            
            # 更新对话时间戳
            conversation.updated_at = datetime.now()
            
            # 提交事务
            db.commit()
            logger.info(f"✅ 消息已保存到数据库")
            
            # 发送完成信号
            yield f"data: {json.dumps({'type': 'done', 'message': '回复生成完成', 'timestamp': datetime.now().isoformat()}, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            logger.error(f"❌ 流式生成异常: {e}")
            error_chunk = {
                'type': 'error',
                'message': f'流式生成失败: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
            yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
    
    # 返回流式响应
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )


@router.post("/{conversation_id}/messages/stream", summary="流式发送消息到对话")
async def send_message_to_conversation_stream(
    conversation_id: str,
    message_data: SimpleMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    流式发送消息到指定对话
    
    - **conversation_id**: 对话ID
    - **message_data**: 消息数据
    
    Returns:
        流式响应，包含AI回复的实时生成过程
    """
    import json
    from datetime import datetime
    
    logger.info(f"🌊 开始流式处理对话消息")
    logger.info(f"👤 用户: {current_user.username}")
    logger.info(f"💬 对话ID: {conversation_id}")
    logger.info(f"📝 消息内容: {message_data.content[:100]}...")
    
    # 验证对话存在性和所有权
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        logger.error(f"❌ 对话不存在或无权限访问")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    logger.info(f"✅ 对话验证通过: {conversation.title}")
    
    # 创建用户消息
    logger.info(f"📝 开始创建用户消息...")
    user_message = Message(
        conversation_id=conversation_id,
        user_id=current_user.id,
        content=message_data.content,
        content_type=message_data.message_type or "text",
        role="user",
        message_data={}
    )
    logger.info(f"✅ 用户消息创建完成: ID={user_message.id}")
    
    # 构建对话历史
    logger.info(f"📚 开始构建对话历史...")
    conversation_history = []
    recent_messages = conversation.messages[-5:]  # 取最近5条消息作为上下文
    logger.info(f"📊 获取到 {len(recent_messages)} 条历史消息")
    
    for i, msg in enumerate(recent_messages):
        conversation_history.append({
            'role': msg.role,
            'content': msg.content
        })
        logger.debug(f"📄 历史消息 {i+1}: {msg.role} - {msg.content[:50]}...")
    
    logger.info(f"✅ 对话历史构建完成，共 {len(conversation_history)} 条消息")
    
    # 获取检索服务实例
    logger.info(f"🔧 获取检索服务实例...")
    retrieval_service = get_retrieval_service()
    logger.info(f"✅ 检索服务实例获取成功")
    
    async def generate_stream():
        """生成流式响应"""
        try:
            # 发送开始信号
            yield f"data: {json.dumps({'type': 'start', 'message': '开始生成回复...', 'timestamp': datetime.now().isoformat()}, ensure_ascii=False)}\n\n"
            
            # 发送检索开始信号
            yield f"data: {json.dumps({'type': 'start', 'message': '开始检索相关文档...', 'timestamp': datetime.now().isoformat()}, ensure_ascii=False)}\n\n"
            
            # 步骤1: 先调用检索服务获取上下文
            logger.info(f"🔍 步骤1: 开始调用知识检索服务获取上下文...")
            retrieval_result = await retrieval_service.search_knowledge(
                query=message_data.content,
                top_k=5
            )
            
            # 处理检索结果
            context = ""
            retrieved_docs_count = 0
            if retrieval_result.get('success', False) and retrieval_result.get('data', {}).get('documents'):
                documents = retrieval_result['data']['documents']
                context_parts = []
                for doc in documents:
                    if 'content' in doc:
                        context_parts.append(doc['content'])
                    elif 'text' in doc:
                        context_parts.append(doc['text'])
                context = "\n\n".join(context_parts)
                retrieved_docs_count = len(documents)
                logger.info(f"📚 成功获取上下文，长度: {len(context)} 字符")
                
                # 发送进度信息
                yield f"data: {json.dumps({'type': 'progress', 'message': f'查询文本向量化完成', 'step': 1}, ensure_ascii=False)}\n\n"
            else:
                logger.info(f"📚 未获取到相关上下文")
                # 发送警告信息
                yield f"data: {json.dumps({'type': 'warning', 'message': '未找到相关文档'}, ensure_ascii=False)}\n\n"
            
            # 步骤2: 调用智能诊断服务生成诊断建议
            logger.info(f"🧠 步骤2: 开始调用智能诊断服务生成诊断建议...")
            
            # 获取智能诊断服务实例
            from ..services.diagnosis_service import DiagnosisServiceClient
            diagnosis_service = DiagnosisServiceClient()
            
            diagnosis_result = await diagnosis_service.generate_diagnosis(
                query=message_data.content,
                context=context,
                response_type="diagnosis",
                enable_summary=True
            )
            
            logger.info(f"📥 智能诊断服务调用完成")
            
            # 处理智能诊断服务返回结果
            ai_response_content = diagnosis_result.get('diagnosis_response', '抱歉，我暂时无法回答您的问题。')
            logger.info(f"💬 AI回复内容: {ai_response_content[:200]}...")
            
            # 发送最终答案
            yield f"data: {json.dumps({'type': 'answer', 'content': ai_response_content}, ensure_ascii=False)}\n\n"
            
            # 保存消息到数据库
            logger.info(f"✅ 开始保存消息到数据库...")
            
            # 保存用户消息
            db.add(user_message)
            db.flush()  # 获取ID但不提交
            
            # 创建AI回复消息
            ai_message = Message(
                conversation_id=conversation_id,
                user_id=None,  # AI消息没有用户ID
                content=ai_response_content,
                content_type="text",
                role="assistant",
                message_data={
                    'retrieval_used': retrieval_result.get('success', False),
                    'retrieved_documents': retrieved_docs_count,
                    'context_length': len(context),
                    'diagnosis_success': diagnosis_result.get('success', False),
                    'summary': diagnosis_result.get('summary', ''),
                    'streaming': True,
                    'timestamp': datetime.now().isoformat()
                }
            )
            db.add(ai_message)
            
            # 更新对话时间戳
            conversation.updated_at = datetime.now()
            
            # 提交事务
            db.commit()
            logger.info(f"✅ 消息已保存到数据库")
            
            # 发送完成信号
            yield f"data: {json.dumps({'type': 'done', 'message': '回复生成完成', 'timestamp': datetime.now().isoformat()}, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            logger.error(f"❌ 流式生成异常: {e}")
            error_chunk = {
                'type': 'error',
                'message': f'流式生成失败: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
            yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
    
    # 返回流式响应
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )