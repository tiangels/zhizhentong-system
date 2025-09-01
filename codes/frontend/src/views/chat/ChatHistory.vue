<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { useChatStore } from '../../stores/chat'
import { formatDateTime } from '../../utils/helpers'

const router = useRouter()
const chatStore = useChatStore()

// 分页相关
const currentPage = ref(1)
const pageSize = ref(10)
const showAll = ref(false)

const formatTime = (timestamp: string | Date | null) => {
  if (!timestamp) return ''
  const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp
  return formatDateTime(date, 'MM-DD HH:mm')
}

// 计算显示的对话列表
const displayedConversations = computed(() => {
  const conversations = chatStore.conversations
  if (showAll.value) {
    // 显示全部，按分页
    const start = (currentPage.value - 1) * pageSize.value
    const end = start + pageSize.value
    return conversations.slice(start, end)
  } else {
    // 只显示最近5条
    return conversations.slice(0, 5)
  }
})

// 总数
const totalConversations = computed(() => chatStore.conversations.length)

const selectConversation = (conversationId: string) => {
  chatStore.selectConversation(conversationId)
  router.push(`/chat/${conversationId}`)
}

const createNewChat = async () => {
  try {
    await chatStore.createConversation({
      title: '新对话',
      type: 'general',
    })
    router.push('/chat')
  } catch (error: any) {
    message.error('创建对话失败')
  }
}

const deleteConversation = async (conversationId: string) => {
  try {
    await chatStore.deleteConversation(conversationId)
    message.success('删除成功')
  } catch (error: any) {
    message.error('删除失败')
  }
}

// 切换显示模式
const toggleShowAll = () => {
  showAll.value = !showAll.value
  currentPage.value = 1 // 重置到第一页
}

// 分页改变
const onPageChange = (page: number) => {
  currentPage.value = page
}

onMounted(async () => {
  try {
    chatStore.initializeUserData()
    console.log('对话历史加载完成:', chatStore.conversations.length, '个对话')
  } catch (error) {
    console.error('加载对话历史失败:', error)
  }
})
</script>

<template>
  <div class="chat-history">
    <div class="history-header">
      <h2>{{ showAll ? '全部对话历史' : '最近对话' }}</h2>
      <div class="header-actions">
        <a-button 
          type="default" 
          @click="toggleShowAll"
          :icon="showAll ? 'eye-invisible' : 'eye'"
        >
          {{ showAll ? '显示最近' : '查看全部' }}
        </a-button>
        <a-button type="primary" @click="createNewChat"> 新建对话 </a-button>
      </div>
    </div>

    <div class="history-list">
      <div
        v-if="chatStore.conversations.length === 0 && !chatStore.isLoading"
        class="empty-history"
      >
        <p>暂无对话历史</p>
        <p>开始您的第一次对话吧！</p>
      </div>

      <div v-else>
        <a-list
          :data-source="displayedConversations"
          :loading="chatStore.isLoading"
          item-layout="horizontal"
        >
          <template #renderItem="{ item }">
            <a-list-item
              :class="{ active: item.id === chatStore.currentConversation?.id }"
              @click="selectConversation(item.id)"
            >
              <a-list-item-meta>
                <template #title>
                  <span class="conversation-title">{{ item.title }}</span>
                </template>
                <template #description>
                  <span class="conversation-preview">{{ item.lastMessage || '暂无消息' }}</span>
                  <span class="conversation-time">{{ formatTime(item.lastMessageAt) }}</span>
                </template>
              </a-list-item-meta>
              <template #actions>
                <a-button type="text" size="small" @click.stop="deleteConversation(item.id)">
                  删除
                </a-button>
              </template>
            </a-list-item>
          </template>
        </a-list>

        <!-- 分页器 - 只在显示全部时显示 -->
        <div v-if="showAll && totalConversations > pageSize" class="pagination-wrapper">
          <a-pagination
            :current="currentPage"
            :total="totalConversations"
            :page-size="pageSize"
            :show-size-changer="false"
            :show-quick-jumper="true"
            :show-total="(total: number) => `共 ${total} 条对话`"
            @change="onPageChange"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="less" scoped>
.chat-history {
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-color-light);
}

.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: @spacing-lg;
  border-bottom: 1px solid var(--border-color);

  h2 {
    margin: 0;
    font-size: @font-size-xl;
    font-weight: @font-weight-semibold;
    color: var(--text-color);
  }

  .header-actions {
    display: flex;
    gap: @spacing-sm;
  }
}

.history-list {
  flex: 1;
  overflow-y: auto;
}

.conversation-title {
  font-weight: @font-weight-medium;
  color: var(--text-color);
}

.conversation-preview {
  color: var(--text-color-secondary);
  font-size: @font-size-sm;
  display: block;
  margin-bottom: @spacing-xs;
}

.conversation-time {
  color: var(--text-color-secondary);
  font-size: @font-size-xs;
}

.active {
  background: @primary-color-light;

  .conversation-title {
    color: @primary-color;
  }
}

.empty-history {
  text-align: center;
  padding: @spacing-xl;
  color: var(--text-color-secondary);

  p {
    margin: @spacing-sm 0;
    font-size: @font-size-base;
  }
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  padding: @spacing-lg;
  border-top: 1px solid var(--border-color);
  background-color: var(--bg-color);
}
</style>
