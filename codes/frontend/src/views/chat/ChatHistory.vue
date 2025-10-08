<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import { useChatStore } from '../../stores/chat'
import { formatDateTime } from '../../utils/helpers'

const router = useRouter()
const chatStore = useChatStore()

// 分页相关
const currentPage = ref(1)
const pageSize = ref(10)
const showAll = ref(false)

// 重命名相关
const editingConversationId = ref<string | null>(null)
const editingTitle = ref('')
const titleInput = ref()
const isSaving = ref(false)

// 悬停状态
const hoveredTitleId = ref<string | null>(null)

// 调试悬停状态的计算属性
const debugHoverState = computed(() => {
  console.log('🔍 当前悬停状态:', hoveredTitleId.value)
  return hoveredTitleId.value
})

// 添加页面加载时的调试信息
onMounted(() => {
  console.log('🚀 ChatHistory 组件已挂载')
  console.log('🔍 初始悬停状态:', hoveredTitleId.value)
})

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
  } catch (error: unknown) {
    message.error('创建对话失败')
  }
}

const deleteConversation = async (conversationId: string) => {
  try {
    // 添加确认对话框
    const confirmed = await new Promise<boolean>(resolve => {
      Modal.confirm({
        title: '确认删除',
        content: '确定要删除这个对话吗？删除后无法恢复。',
        okText: '删除',
        cancelText: '取消',
        okType: 'danger',
        onOk: () => resolve(true),
        onCancel: () => resolve(false),
      })
    })

    if (!confirmed) return

    await chatStore.deleteConversation(conversationId)
    message.success('删除成功')
  } catch (error: unknown) {
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

// 生成智能标题建议
const generateSmartTitle = (conversationId: string) => {
  const conversation = chatStore.conversations.find(c => c.id === conversationId)
  if (!conversation || !conversation.lastMessage) {
    return '新对话'
  }

  const lastMessage = conversation.lastMessage
  // 简单的标题生成逻辑
  if (lastMessage.includes('症状') || lastMessage.includes('疼痛')) {
    return '症状咨询'
  } else if (lastMessage.includes('检查') || lastMessage.includes('报告')) {
    return '检查报告'
  } else if (lastMessage.includes('药物') || lastMessage.includes('用药')) {
    return '用药咨询'
  } else if (lastMessage.includes('CT') || lastMessage.includes('MRI')) {
    return '影像检查'
  } else {
    // 取前10个字符作为标题
    return lastMessage.length > 10 ? lastMessage.substring(0, 10) + '...' : lastMessage
  }
}

// 开始重命名
const startRename = (conversationId: string, currentTitle: string) => {
  editingConversationId.value = conversationId
  editingTitle.value = currentTitle
  // 等待DOM更新后聚焦输入框
  setTimeout(() => {
    if (titleInput.value) {
      titleInput.value.focus()
      titleInput.value.select()
    }
  }, 0)
}

// 使用智能标题
const useSmartTitle = () => {
  if (editingConversationId.value) {
    editingTitle.value = generateSmartTitle(editingConversationId.value)
  }
}

// 悬停事件处理
const handleMouseEnter = (event: MouseEvent) => {
  console.log('🖱️ Mouse enter event triggered!', event)
  const target = event.currentTarget as HTMLElement
  console.log('🎯 Target element:', target)
  console.log('🏷️ Target classes:', target.className)
  console.log('📋 Target attributes:', target.attributes)

  const conversationId = target.getAttribute('data-conversation-id')
  console.log('🆔 Conversation ID:', conversationId)

  if (conversationId) {
    hoveredTitleId.value = conversationId
    console.log('✅ Hovered title ID set to:', hoveredTitleId.value)
  } else {
    console.log('❌ No conversation ID found')
  }
}

const handleMouseLeave = (event: MouseEvent) => {
  console.log('🖱️ Mouse leave event triggered!', event)
  const target = event.currentTarget as HTMLElement
  const conversationId = target.getAttribute('data-conversation-id')
  console.log('🆔 Conversation ID:', conversationId)

  if (conversationId) {
    hoveredTitleId.value = null
    console.log('✅ Hovered title ID cleared')
  }
}

// 保存重命名
const saveRename = async () => {
  if (!editingConversationId.value || isSaving.value) {
    return
  }

  const trimmedTitle = editingTitle.value.trim()

  // 验证标题
  if (!trimmedTitle) {
    message.warning('标题不能为空')
    return
  }

  if (trimmedTitle.length > 50) {
    message.warning('标题不能超过50个字符')
    return
  }

  // 检查是否与当前标题相同
  const currentConversation = chatStore.conversations.find(
    c => c.id === editingConversationId.value
  )
  if (currentConversation && currentConversation.title === trimmedTitle) {
    cancelRename()
    return
  }

  isSaving.value = true
  try {
    await chatStore.updateConversationTitle(editingConversationId.value, trimmedTitle)
    message.success('重命名成功')
    editingConversationId.value = null
    editingTitle.value = ''
  } catch (error: unknown) {
    message.error('重命名失败，请稍后重试')
    console.error('重命名失败:', error)
  } finally {
    isSaving.value = false
  }
}

// 取消重命名
const cancelRename = () => {
  editingConversationId.value = null
  editingTitle.value = ''
}

onMounted(async () => {
  try {
    chatStore.initializeUserData()
    console.log('对话历史加载完成:', chatStore.conversations.length, '个对话')
    console.log('🔍 悬停状态初始化:', hoveredTitleId.value)
    console.log(
      '🔍 对话列表:',
      chatStore.conversations.map(c => ({ id: c.id, title: c.title }))
    )
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
        <a-button type="default" @click="toggleShowAll" :icon="showAll ? 'eye-invisible' : 'eye'">
          {{ showAll ? '显示最近' : '查看全部' }}
        </a-button>
        <a-button type="primary" @click="createNewChat"> 新建对话 </a-button>
        <!-- 调试按钮 -->
        <a-button
          type="dashed"
          size="small"
          @click="() => console.log('🧪 测试按钮点击成功！')"
          style="margin-left: 8px"
        >
          测试控制台
        </a-button>
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
                  <div v-if="editingConversationId === item.id" class="editing-title">
                    <a-input
                      v-model="editingTitle"
                      @press-enter="saveRename"
                      @blur="saveRename"
                      @keyup.escape="cancelRename"
                      :ref="el => (titleInput = el)"
                      size="small"
                      :maxlength="50"
                      :placeholder="'请输入对话标题'"
                      :loading="isSaving"
                      style="width: 200px"
                    />
                    <a-button
                      type="text"
                      size="small"
                      @click="useSmartTitle"
                      title="智能生成标题"
                      style="padding: 0 4px; min-width: auto"
                    >
                      🤖
                    </a-button>
                    <span class="char-count">{{ editingTitle.length }}/50</span>
                  </div>
                  <div
                    v-else
                    class="conversation-title-wrapper"
                    :data-conversation-id="item.id"
                    @click="startRename(item.id, item.title)"
                    @mouseenter="handleMouseEnter"
                    @mouseleave="handleMouseLeave"
                    :title="'点击重命名'"
                    style="
                      cursor: pointer;
                      padding: 4px 8px;
                      border-radius: 6px;
                      transition: all 0.2s ease;
                      display: inline-block;
                      position: relative;
                    "
                  >
                    <span class="conversation-title editable">
                      {{ item.title }}
                    </span>
                    <span
                      v-show="hoveredTitleId === item.id"
                      class="hover-icon"
                      style="
                        margin-left: 8px;
                        font-size: 12px;
                        opacity: 1;
                        transition: opacity 0.2s ease;
                      "
                    >
                      ✏️ ({{ hoveredTitleId }})
                    </span>
                    <!-- 调试信息 -->
                    <span
                      v-if="true"
                      style="
                        margin-left: 8px;
                        font-size: 10px;
                        color: #999;
                        background: #f0f0f0;
                        padding: 2px 4px;
                        border-radius: 3px;
                      "
                    >
                      DEBUG: hovered={{ hoveredTitleId }}, item={{ item.id }}, match={{
                        hoveredTitleId === item.id
                      }}
                    </span>
                  </div>
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
            :show-total="total => `共 ${total} 条对话`"
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

// 重命名相关样式
.editing-title {
  display: flex;
  align-items: center;
  gap: 8px;

  .char-count {
    font-size: 12px;
    color: var(--text-color-secondary, #999);
    white-space: nowrap;
  }
}

.conversation-title-wrapper {
  cursor: pointer !important;
  padding: 4px 8px;
  border-radius: 6px;
  transition: all 0.2s ease;
  position: relative;
  display: inline-block;

  &:hover {
    background-color: #f5f5f5 !important;

    .conversation-title {
      color: #1890ff !important;
    }
  }
}

.conversation-title.editable {
  transition: all 0.2s ease;
}

// 确保样式优先级
.ant-list-item-meta-title .conversation-title-wrapper {
  cursor: pointer !important;

  &:hover {
    background-color: #f5f5f5 !important;

    .conversation-title {
      color: #1890ff !important;
    }
  }
}
</style>
