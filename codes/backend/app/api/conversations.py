"""
对话API路由
处理对话会话和消息管理
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
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
from ..services.rag_service import get_rag_service
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
    
    # 调用RAG服务生成AI回复
    try:
        logger.info(f"🤖 开始为对话 {message_data.conversation_id} 生成AI回复")
        logger.info(f"👤 用户消息: {message_data.content[:100]}...")
        
        # 获取RAG服务实例
        rag_service = get_rag_service()
        
        # 构建对话历史
        conversation_history = []
        for msg in conversation.messages[-5:]:  # 取最近5条消息作为上下文
            conversation_history.append({
                'role': msg.role,
                'content': msg.content
            })
        
        logger.info(f"📚 对话历史: {len(conversation_history)} 条消息")
        for i, msg in enumerate(conversation_history):
            logger.debug(f"📝 历史消息 {i+1}: {msg['role']} - {msg['content'][:50]}...")
        
        # 调用RAG服务生成回复
        logger.info("🚀 调用RAG服务生成回复...")
        rag_result = await rag_service.generate_response(
            user_message=message_data.content,
            conversation_history=conversation_history,
            top_k=5
        )
        
        ai_response = rag_result.get('answer', '抱歉，我暂时无法回答您的问题。')
        
        # 记录RAG处理信息
        rag_metadata = {
            'rag_used': rag_result.get('rag_used', False),
            'retrieved_documents': len(rag_result.get('retrieved_documents', [])),
            'processing_time': rag_result.get('processing_time', 0),
            'timestamp': rag_result.get('timestamp', ''),
            'success': rag_result.get('success', False)
        }
        
        logger.info(f"✅ RAG服务处理完成:")
        logger.info(f"   - 成功: {rag_result.get('success', False)}")
        logger.info(f"   - 使用RAG: {rag_result.get('rag_used', False)}")
        logger.info(f"   - 检索文档数: {len(rag_result.get('retrieved_documents', []))}")
        logger.info(f"   - 处理时间: {rag_result.get('processing_time', 0):.3f}秒")
        logger.info(f"   - AI回复长度: {len(ai_response)} 字符")
        
        if not rag_result.get('success', False):
            rag_metadata['error'] = rag_result.get('error', 'Unknown error')
            if rag_result.get('fallback_used', False):
                rag_metadata['fallback_used'] = True
            logger.warning(f"⚠️ RAG服务处理失败: {rag_metadata.get('error', 'Unknown error')}")
        
    except Exception as e:
        logger.error(f"❌ RAG服务调用失败: {e}")
        # 备用回复
        ai_response = "您好！我是您的AI医生助手。请详细描述您的症状，我会尽力帮助您。"
        rag_metadata = {
            'rag_used': False,
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
        message_data=rag_metadata
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
    
    # 调用RAG服务生成AI回复
    try:
        logger.info(f"🤖 开始调用RAG服务生成AI回复...")
        
        # 获取RAG服务实例
        logger.info(f"🔧 获取RAG服务实例...")
        rag_service = get_rag_service()
        logger.info(f"✅ RAG服务实例获取成功")
        
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
        
        # 调用RAG服务生成回复
        logger.info(f"🚀 开始调用RAG服务生成回复...")
        logger.info(f"📤 用户消息: {message_data.content[:100]}...")
        logger.info(f"🎯 检索参数: top_k=5")
        
        rag_result = await rag_service.generate_response(
            user_message=message_data.content,
            conversation_history=conversation_history,
            top_k=5
        )
        
        logger.info(f"📥 RAG服务调用完成")
        
        # 处理RAG服务返回结果
        logger.info(f"📊 开始处理RAG服务返回结果...")
        ai_response_content = rag_result.get('answer', '抱歉，我暂时无法回答您的问题。')
        logger.info(f"💬 AI回复内容: {ai_response_content[:200]}...")
        
        # 记录RAG处理信息
        rag_metadata = {
            'rag_used': rag_result.get('rag_used', False),
            'retrieved_documents': len(rag_result.get('retrieved_documents', [])),
            'processing_time': rag_result.get('processing_time', 0),
            'timestamp': rag_result.get('timestamp', ''),
            'success': rag_result.get('success', False)
        }
        
        logger.info(f"📈 RAG处理统计:")
        logger.info(f"   - 成功: {rag_result.get('success', False)}")
        logger.info(f"   - 使用RAG: {rag_result.get('rag_used', False)}")
        logger.info(f"   - 检索文档数: {len(rag_result.get('retrieved_documents', []))}")
        logger.info(f"   - 处理时间: {rag_result.get('processing_time', 0):.3f}秒")
        
        if not rag_result.get('success', False):
            error_msg = rag_result.get('error', 'Unknown error')
            logger.warning(f"⚠️ RAG服务返回错误: {error_msg}")
            rag_metadata['error'] = error_msg
            if rag_result.get('fallback_used', False):
                logger.info(f"🔄 使用了备用回复")
                rag_metadata['fallback_used'] = True
        
    except Exception as e:
        logger.error(f"❌ RAG服务调用失败: {e}")
        logger.error(f"🔍 错误类型: {type(e).__name__}")
        logger.error(f"📋 错误详情: {str(e)}")
        
        # 备用回复
        ai_response_content = "您好！我是您的AI医生助手。请详细描述您的症状，我会尽力帮助您。"
        logger.info(f"🔄 使用备用回复: {ai_response_content}")
        
        rag_metadata = {
            'rag_used': False,
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
        message_data=rag_metadata
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
    
    # 获取RAG服务实例
    logger.info(f"🔧 获取RAG服务实例...")
    rag_service = get_rag_service()
    logger.info(f"✅ RAG服务实例获取成功")
    
    async def generate_stream():
        """生成流式响应"""
        try:
            # 发送开始信号
            yield f"data: {json.dumps({'type': 'start', 'message': '开始生成回复...', 'timestamp': datetime.now().isoformat()}, ensure_ascii=False)}\n\n"
            
            # 调用RAG服务的流式生成
            logger.info(f"🚀 开始调用RAG服务流式生成...")
            full_response = ""
            
            async for chunk in rag_service.generate_response_stream(
                user_message=message_data.content,
                conversation_history=conversation_history,
                top_k=5
            ):
                logger.debug(f"📦 收到流式数据块: {chunk}")
                
                # 发送数据块
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                
                # 如果是内容块，累积完整回复
                if chunk.get('type') == 'content':
                    full_response = chunk.get('full_content', full_response)
                
                # 如果是完成信号，保存消息到数据库
                elif chunk.get('type') == 'done':
                    full_response = chunk.get('full_content', full_response)
                    logger.info(f"✅ 流式生成完成，开始保存到数据库...")
                    
                    # 保存用户消息
                    db.add(user_message)
                    db.flush()  # 获取ID但不提交
                    
                    # 创建AI回复消息
                    ai_message = Message(
                        conversation_id=conversation_id,
                        user_id=None,  # AI消息没有用户ID
                        content=full_response,
                        content_type="text",
                        role="assistant",
                        message_data={
                            'rag_used': True,
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
                    
                    # 发送最终完成信号
                    final_chunk = {
                        'type': 'final',
                        'message': '回复生成完成',
                        'user_message_id': str(user_message.id),
                        'ai_message_id': str(ai_message.id),
                        'full_content': full_response,
                        'timestamp': datetime.now().isoformat()
                    }
                    yield f"data: {json.dumps(final_chunk, ensure_ascii=False)}\n\n"
                    break
                
                # 如果是错误信号
                elif chunk.get('type') == 'error':
                    logger.error(f"❌ 流式生成错误: {chunk.get('message', 'Unknown error')}")
                    break
            
            # 发送结束信号
            yield f"data: {json.dumps({'type': 'end', 'timestamp': datetime.now().isoformat()}, ensure_ascii=False)}\n\n"
            
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