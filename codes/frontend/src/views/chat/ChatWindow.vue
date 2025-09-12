<script setup lang="ts">
import { ref, nextTick, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useChatStore } from '../../stores/chat'
import { useAuthStore } from '../../stores/auth'

// 接收路由参数
interface Props {
  id?: string
}

const props = defineProps<Props>()

const route = useRoute()
const chatStore = useChatStore()
const authStore = useAuthStore()

// 输入消息
const inputMessage = ref('')
const messagesContainer = ref<HTMLElement>()

// 快速操作按钮
const quickActions = [
  { id: 1, text: '我最近总是头痛' },
  { id: 2, text: '我感冒了，有什么建议？' },
  { id: 3, text: '我睡眠质量不好' },
  { id: 4, text: '我想了解健康饮食' },
]

// 发送消息
const sendMessage = async () => {
  if (!inputMessage.value.trim() || chatStore.isLoading) return

  // 检查用户是否已登录
  if (!authStore.isLoggedIn) {
    console.error('用户未登录，无法发送消息')
    return
  }

  const message = inputMessage.value.trim()
  inputMessage.value = ''

  try {
    // 如果没有当前对话，先创建一个新对话
    if (!chatStore.currentConversation) {
      console.log('创建新对话用于发送消息')
      await chatStore.createConversation({
        title: '新对话',
        type: 'diagnosis',
      })
    }

    // 确保有当前对话
    if (!chatStore.currentConversation) {
      console.error('创建对话失败，无法发送消息')
      return
    }

    await chatStore.sendMessageStream({
      content: message,
      type: 'user',
      conversationId: chatStore.currentConversation.id,
    })

    // 滚动到底部
    await nextTick()
    scrollToBottom()
  } catch (error) {
    console.error('发送消息失败:', error)
  }
}

// 发送快速消息
const sendQuickMessage = async (text: string) => {
  inputMessage.value = text
  await sendMessage()
}

// 开始新对话
const startNewConversation = async () => {
  try {
    console.log('开始新对话')

    // 如果当前有对话且有消息，确保它被保存到历史中
    if (chatStore.currentConversation && chatStore.currentMessages.length > 0) {
      console.log('保存当前对话到历史:', chatStore.currentConversation.id)
      // 当前对话会在创建新对话时自动保存到conversations列表中
    }

    await chatStore.createConversation({
      title: '新对话',
      type: 'diagnosis',
    })

    // 清空输入框
    inputMessage.value = ''

    // 滚动到底部
    await nextTick()
    scrollToBottom()
  } catch (error) {
    console.error('创建新对话失败:', error)
  }
}

// 处理回车键
const handleEnterKey = (event: KeyboardEvent) => {
  if (event.shiftKey) {
    // Shift + Enter 换行
    return
  }
  // Enter 发送
  sendMessage()
}

// 滚动到底部
const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 格式化时间
const formatTime = (timestamp: string) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  })
}

// 监听消息变化，自动滚动
watch(
  () => chatStore.currentMessages,
  () => {
    nextTick(() => {
      scrollToBottom()
    })
  },
  { deep: true }
)

onMounted(async () => {
  console.log('ChatWindow mounted, route params:', route.params, 'props:', props)

  // 确保用户已登录并且 chat store 已初始化
  if (!authStore.isAuthenticated) {
    console.log('用户未登录，无法加载对话')
    return
  }

  // 确保 chat store 用户数据已初始化
  if (chatStore.conversations.length === 0 && chatStore.messages.length === 0) {
    console.log('Chat store 数据未初始化，重新初始化用户数据')
    chatStore.initializeUserData()
  }

  // 如果有路由参数ID，加载指定对话
  const conversationId = props.id || (route.params.id as string)

  if (conversationId && conversationId !== 'new') {
    try {
      console.log('Loading conversation:', conversationId)
      await chatStore.selectConversation(conversationId)
    } catch (error) {
      console.error('加载对话失败:', error)
      // 如果加载失败，清空当前对话，等待用户发送第一条消息时创建
      chatStore.currentConversation = null
    }
  } else {
    // 智能问诊页面：检查本地存储的对话历史
    console.log('智能问诊页面：检查本地对话历史')

    // 首先检查本地是否有智能问诊对话和消息
    const localDiagnosisConversations = chatStore.conversations.filter(
      conv => conv.type === 'diagnosis' && conv.messageCount > 0
    )

    const localMessages = chatStore.messages.filter((msg: any) =>
      localDiagnosisConversations.some((conv: any) => conv.id === msg.conversationId)
    )

    console.log(
      '本地智能问诊对话数:',
      localDiagnosisConversations.length,
      '本地消息数:',
      localMessages.length
    )

    if (localDiagnosisConversations.length > 0 && localMessages.length > 0) {
      // 有本地对话和消息，直接使用本地数据
      const latestConversation = localDiagnosisConversations[0]
      console.log(
        '使用本地对话历史:',
        latestConversation.id,
        '消息数:',
        localMessages.filter((m: any) => m.conversationId === latestConversation.id).length
      )
      chatStore.currentConversation = latestConversation
    } else if (!chatStore.currentConversation) {
      // 没有本地数据，尝试从API加载
      try {
        console.log('没有本地对话历史，从API加载智能问诊对话历史')
        // 专门获取智能问诊类型的对话
        chatStore.initializeUserData()

        // 查找有消息的智能问诊对话
        const diagnosisConversations = chatStore.conversations.filter(
          conv => conv.type === 'diagnosis' && conv.messageCount > 0
        )

        if (diagnosisConversations.length > 0) {
          // 选择最近的智能问诊对话
          const latestConversation = diagnosisConversations[0]
          console.log(
            '从API找到最近的智能问诊对话:',
            latestConversation.id,
            '消息数:',
            latestConversation.messageCount
          )
          await chatStore.selectConversation(latestConversation.id)
        } else {
          console.log('没有智能问诊历史对话，等待用户创建')
        }
      } catch (error) {
        console.error('加载智能问诊对话历史失败:', error)
      }
    } else {
      console.log('智能问诊页面：已有当前对话，保持现有状态', chatStore.currentConversation.id)
    }
  }

  // 滚动到底部
  await nextTick()
  scrollToBottom()
})
</script>

<template>
  <div class="chat-window">
    <div class="chat-header">
      <div class="chat-header-left">
        <h2>智能问诊</h2>
        <p>请描述您的症状，AI医生将为您提供专业的医疗建议</p>
      </div>
      <div class="chat-header-right">
        <button @click="startNewConversation" class="new-chat-btn">
          <i class="fas fa-plus"></i>
          新对话
        </button>
      </div>
    </div>

    <div class="chat-container">
      <!-- 消息列表 -->
      <div class="messages-container" ref="messagesContainer">
        <div v-if="chatStore.currentMessages.length === 0" class="welcome-message">
          <div class="welcome-icon">
            <i class="fas fa-user-md"></i>
          </div>
          <h3>欢迎使用智诊通</h3>
          <p>我是您的AI医生助手，请告诉我您的症状或健康问题</p>
          <div class="quick-actions">
            <button
              v-for="action in quickActions"
              :key="action.id"
              @click="sendQuickMessage(action.text)"
              class="quick-action-btn"
            >
              {{ action.text }}
            </button>
          </div>
        </div>

        <div
          v-for="message in chatStore.currentMessages"
          :key="message.id"
          class="message"
          :class="{
            'user-message': message.type === 'user',
            'ai-message': message.type === 'assistant',
          }"
        >
          <div class="message-avatar">
            <i :class="message.type === 'user' ? 'fas fa-user' : 'fas fa-robot'"></i>
          </div>
          <div class="message-content">
            <div class="message-text">{{ message.content }}</div>
            <div class="message-time">{{ formatTime(message.timestamp) }}</div>
          </div>
        </div>

        <!-- 正在输入指示器 -->
        <div v-if="chatStore.isTyping" class="message ai-message">
          <div class="message-avatar">
            <i class="fas fa-robot"></i>
          </div>
          <div class="message-content">
            <div class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="input-container">
        <div class="input-wrapper">
          <textarea
            v-model="inputMessage"
            @keydown.enter.prevent="handleEnterKey"
            placeholder="请描述您的症状或健康问题..."
            class="message-input"
            rows="3"
            maxlength="1000"
          ></textarea>
          <div class="input-actions">
            <button
              @click="sendMessage"
              :disabled="!inputMessage.trim() || chatStore.isLoading"
              class="send-btn"
            >
              <i class="fas fa-paper-plane"></i>
              发送
            </button>
          </div>
        </div>

        <div class="input-tips">
          <span>按 Enter 发送，Shift + Enter 换行</span>
          <span class="char-count">{{ inputMessage.length }}/1000</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="less">
.chat-window {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
}

.chat-header {
  padding: 24px;
  background: white;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;

  .chat-header-left {
    flex: 1;

    h2 {
      margin: 0 0 8px 0;
      color: #333;
      font-size: 1.5rem;
    }

    p {
      margin: 0;
      color: #666;
      font-size: 0.9rem;
    }
  }

  .chat-header-right {
    .new-chat-btn {
      padding: 8px 16px;
      background: #1890ff;
      color: white;
      border: none;
      border-radius: 6px;
      cursor: pointer;
      font-size: 0.9rem;
      transition: all 0.3s;
      display: flex;
      align-items: center;
      gap: 6px;

      &:hover {
        background: #40a9ff;
        transform: translateY(-1px);
      }

      &:active {
        transform: translateY(0);
      }

      i {
        font-size: 0.8rem;
      }
    }
  }
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.welcome-message {
  text-align: center;
  padding: 40px 20px;
  color: #666;

  .welcome-icon {
    width: 80px;
    height: 80px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 20px;
    color: white;
    font-size: 2rem;
  }

  h3 {
    margin: 0 0 12px 0;
    color: #333;
    font-size: 1.3rem;
  }

  p {
    margin: 0 0 24px 0;
    color: #666;
    line-height: 1.5;
  }
}

.quick-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;

  .quick-action-btn {
    padding: 8px 16px;
    border: 1px solid #d9d9d9;
    border-radius: 20px;
    background: white;
    color: #666;
    cursor: pointer;
    transition: all 0.3s;
    font-size: 0.9rem;

    &:hover {
      border-color: #1890ff;
      color: #1890ff;
      background: #f0f8ff;
    }
  }
}

.message {
  display: flex;
  gap: 12px;
  max-width: 80%;

  &.user-message {
    align-self: flex-end;
    flex-direction: row-reverse;

    .message-content {
      background: #1890ff;
      color: white;
      border-radius: 18px 18px 4px 18px;
    }
  }

  &.ai-message {
    align-self: flex-start;

    .message-content {
      background: white;
      color: #333;
      border-radius: 18px 18px 18px 4px;
      border: 1px solid #f0f0f0;
    }
  }
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f0f0;
  color: #666;
  font-size: 1.2rem;
  flex-shrink: 0;
}

.message-content {
  padding: 12px 16px;
  max-width: 100%;

  .message-text {
    line-height: 1.5;
    word-wrap: break-word;
  }

  .message-time {
    font-size: 0.8rem;
    color: #999;
    margin-top: 4px;
  }
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 8px 0;

  span {
    width: 8px;
    height: 8px;
    background: #999;
    border-radius: 50%;
    animation: typing 1.4s infinite ease-in-out;

    &:nth-child(1) {
      animation-delay: -0.32s;
    }
    &:nth-child(2) {
      animation-delay: -0.16s;
    }
  }
}

@keyframes typing {
  0%,
  80%,
  100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.input-container {
  padding: 24px;
  background: white;
  border-top: 1px solid #f0f0f0;
}

.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.message-input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #d9d9d9;
  border-radius: 8px;
  resize: none;
  font-family: inherit;
  font-size: 0.9rem;
  line-height: 1.5;
  transition: border-color 0.3s;

  &:focus {
    outline: none;
    border-color: #1890ff;
  }

  &::placeholder {
    color: #999;
  }
}

.input-actions {
  .send-btn {
    padding: 12px 20px;
    background: #1890ff;
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.9rem;
    transition: background-color 0.3s;
    display: flex;
    align-items: center;
    gap: 8px;

    &:hover:not(:disabled) {
      background: #40a9ff;
    }

    &:disabled {
      background: #d9d9d9;
      cursor: not-allowed;
    }
  }
}

.input-tips {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 0.8rem;
  color: #999;

  .char-count {
    color: #666;
  }
}

// 响应式设计
@media (max-width: 768px) {
  .chat-header {
    padding: 16px;

    h2 {
      font-size: 1.3rem;
    }
  }

  .messages-container {
    padding: 16px;
  }

  .input-container {
    padding: 16px;
  }

  .message {
    max-width: 90%;
  }
}
</style>
