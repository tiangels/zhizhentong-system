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

  // 对话列表
  const conversations = ref<Conversation[]>([])

  // 当前对话
  const currentConversation = ref<Conversation | null>(null)

  // 所有消息
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
   * 初始化用户数据
   */
  const initializeUserData = () => {
    const authStore = useAuthStore()
    console.log('Chat Store: 初始化用户数据')
    
    // 检查用户是否已认证
    if (!authStore.isAuthenticated) {
      console.log('Chat Store: 用户未认证，跳过初始化')
      return
    }
    
    // 加载用户专用的对话和消息数据
    const loadedConversations = loadConversationsFromStorage()
    const loadedMessages = loadMessagesFromStorage()
    
    // 确保始终是数组
    conversations.value = Array.isArray(loadedConversations) ? loadedConversations : []
    messages.value = Array.isArray(loadedMessages) ? loadedMessages : []
    
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
  const createConversation = async(request: CreateConversationRequest): Promise<Conversation | null> => {
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
        conversation_type: request.type || 'general'
      })
      
      const response = await conversationApi.createConversation({
        title: request.title || '新对话',
        conversation_type: request.type || 'general'
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
  const deleteConversation = async(conversationId: string) => {
    try {
      isLoading.value = true

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
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 更新对话标题
   */
  const updateConversationTitle = async(conversationId: string, title: string) => {
    const conversation = conversations.value.find(c => c.id === conversationId)
    if (conversation) {
      conversation.title = title
      conversation.updatedAt = new Date().toISOString()
      saveConversationsToStorage(conversations.value)
      console.log('更新对话标题:', title)
    }
  }

  // ==================== 消息管理方法 ====================

  /**
   * 发送消息 - 使用实际API
   */
  const sendMessage = async(request: SendMessageRequest): Promise<Message | null> => {
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
        contentType: 'text',
        content: request.content,
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
        m => m.conversationId === currentConversation.value?.id && m.type === 'user',
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
        m => m.conversationId === currentConversation.value?.id,
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

          // 更新对话信息
          currentConversation.value.lastMessage = aiMessage.content
          currentConversation.value.lastMessageAt = aiMessage.timestamp
          currentConversation.value.messageCount = messages.value.filter(
            m => m.conversationId === currentConversation.value?.id,
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
        const errorMessage = apiError instanceof Error ? apiError.message : 
                            typeof apiError === 'object' ? JSON.stringify(apiError) : 
                            String(apiError)
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
   * 发送模拟消息
   */
  const sendMockMessage = async(userContent: string): Promise<Message | null> => {
    if (!currentConversation.value) return null

    try {
      // 模拟API延迟
      await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000))

      // 生成模拟回复
      const mockReplies = [
        '我理解您的问题。让我为您详细分析一下...',
        '这是一个很好的问题。根据我的理解...',
        '感谢您的提问。我建议您可以考虑以下几个方面...',
        '基于您提供的信息，我认为...',
        '这个问题确实值得深入探讨。让我们从以下角度来看...',
      ]

      const randomReply = mockReplies[Math.floor(Math.random() * mockReplies.length)]
      const mockContent = `${randomReply}\n\n针对您提到的"${userContent.substring(0, 20)}${userContent.length > 20 ? '...' : ''}"，我的建议是：\n\n1. 首先需要明确具体需求\n2. 然后制定合适的方案\n3. 最后逐步实施和优化\n\n希望这个回答对您有帮助。如果您还有其他问题，请随时告诉我。`

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
        m => m.conversationId === currentConversation.value?.id && m.type === 'user',
      ).length

      if (
        existingUserMessages === 1 &&
        (currentConversation.value.title === '新对话' ||
          currentConversation.value.title === '未命名对话')
      ) {
        const sentMessage = messages.value.find(
          m => m.conversationId === currentConversation.value?.id && m.type === 'user',
        )
        if (sentMessage) {
          currentConversation.value.title =
            sentMessage.content.length > 20
              ? sentMessage.content.substring(0, 20) + '...'
              : sentMessage.content
        }
      }

      currentConversation.value.lastMessage = aiMessage.content
      currentConversation.value.lastMessageAt = aiMessage.timestamp
      currentConversation.value.messageCount = messages.value.filter(
        m => m.conversationId === currentConversation.value?.id,
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
  const resendMessage = async(messageId: string) => {
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
  const deleteMessage = async(messageId: string) => {
    messages.value = messages.value.filter(m => m.id !== messageId)
    saveMessagesToStorage(messages.value)

    // 更新对话的消息计数
    if (currentConversation.value) {
      currentConversation.value.messageCount = messages.value.filter(
        m => m.conversationId === currentConversation.value?.id,
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
  const testCreateConversation = async() => {
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
  const testSendMessage = async(content?: string) => {
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

    // 对话管理
    createConversation,
    selectConversation,
    deleteConversation,
    updateConversationTitle,

    // 消息管理
    sendMessage,
    sendMockMessage,
    resendMessage,
    deleteMessage,
    getConversationMessages,

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
