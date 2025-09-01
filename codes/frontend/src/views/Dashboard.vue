<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useChatStore } from '../stores/chat'
import type { Conversation } from '../types'

const router = useRouter()
const authStore = useAuthStore()
const chatStore = useChatStore()

// 统计数据
const chatStats = ref({
  totalChats: 0,
  thisMonth: 0,
  avgRating: 0,
})

const userStats = ref({
  daysActive: 0,
})

// 最近对话
const recentChats = ref<Conversation[]>([])

// 格式化时间
const formatTime = (timestamp: string) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) {
    return '今天'
  } else if (days === 1) {
    return '昨天'
  } else if (days < 7) {
    return `${days}天前`
  } else {
    return date.toLocaleDateString()
  }
}

// 格式化日期
const formatDate = (timestamp?: string) => {
  if (!timestamp) return '未知'
  return new Date(timestamp).toLocaleDateString()
}

// 开始新对话
const startNewChat = () => {
  router.push('/chat')
}

// 跳转到对话
const goToChat = (chatId: string) => {
  console.log('仪表盘：跳转到对话:', chatId)
  // 跳转到智能问诊页面，并加载指定对话
  router.push(`/chat/${chatId}`)
}

// 删除对话
const deleteChat = async(chatId: string) => {
  try {
    await chatStore.deleteConversation(chatId)
    // 重新加载最近对话
    loadRecentChats()
  } catch (error) {
    console.error('删除对话失败:', error)
  }
}

// 加载最近对话
const loadRecentChats = async() => {
  try {
    // 初始化用户数据，这会从本地存储加载对话
    chatStore.initializeUserData()
    
    // 使用 computed 属性获取已排序的对话
    const sortedConversations = chatStore.sortedConversations
    
    recentChats.value = sortedConversations.slice(0, 5) // 只显示最近5个
    console.log('仪表盘：加载最近对话:', recentChats.value.length, '个')
    console.log('对话列表:', recentChats.value.map(conv => ({
      id: conv.id,
      title: conv.title,
      type: conv.type,
      messageCount: conv.messageCount,
      updatedAt: conv.updatedAt
    })))
  } catch (error) {
    console.error('加载对话历史失败:', error)
  }
}

// 加载统计数据
const loadStats = async() => {
  try {
    // 这里可以调用API获取统计数据
    // 暂时使用模拟数据
    chatStats.value = {
      totalChats: 12,
      thisMonth: 3,
      avgRating: 4.8,
    }

    userStats.value = {
      daysActive: 15,
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

// 监听对话变化，自动更新最近对话列表
const unwatchConversations = watch(
  () => chatStore.conversations,
  (newConversations) => {
    console.log('仪表盘：检测到对话变化，新对话数:', newConversations.length)
    recentChats.value = newConversations.slice(0, 5)
  },
  { deep: true, immediate: true }
)

onMounted(async() => {
  await loadStats()
  await loadRecentChats()
})

onUnmounted(() => {
  unwatchConversations()
})
</script>

<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h1>仪表盘</h1>
      <p>欢迎回来，{{ authStore.user?.username }}！</p>
    </div>

    <div class="dashboard-stats">
      <div class="stat-card">
        <div class="stat-icon">
          <i class="fas fa-comments"></i>
        </div>
        <div class="stat-content">
          <h3>{{ chatStats.totalChats }}</h3>
          <p>总对话数</p>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">
          <i class="fas fa-clock"></i>
        </div>
        <div class="stat-content">
          <h3>{{ chatStats.thisMonth }}</h3>
          <p>本月对话</p>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">
          <i class="fas fa-star"></i>
        </div>
        <div class="stat-content">
          <h3>{{ chatStats.avgRating }}</h3>
          <p>平均评分</p>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">
          <i class="fas fa-calendar"></i>
        </div>
        <div class="stat-content">
          <h3>{{ userStats.daysActive }}</h3>
          <p>活跃天数</p>
        </div>
      </div>
    </div>

    <div class="dashboard-content">
      <div class="content-section">
        <h2>最近对话</h2>
        <div class="recent-chats">
          <div v-if="recentChats.length === 0" class="no-chats">
            <p>暂无对话记录</p>
            <button @click="startNewChat" class="btn btn-primary">开始新对话</button>
          </div>
          <div v-else class="chat-list">
            <div
              v-for="chat in recentChats"
              :key="chat.id"
              class="chat-item"
              @click="goToChat(chat.id)"
            >
              <div class="chat-info">
                <h4>{{ chat.title || '未命名对话' }}</h4>
                <p>{{ chat.lastMessage || '暂无消息' }}</p>
                <span class="chat-time">{{ formatTime(chat.updatedAt) }}</span>
                <span class="chat-type">{{ chat.type === 'diagnosis' ? '智能问诊' : '普通对话' }}</span>
              </div>
              <div class="chat-actions">
                <button @click.stop="deleteChat(chat.id)" class="btn-delete">
                  <i class="fas fa-trash"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="content-section">
        <h2>系统信息</h2>
        <div class="system-info">
          <div class="info-item">
            <span class="label">用户名：</span>
            <span class="value">{{ authStore.user?.username }}</span>
          </div>
          <div class="info-item">
            <span class="label">邮箱：</span>
            <span class="value">{{ authStore.user?.email || '未设置' }}</span>
          </div>
          <div class="info-item">
            <span class="label">注册时间：</span>
            <span class="value">{{ formatDate(authStore.user?.createdAt) }}</span>
          </div>
          <div class="info-item">
            <span class="label">最后登录：</span>
            <span class="value">{{ formatDate(authStore.user?.updatedAt) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="less">
.dashboard {
  padding: 24px;
}

.dashboard-header {
  margin-bottom: 32px;

  h1 {
    margin: 0 0 8px 0;
    font-size: 2rem;
    color: #333;
  }

  p {
    margin: 0;
    color: #666;
    font-size: 1.1rem;
  }
}

.dashboard-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.stat-card {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 16px;
  transition: transform 0.3s ease;

  &:hover {
    transform: translateY(-2px);
  }
}

.stat-icon {
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.5rem;
}

.stat-content h3 {
  margin: 0 0 4px 0;
  font-size: 2rem;
  color: #333;
}

.stat-content p {
  margin: 0;
  color: #666;
  font-size: 0.9rem;
}

.dashboard-content {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
}

.content-section {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

  h2 {
    margin: 0 0 20px 0;
    color: #333;
    font-size: 1.3rem;
  }
}

.recent-chats {
  .no-chats {
    text-align: center;
    padding: 40px 20px;
    color: #666;

    p {
      margin-bottom: 16px;
    }
  }
}

.chat-list {
  .chat-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px;
    border-bottom: 1px solid #f0f0f0;
    cursor: pointer;
    transition: background-color 0.3s;

    &:hover {
      background-color: #f9f9f9;
    }

    &:last-child {
      border-bottom: none;
    }
  }
}

.chat-info {
  flex: 1;

  h4 {
    margin: 0 0 4px 0;
    color: #333;
    font-size: 1rem;
  }

  p {
    margin: 0 0 4px 0;
    color: #666;
    font-size: 0.9rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 300px;
  }

  .chat-time {
    color: #999;
    font-size: 0.8rem;
    margin-right: 8px;
  }

  .chat-type {
    color: #1890ff;
    font-size: 0.75rem;
    background: #f0f8ff;
    padding: 2px 6px;
    border-radius: 10px;
    display: inline-block;
  }
}

.chat-actions {
  .btn-delete {
    background: none;
    border: none;
    color: #ff4d4f;
    cursor: pointer;
    padding: 8px;
    border-radius: 4px;
    transition: background-color 0.3s;

    &:hover {
      background-color: #fff1f0;
    }
  }
}

.system-info {
  .info-item {
    display: flex;
    justify-content: space-between;
    padding: 12px 0;
    border-bottom: 1px solid #f0f0f0;

    &:last-child {
      border-bottom: none;
    }

    .label {
      color: #666;
      font-weight: 500;
    }

    .value {
      color: #333;
    }
  }
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 0.9rem;
}

.btn-primary {
  background: #1890ff;
  color: white;

  &:hover {
    background: #40a9ff;
  }
}

// 响应式设计
@media (max-width: 768px) {
  .dashboard-content {
    grid-template-columns: 1fr;
  }

  .dashboard-stats {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  }
}
</style>
