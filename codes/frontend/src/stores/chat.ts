/**
 * 对话状态管理Store
 * 管理对话会话、消息、实时通信等状态
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Conversation, Message, SendMessageRequest, CreateConversationRequest } from '@/types'
import { conversationApi } from '@/services/apiService'
import { generateUUID } from '@/utils/helpers'
import { STORAGE_KEYS, getUserStorageKey } from '@/utils/constants'
import { useAuthStore } from '@/stores/auth'

// ==================== 状态定义 ====================

/**
 * 对话状态接口
 */
// interface ChatState {
//   conversations: Conversation[]
//   currentConversation: Conversation | null
//   currentMessages: Message[]
//   isLoading: boolean
//   isTyping: boolean
//   error: string | null
// }

// ==================== 本地存储工具函数 ====================

/**
 * 从本地存储加载对话数据
 */
const loadConversationsFromStorage = (): Conversation[] => {
  try {
    const authStore = useAuthStore()
    const userId = authStore.currentUser?.id || authStore.user?.id
    if (!userId) {
      console.log('用户未登录，无法加载对话历史')
      return []
    }

    const userKey = getUserStorageKey(STORAGE_KEYS.CHAT_HISTORY, userId)
    const stored = localStorage.getItem(userKey)
    if (stored) {
      const parsed = JSON.parse(stored)
      // 确保返回的是数组
      if (Array.isArray(parsed)) {
        console.log(`Chat Store: 从存储加载 ${parsed.length} 个对话`)
        return parsed
      } else {
        console.warn('存储的对话数据不是数组格式，重置为空数组')
        return []
      }
    }
  } catch (error) {
    console.error('加载对话历史失败:', error)
  }
  return []
}

/**
 * 保存对话数据到本地存储
 */
const saveConversationsToStorage = (conversations: Conversation[]) => {
  try {
    const authStore = useAuthStore()
    const userId = authStore.currentUser?.id || authStore.user?.id
    if (!userId) {
      console.log('用户未登录，无法保存对话历史')
      return
    }

    const userKey = getUserStorageKey(STORAGE_KEYS.CHAT_HISTORY, userId)
    localStorage.setItem(userKey, JSON.stringify(conversations))
    console.log(`Chat Store: 保存 ${conversations.length} 个对话到存储`)
  } catch (error) {
    console.error('保存对话历史失败:', error)
  }
}

/**
 * 从本地存储加载消息数据
 */
const loadMessagesFromStorage = (): Message[] => {
  try {
    const authStore = useAuthStore()
    const userId = authStore.currentUser?.id || authStore.user?.id
    if (!userId) {
      console.log('用户未登录，无法加载消息历史')
      return []
    }

    const userKey = getUserStorageKey(STORAGE_KEYS.CHAT_MESSAGES, userId)
    const stored = localStorage.getItem(userKey)
    if (stored) {
      const parsed = JSON.parse(stored)
      // 确保返回的是数组
      if (Array.isArray(parsed)) {
        console.log(`Chat Store: 从存储加载 ${parsed.length} 条消息`)
        return parsed
      } else {
        console.warn('存储的消息数据不是数组格式，重置为空数组')
        return []
      }
    }
  } catch (error) {
    console.error('加载消息历史失败:', error)
  }
  return []
}

/**
 * 保存消息数据到本地存储
 */
const saveMessagesToStorage = (messages: Message[]) => {
  try {
    const authStore = useAuthStore()
    const userId = authStore.currentUser?.id || authStore.user?.id
    if (!userId) {
      console.log('用户未登录，无法保存消息历史')
      return
    }

    const userKey = getUserStorageKey(STORAGE_KEYS.CHAT_MESSAGES, userId)
    localStorage.setItem(userKey, JSON.stringify(messages))
    console.log(`Chat Store: 保存 ${messages.length} 条消息到存储`)
  } catch (error) {
    console.error('保存消息历史失败:', error)
  }
}

/**
 * 保存当前对话ID到本地存储
 */
const saveCurrentConversationId = (conversationId: string | null) => {
  try {
    const authStore = useAuthStore()
    const userId = authStore.currentUser?.id || authStore.user?.id
    if (!userId) {
      return
    }

    const key = `currentConversationId_${userId}`
    if (conversationId) {
      localStorage.setItem(key, conversationId)
    } else {
      localStorage.removeItem(key)
    }
  } catch (error) {
    console.error('保存当前对话ID失败:', error)
  }
}

// ==================== Store定义 ====================

export const useChatStore = defineStore('chat', () => {
  // ==================== 状态变量 ====================

  // 对话列表 - 初始化时从本地存储加载
  const conversations = ref<Conversation[]>([])

  // 当前对话
  const currentConversation = ref<Conversation | null>(null)

  // 所有消息 - 初始化时从本地存储加载
  const messages = ref<Message[]>([])

  // 确保 conversations 始终是数组的辅助函数
  const ensureConversationsArray = () => {
    if (!Array.isArray(conversations.value)) {
      console.warn('conversations.value 不是数组，重置为空数组')
      conversations.value = []
    }
  }

  // 加载状态
  const isLoading = ref(false)

  // 正在输入状态
  const isTyping = ref(false)

  // 错误信息
  const error = ref<string | null>(null)

  // ==================== 计算属性 ====================

  /**
   * 当前对话的消息列表
   */
  const currentMessages = computed(() => {
    if (!currentConversation.value) return []
    return messages.value
      .filter(msg => msg.conversationId === currentConversation.value?.id)
      .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
  })

  /**
   * 按时间排序的对话列表
   */
  const sortedConversations = computed(() => {
    return [...conversations.value].sort((a, b) => {
      const timeA = a.updatedAt || a.createdAt
      const timeB = b.updatedAt || b.createdAt
      return new Date(timeB).getTime() - new Date(timeA).getTime()
    })
  })

  // ==================== 初始化方法 ====================

  /**
   * 更新对话的lastMessage为最后一条用户消息
   */
  const updateConversationLastMessage = (conversationId: string) => {
    const conversation = conversations.value.find(c => c.id === conversationId)
    if (!conversation) return

    const lastUserMessage = messages.value
      .filter(m => m.conversationId === conversationId && m.type === 'user')
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())[0]
    
    if (lastUserMessage) {
      conversation.lastMessage = lastUserMessage.content
      conversation.lastMessageAt = lastUserMessage.timestamp
    }
  }

  /**
   * 初始化用户数据
   */
  const initializeUserData = async () => {
    const authStore = useAuthStore()
    console.log('Chat Store: 初始化用户数据')

    // 检查用户是否已认证
    if (!authStore.isAuthenticated) {
      console.log('Chat Store: 用户未认证，跳过初始化')
      return
    }

    // 首先确保从本地存储加载数据（页面刷新后的快速恢复）
    console.log('Chat Store: 从本地存储加载数据')
    const localConversations = loadConversationsFromStorage()
    const localMessages = loadMessagesFromStorage()
    
    if (localConversations.length > 0 || localMessages.length > 0) {
      conversations.value = localConversations
      messages.value = localMessages
      console.log(
        `Chat Store: 从本地存储加载了 ${localConversations.length} 个对话, ${localMessages.length} 条消息`
      )

      // 更新每个对话的lastMessage
      conversations.value.forEach(conversation => {
        updateConversationLastMessage(conversation.id)
      })
    }

    try {
      // 然后从后端同步最新数据
      console.log('Chat Store: 开始从后端同步对话列表')
      const conversationsResponse = await conversationApi.getConversations()
      
      if (conversationsResponse.success && conversationsResponse.data) {
        console.log('Chat Store: 后端对话数据:', conversationsResponse.data)

        // 转换后端数据格式为前端格式
        const backendConversations = conversationsResponse.data.map((conv: any) => ({
          id: conv.id,
          userId: conv.user_id,
          title: conv.title,
          type: conv.conversation_type || 'general',
          status: conv.status || 'active',
          messageCount: conv.message_count || 0,
          lastMessage: '',
          lastMessageAt: conv.updated_at,
          createdAt: conv.created_at,
          updatedAt: conv.updated_at,
        }))
        
        conversations.value = backendConversations
        console.log(`Chat Store: 从后端同步了 ${backendConversations.length} 个对话`)

        // 保存到本地存储
        saveConversationsToStorage(conversations.value)

        // 只更新对话的lastMessage，不加载所有消息
        console.log('Chat Store: 更新对话最后消息')
        for (const conversation of backendConversations) {
          updateConversationLastMessage(conversation.id)
        }
      } else {
        console.log('Chat Store: 后端同步失败，使用本地数据')
        // 如果后端同步失败，确保本地数据已加载
        if (conversations.value.length === 0) {
          conversations.value = localConversations
        }
        if (messages.value.length === 0) {
          messages.value = localMessages
        }
      }
    } catch (syncError) {
      console.error('Chat Store: 后端同步失败，使用本地数据:', syncError)
      // 如果后端同步失败，确保本地数据已加载
      if (conversations.value.length === 0) {
        conversations.value = localConversations
      }
      if (messages.value.length === 0) {
        messages.value = localMessages
      }
    }

    // 双重检查确保数组状态
    ensureConversationsArray()

    // 恢复当前对话状态
    const userId = authStore.currentUser?.id || authStore.user?.id
    if (userId) {
      const savedCurrentConversationId = localStorage.getItem(`currentConversationId_${userId}`)
      if (savedCurrentConversationId) {
        const conversation = conversations.value.find(c => c.id === savedCurrentConversationId)
        if (conversation) {
          currentConversation.value = conversation
          console.log('Chat Store: 恢复当前对话状态:', conversation.id)
        } else {
          // 如果本地没有找到对话，清除保存的对话ID
          localStorage.removeItem(`currentConversationId_${userId}`)
          console.log('Chat Store: 清除无效的当前对话ID')
        }
      }
    }
    console.log(
      `Chat Store: 用户数据初始化完成 - ${conversations.value.length} 个对话, ${messages.value.length} 条消息`
    )
  }

  /**
   * 同步对话消息
   */
  const syncConversationMessages = async (conversationId: string) => {
    try {
      console.log(`Chat Store: 同步对话消息 - 对话ID: ${conversationId}`)
      
      // 获取对话消息
      const messagesResponse = await conversationApi.getConversationMessages(conversationId, 0, 100)
      
      if (messagesResponse.success && messagesResponse.data) {
        console.log(`Chat Store: 获取到 ${messagesResponse.data.length} 条消息`)
        
        // 转换后端消息格式为前端格式
        const backendMessages = messagesResponse.data.map((msg: any) => ({
          id: msg.id,
          conversationId: msg.conversation_id,
          type: (msg.role === 'user' ? 'user' : 'assistant') as 'user' | 'assistant',
          contentType: (msg.content_type || 'text') as 'text' | 'image' | 'audio' | 'video' | 'file',
          content: msg.content,
          messageData: {
            content_type: msg.content_type || 'text',
            ...(msg.message_data || {}),
          },
          timestamp: msg.created_at,
          status: 'sent' as 'sending' | 'sent' | 'failed',
          createdAt: msg.created_at,
          updatedAt: msg.updated_at || msg.created_at,
        }))
        
        // 过滤掉已存在的消息，避免重复
        const existingMessageIds = messages.value.map(m => m.id)
        const newMessages = backendMessages.filter(msg => !existingMessageIds.includes(msg.id))
        
        if (newMessages.length > 0) {
          messages.value.push(...newMessages)
          saveMessagesToStorage(messages.value)
          console.log(`Chat Store: 添加了 ${newMessages.length} 条新消息`)
        }
      }
    } catch (syncError) {
      console.error(`Chat Store: 同步对话消息失败 - 对话ID: ${conversationId}`, syncError)
    }
  }

  /**
   * 清理用户数据
   */
  const clearUserData = () => {
    console.log('Chat Store: 清理用户数据')
    conversations.value = []
    messages.value = []
    currentConversation.value = null
    error.value = null
    isLoading.value = false
    isTyping.value = false
  }

  // ==================== 对话管理方法 ====================

  /**
   * 创建新对话
   */
  const createConversation = async (
    request: CreateConversationRequest
  ): Promise<Conversation | null> => {
    try {
      isLoading.value = true
      error.value = null

      const authStore = useAuthStore()
      if (!authStore.isAuthenticated) {
        throw new Error('用户未登录')
      }

      // 调用后端API创建对话
      console.log('Chat Store: 开始创建对话，请求数据:', {
        title: request.title || '新对话',
        conversation_type: request.type || 'general',
      })

      const response = await conversationApi.createConversation({
        title: request.title || '新对话',
        conversation_type: request.type || 'general',
      })

      console.log('Chat Store: API响应:', response)
      console.log('Chat Store: 响应类型:', typeof response)
      console.log('Chat Store: 响应成功标志:', response.success)
      console.log('Chat Store: 响应数据:', response.data)

      if (response.success && response.data) {
        const conversationData: Conversation = {
          id: response.data.id,
          userId: response.data.user_id,
          title: response.data.title,
          type: response.data.conversation_type,
          status: response.data.status,
          messageCount: response.data.message_count || 0,
          lastMessage: '',
          lastMessageAt: response.data.updated_at,
          createdAt: response.data.created_at,
          updatedAt: response.data.updated_at,
        }

        // 确保 conversations.value 是数组
        ensureConversationsArray()

        // 添加到对话列表
        conversations.value.unshift(conversationData)

        // 设为当前对话
        currentConversation.value = conversationData

        // 保存到存储
        saveConversationsToStorage(conversations.value)
        saveCurrentConversationId(conversationData.id)

        console.log('创建对话成功:', conversationData.title)
        return conversationData
      } else {
        throw new Error(response.message || '创建对话失败')
      }
    } catch (err) {
      console.error('创建对话失败:', err)
      error.value = err instanceof Error ? err.message : '创建对话失败'
      return null
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 选择对话
   */
  const selectConversation = (conversationId: string) => {
    const conversation = conversations.value.find(c => c.id === conversationId)
    if (conversation) {
      currentConversation.value = conversation
      saveCurrentConversationId(conversationId)
      console.log('切换到对话:', conversation.title)
    }
  }

  /**
   * 删除对话
   */
  const deleteConversation = async (conversationId: string) => {
    try {
      isLoading.value = true

      // 调用后端API删除对话
      const response = await conversationApi.deleteConversation(conversationId)
      
      if (!response.success) {
        throw new Error('删除对话失败')
      }

      // 删除对话
      conversations.value = conversations.value.filter(c => c.id !== conversationId)

      // 删除相关消息
      messages.value = messages.value.filter(m => m.conversationId !== conversationId)

      // 如果删除的是当前对话，清空当前对话
      if (currentConversation.value?.id === conversationId) {
        currentConversation.value = null
        saveCurrentConversationId(null)
      }

      // 保存到存储
      saveConversationsToStorage(conversations.value)
      saveMessagesToStorage(messages.value)

      console.log('删除对话成功')
    } catch (err) {
      console.error('删除对话失败:', err)
      error.value = err instanceof Error ? err.message : '删除对话失败'
      throw err // 重新抛出错误，让调用方处理
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 更新对话标题
   */
  const updateConversationTitle = async (conversationId: string, title: string) => {
    try {
      // 调用后端API更新标题
      const response = await conversationApi.updateConversation(conversationId, { title })
      
      if (!response.success) {
        throw new Error('更新标题失败')
      }

      // 更新本地状态
      const conversation = conversations.value.find(c => c.id === conversationId)
      if (conversation) {
        conversation.title = title
        conversation.updatedAt = new Date().toISOString()
        saveConversationsToStorage(conversations.value)
        console.log('✅ 更新对话标题成功:', title)
      }
    } catch (error) {
      console.error('❌ 更新对话标题失败:', error)
      throw error // 重新抛出错误，让调用方处理
    }
  }

  // ==================== 消息管理方法 ====================

  /**
   * 发送消息 - 使用实际API
   */
  const sendMessage = async (request: SendMessageRequest): Promise<Message | null> => {
    if (!currentConversation.value) {
      console.error('没有当前对话')
      return null
    }

    try {
      isLoading.value = true
      isTyping.value = true
      error.value = null

      // 创建用户消息
      const userMessage: Message = {
        id: generateUUID(),
        conversationId: currentConversation.value.id,
        type: 'user',
        contentType: request.contentType || 'text',
        content: request.content,
        messageData: request.messageData,
        timestamp: new Date().toISOString(),
        status: 'sent',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      }

      // 添加用户消息到列表
      messages.value.push(userMessage)
      saveMessagesToStorage(messages.value)

      // 更新对话信息
      const existingUserMessages = messages.value.filter(
        m => m.conversationId === currentConversation.value?.id && m.type === 'user'
      ).length

      if (
        existingUserMessages === 1 &&
        (currentConversation.value.title === '新对话' ||
          currentConversation.value.title === '未命名对话')
      ) {
        currentConversation.value.title =
          userMessage.content.length > 20
            ? userMessage.content.substring(0, 20) + '...'
            : userMessage.content
      }

      currentConversation.value.lastMessage = userMessage.content
      currentConversation.value.lastMessageAt = userMessage.timestamp
      currentConversation.value.messageCount = messages.value.filter(
        m => m.conversationId === currentConversation.value?.id
      ).length
      currentConversation.value.updatedAt = userMessage.timestamp

      // 保存对话更新
      saveConversationsToStorage(conversations.value)

      console.log('用户消息已发送:', userMessage.content)

      // 调用API获取AI回复
      try {
        const response = await conversationApi.sendMessage(currentConversation.value.id, {
          content: request.content,
        })

        console.log('API响应:', response)

        if (response.success && response.data) {
          // 从后端响应中提取AI回复
          const aiResponseContent = response.data.ai_response || '抱歉，暂时无法回复。'
          
          console.log('AI回复内容:', aiResponseContent)
          console.log('完整响应数据:', response.data)

          // 创建AI回复消息
          const aiMessage: Message = {
            id: generateUUID(),
            conversationId: currentConversation.value.id,
            type: 'assistant',
            contentType: 'text',
            content: aiResponseContent,
            timestamp: new Date().toISOString(),
            status: 'sent',
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          }

          // 添加AI消息到列表
          messages.value.push(aiMessage)
          saveMessagesToStorage(messages.value)

          // 更新对话信息 - 保持显示用户最后一条消息
          const lastUserMessage = messages.value
            .filter(m => m.conversationId === currentConversation.value?.id && m.type === 'user')
            .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())[0]
          
          if (lastUserMessage) {
            currentConversation.value.lastMessage = lastUserMessage.content
            currentConversation.value.lastMessageAt = lastUserMessage.timestamp
          }
          currentConversation.value.messageCount = messages.value.filter(
            m => m.conversationId === currentConversation.value?.id
          ).length
          currentConversation.value.updatedAt = aiMessage.timestamp

          // 保存对话更新
          saveConversationsToStorage(conversations.value)

          console.log('AI回复已接收:', aiResponseContent)
          return aiMessage
        } else {
          throw new Error(response.message || 'API调用失败')
        }
      } catch (apiError) {
        // 改进错误日志，确保错误信息可读
        const errorMessage =
          apiError instanceof Error
            ? apiError.message
            : typeof apiError === 'object'
              ? JSON.stringify(apiError)
              : String(apiError)
        console.error('API调用失败，使用模拟回复:', errorMessage)
        console.error('完整错误对象:', apiError)

        // 如果API调用失败，返回模拟回复
        return await sendMockMessage(userMessage.content)
      }
    } catch (err) {
      console.error('发送消息失败:', err)
      error.value = err instanceof Error ? err.message : '发送消息失败'
      return null
    } finally {
      isLoading.value = false
      isTyping.value = false
    }
  }

  /**
   * 打字机效果 - 逐字显示文本，模拟医生边思考边回复的自然感
   */
  const typewriterEffect = async (
    targetMessage: Message,
    fullContent: string,
    baseSpeed: number = 60
  ) => {
    const messageIndex = messages.value.findIndex(m => m.id === targetMessage.id)
    if (messageIndex === -1) return

    let currentContent = ''
    const characters = fullContent.split('')
    
    for (let i = 0; i < characters.length; i++) {
      currentContent += characters[i]
      targetMessage.content = currentContent
      targetMessage.updatedAt = new Date().toISOString()
      
      // 强制触发Vue响应式更新
      messages.value[messageIndex] = { ...targetMessage }
      saveMessagesToStorage(messages.value)
      
      // 根据字符类型调整显示速度，模拟自然思考停顿
      let delay = baseSpeed
      const char = characters[i]
      
      if (char === '。' || char === '！' || char === '？') {
        // 句号、感叹号、问号后停顿150ms，模拟思考
        delay = 150
      } else if (char === '，' || char === '；' || char === '：') {
        // 逗号、分号、冒号后停顿100ms
        delay = 100
      } else if (char === ' ' || char === '\n') {
        // 空格和换行停顿80ms
        delay = 80
      } else if (/[a-zA-Z0-9]/.test(char)) {
        // 英文字母和数字稍快一些
        delay = baseSpeed * 0.8
      } else {
        // 中文字符使用基础速度
        delay = baseSpeed
      }
      
      await new Promise(resolve => setTimeout(resolve, delay))
    }
  }

  /**
   * 发送消息（流式）
   */
  const sendMessageStream = async (request: SendMessageRequest): Promise<Message | null> => {
    if (!currentConversation.value) {
      console.error('没有当前对话')
      return null
    }

    // 检查用户是否已登录
    const authStore = useAuthStore()
    if (!authStore.isLoggedIn) {
      console.error('用户未登录，无法发送消息')
      return null
    }

    try {
      isLoading.value = true
      isTyping.value = true
      error.value = null

      // 创建用户消息
      const userMessage: Message = {
        id: generateUUID(),
        conversationId: currentConversation.value.id,
        type: 'user',
        contentType: request.contentType || 'text',
        content: request.content,
        messageData: request.messageData,
        timestamp: new Date().toISOString(),
        status: 'sent',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      }

      // 添加用户消息到列表
      messages.value.push(userMessage)
      saveMessagesToStorage(messages.value)

      // 更新对话信息
      const existingUserMessages = messages.value.filter(
        m => m.conversationId === currentConversation.value?.id && m.type === 'user'
      ).length

      if (
        existingUserMessages === 1 &&
        (currentConversation.value.title === '新对话' ||
          currentConversation.value.title === '未命名对话')
      ) {
        currentConversation.value.title =
          userMessage.content.length > 20
            ? userMessage.content.substring(0, 20) + '...'
            : userMessage.content
      }

      currentConversation.value.lastMessage = userMessage.content
      currentConversation.value.lastMessageAt = userMessage.timestamp
      currentConversation.value.messageCount = messages.value.filter(
        m => m.conversationId === currentConversation.value?.id
      ).length
      currentConversation.value.updatedAt = userMessage.timestamp

      // 保存对话更新
      saveConversationsToStorage(conversations.value)

      console.log('用户消息已发送:', userMessage.content)

      // 创建AI消息占位符
      const aiMessage: Message = {
        id: generateUUID(),
        conversationId: currentConversation.value.id,
        type: 'assistant',
        contentType: 'text',
        content: '',
        timestamp: new Date().toISOString(),
        status: 'sending',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      }

      // 添加AI消息占位符到列表
      messages.value.push(aiMessage)
      saveMessagesToStorage(messages.value)

      // 存储完整内容用于打字机效果
      let fullContent = ''

      // 调用流式API
      try {
        await conversationApi.sendMessageStream(
          currentConversation.value.id,
          {
            content: request.content,
            content_type: request.messageType || 'text',
            message_data: request.messageData || {},
          },
          (data) => {
            console.log('收到流式数据:', data)
            
            switch (data.type) {
              case 'start':
                console.log('开始生成回复...')
                break
              case 'progress':
                // 处理进度信息
                console.log('进度更新:', data.message)
                break
              case 'warning':
                // 处理警告信息
                console.warn('警告:', data.message)
                break
              case 'content':
                // 累积完整内容
                if (data.full_content !== undefined) {
                  fullContent = data.full_content
                } else if (data.content !== undefined) {
                  fullContent += data.content
                }
                break
              case 'answer':
                // 处理最终答案
                if (data.content !== undefined) {
                  fullContent = data.content
                }
                console.log('收到最终答案:', data.content)
                break
              case 'done':
                console.log('回复生成完成')
                break
              case 'final':
                // 使用最终内容
                fullContent = data.full_content || fullContent
                break
              case 'error':
                console.error('流式生成错误:', data.message)
                fullContent = '抱歉，生成回复时出现错误。'
                break
            }
          },
          (error) => {
            console.error('流式API错误:', error)
            fullContent = '抱歉，无法获取回复。'
          },
          async () => {
            console.log('流式生成完成，开始打字机效果')
            
            // 开始打字机效果 - 模拟医生边思考边回复的自然感
            if (fullContent) {
              await typewriterEffect(aiMessage, fullContent, 60) // 60ms基础速度，标点处会延长
            }
            
            // 更新消息状态
            aiMessage.status = 'sent'
            aiMessage.updatedAt = new Date().toISOString()
            
            // 强制触发Vue响应式更新
            const messageIndex = messages.value.findIndex(m => m.id === aiMessage.id)
            if (messageIndex !== -1) {
              messages.value[messageIndex] = { ...aiMessage }
            }
            
            saveMessagesToStorage(messages.value)
            
            // 更新对话信息 - 保持显示用户最后一条消息
            const lastUserMessage = messages.value
              .filter(m => m.conversationId === currentConversation.value?.id && m.type === 'user')
              .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())[0]
            
            if (lastUserMessage) {
              currentConversation.value!.lastMessage = lastUserMessage.content
              currentConversation.value!.lastMessageAt = lastUserMessage.timestamp
            }
            currentConversation.value!.messageCount = messages.value.filter(
              m => m.conversationId === currentConversation.value?.id
            ).length
            currentConversation.value!.updatedAt = aiMessage.timestamp
            saveConversationsToStorage(conversations.value)
          }
        )

        console.log('AI回复已接收:', aiMessage.content)
        return aiMessage
      } catch (apiError) {
        console.error('流式API调用失败:', apiError)
        aiMessage.content = '抱歉，无法获取回复。'
        aiMessage.status = 'error'
        aiMessage.updatedAt = new Date().toISOString()
        saveMessagesToStorage(messages.value)
        return aiMessage
      }
    } catch (err) {
      console.error('发送流式消息失败:', err)
      error.value = err instanceof Error ? err.message : '发送消息失败'
      return null
    } finally {
      isLoading.value = false
      isTyping.value = false
    }
  }

  /**
   * 发送模拟消息
   */
  const sendMockMessage = async (userContent: string): Promise<Message | null> => {
    if (!currentConversation.value) return null

    try {
      // 模拟API延迟
      await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000))

      // 生成专业的医疗AI回复
      const mockContent = `作为医疗AI助手，我理解您的问题："${userContent}"。请注意，我不能提供具体的医疗诊断或治疗建议。如果您有健康问题，请咨询专业医生。`

      // 创建AI回复消息
      const aiMessage: Message = {
        id: generateUUID(),
        conversationId: currentConversation.value.id,
        type: 'assistant',
        contentType: 'text',
        content: mockContent,
        timestamp: new Date().toISOString(),
        status: 'sent',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      }

      // 添加AI消息到列表
      messages.value.push(aiMessage)
      saveMessagesToStorage(messages.value)

      // 更新对话信息
      const existingUserMessages = messages.value.filter(
        m => m.conversationId === currentConversation.value?.id && m.type === 'user'
      ).length

      if (
        existingUserMessages === 1 &&
        (currentConversation.value.title === '新对话' ||
          currentConversation.value.title === '未命名对话')
      ) {
        const sentMessage = messages.value.find(
          m => m.conversationId === currentConversation.value?.id && m.type === 'user'
        )
        if (sentMessage) {
          currentConversation.value.title =
            sentMessage.content.length > 20
              ? sentMessage.content.substring(0, 20) + '...'
              : sentMessage.content
        }
      }

      // 更新对话信息 - 保持显示用户最后一条消息
      const lastUserMessage = messages.value
        .filter(m => m.conversationId === currentConversation.value?.id && m.type === 'user')
        .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())[0]
      
      if (lastUserMessage) {
        currentConversation.value.lastMessage = lastUserMessage.content
        currentConversation.value.lastMessageAt = lastUserMessage.timestamp
      }
      currentConversation.value.messageCount = messages.value.filter(
        m => m.conversationId === currentConversation.value?.id
      ).length
      currentConversation.value.updatedAt = aiMessage.timestamp

      // 保存对话更新
      saveConversationsToStorage(conversations.value)

      console.log('模拟AI回复已生成')
      return aiMessage
    } catch (err) {
      console.error('生成模拟回复失败:', err)
      return null
    }
  }

  /**
   * 重新发送消息
   */
  const resendMessage = async (messageId: string) => {
    const message = messages.value.find(m => m.id === messageId)
    if (message && message.type === 'user') {
      // 删除原消息
      messages.value = messages.value.filter(m => m.id !== messageId)
      // 重新发送
      await sendMessage({ content: message.content })
    }
  }

  /**
   * 删除消息
   */
  const deleteMessage = async (messageId: string) => {
    messages.value = messages.value.filter(m => m.id !== messageId)
    saveMessagesToStorage(messages.value)

    // 更新对话的消息计数
    if (currentConversation.value) {
      currentConversation.value.messageCount = messages.value.filter(
        m => m.conversationId === currentConversation.value?.id
      ).length
      saveConversationsToStorage(conversations.value)
    }
  }

  // ==================== 实时通信方法 ====================

  /**
   * 设置正在输入状态
   */
  const setTyping = (typing: boolean) => {
    isTyping.value = typing
  }

  /**
   * 清除错误
   */
  const clearError = () => {
    error.value = null
  }

  // ==================== 调试和测试方法 ====================

  /**
   * 获取对话消息
   */
  const getConversationMessages = (conversationId: string): Message[] => {
    return messages.value
      .filter(msg => msg.conversationId === conversationId)
      .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
  }

  /**
   * 调试存储数据
   */
  const debugStorage = () => {
    console.log('=== 调试存储数据 ===')
    const authStore = useAuthStore()
    const userId = authStore.currentUser?.id || authStore.user?.id || 'guest'
    const conversationsKey = getUserStorageKey(STORAGE_KEYS.CHAT_HISTORY, userId)
    const messagesKey = getUserStorageKey(STORAGE_KEYS.CHAT_MESSAGES, userId)
    const storedConversations = localStorage.getItem(conversationsKey)
    const storedMessages = localStorage.getItem(messagesKey)

    console.log('用户ID:', userId)
    console.log('对话存储键:', conversationsKey)
    console.log('消息存储键:', messagesKey)
    console.log('存储的对话数据:', storedConversations ? JSON.parse(storedConversations) : '无数据')
    console.log('存储的消息数据:', storedMessages ? JSON.parse(storedMessages) : '无数据')
    console.log('当前内存中的对话:', conversations.value)
    console.log('当前内存中的消息:', messages.value)
    console.log('当前对话:', currentConversation.value)
  }

  /**
   * 清空存储数据
   */
  const clearStorage = () => {
    const authStore = useAuthStore()
    const userId = authStore.currentUser?.id || authStore.user?.id || 'guest'
    const conversationsKey = getUserStorageKey(STORAGE_KEYS.CHAT_HISTORY, userId)
    const messagesKey = getUserStorageKey(STORAGE_KEYS.CHAT_MESSAGES, userId)
    localStorage.removeItem(conversationsKey)
    localStorage.removeItem(messagesKey)
    conversations.value = []
    messages.value = []
    currentConversation.value = null
    console.log('已清空所有存储数据')
  }

  /**
   * 测试创建对话
   */
  const testCreateConversation = async () => {
    console.log('=== 测试创建对话 ===')
    const conversation = await createConversation({
      title: '测试对话 - ' + new Date().toLocaleTimeString(),
      type: 'general',
    })
    if (conversation) {
      console.log('测试对话创建成功:', conversation)
      return conversation
    } else {
      console.log('测试对话创建失败')
      return null
    }
  }

  /**
   * 测试发送消息
   */
  const testSendMessage = async (content?: string) => {
    if (!currentConversation.value) {
      console.log('没有当前对话，先创建一个测试对话')
      await testCreateConversation()
    }

    if (currentConversation.value) {
      console.log('=== 测试发送消息 ===')
      const testContent = content || '这是一条测试消息 - ' + new Date().toLocaleTimeString()
      const message = await sendMessage({ content: testContent })
      if (message) {
        console.log('测试消息发送成功:', message)
        return message
      } else {
        console.log('测试消息发送失败')
        return null
      }
    }
  }

  /**
   * 更新消息数据
   */
  const updateMessage = (messageId: string, updates: Partial<Message>) => {
    const messageIndex = messages.value.findIndex(msg => msg.id === messageId)
    if (messageIndex !== -1) {
      messages.value[messageIndex] = {
        ...messages.value[messageIndex],
        ...updates,
        updatedAt: new Date().toISOString()
      }
      saveMessagesToStorage(messages.value)
      console.log('消息已更新:', messageId, updates)
    } else {
      console.warn('未找到要更新的消息:', messageId)
    }
  }

  // ==================== 返回Store接口 ====================

  return {
    // 状态
    conversations,
    currentConversation,
    messages,
    currentMessages,
    sortedConversations,
    isLoading,
    isTyping,
    error,

    // 初始化方法
    initializeUserData,
    clearUserData,
    syncConversationMessages,

    // 对话管理
    createConversation,
    selectConversation,
    deleteConversation,
    updateConversationTitle,

    // 消息管理
    sendMessage,
    sendMessageStream,
    sendMockMessage,
    resendMessage,
    deleteMessage,
    getConversationMessages,
    updateMessage,

    // 实时通信
    setTyping,
    clearError,

    // 调试和测试
    debugStorage,
    clearStorage,
    testCreateConversation,
    testSendMessage,
  }
})
