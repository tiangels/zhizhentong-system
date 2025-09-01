"""
对话API路由
处理对话会话和消息管理
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
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
    
    # 创建AI回复消息
    ai_response = "您好！我是您的AI医生助手。请详细描述您的症状，我会尽力帮助您。"
    assistant_message = Message(
        conversation_id=message_data.conversation_id,
        user_id=None,
        content=ai_response,
        content_type="text",
        role="assistant",
        message_data={}
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
    # 验证对话存在且属于当前用户
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在"
        )
    
    # 创建用户消息
    user_message = Message(
        conversation_id=conversation_id,
        user_id=current_user.id,
        content=message_data.content,
        content_type=message_data.message_type or "text",
        role="user",
        message_data={}
    )
    
    # 生成AI回复（模拟数据）
    ai_responses = [
        "感谢您的咨询。根据您的描述，我建议您多休息，保持充足的水分摄入。",
        "您好！根据您提到的症状，建议您注意保暖，适当休息。如果症状持续或加重，请及时就医。",
        "我理解您的担心。对于这种情况，建议您保持良好的作息习惯，多喝温水。",
        "根据您的情况，这可能是常见的季节性症状。建议您注意饮食清淡，避免过度劳累。",
        "感谢您的信任。建议您密切观察症状变化，如有不适请及时咨询专业医生。"
    ]
    
    import random
    ai_response_content = random.choice(ai_responses)
    
    # 创建AI回复消息
    ai_message = Message(
        conversation_id=conversation_id,
        user_id=None,
        content=ai_response_content,
        content_type="text",
        role="assistant",
        message_data={}
    )
    
    # 更新对话的 updated_at 时间戳
    from datetime import datetime
    conversation.updated_at = datetime.utcnow()
    
    db.add(user_message)
    db.add(ai_message)
    db.commit()
    db.refresh(user_message)
    db.refresh(ai_message)
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
        ai_response=ai_response_content
    )


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