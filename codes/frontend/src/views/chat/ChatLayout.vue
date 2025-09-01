<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { UserOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '../../stores/auth'
import { useUIStore } from '../../stores/ui'

const router = useRouter()
const authStore = useAuthStore()
const uiStore = useUIStore()

const isDarkTheme = computed(() => uiStore.isDarkTheme)

const toggleTheme = () => {
  uiStore.toggleTheme()
}

const handleLogout = async() => {
  try {
    await authStore.logout()
    message.success('已退出登录')
    router.push('/auth/login')
  } catch (error: any) {
    message.error('退出登录失败')
  }
}
</script>

<template>
  <div class="chat-layout">
    <div class="chat-header">
      <div class="chat-header-left">
        <h1 class="chat-title">智诊通</h1>
        <p class="chat-subtitle">多模态智能医生问诊系统</p>
      </div>
      <div class="chat-header-right">
        <a-button @click="toggleTheme">
          {{ isDarkTheme ? '🌞 浅色' : '🌙 深色' }}
        </a-button>
        <a-dropdown>
          <a-button>
            <UserOutlined />
            {{ authStore.currentUser?.username || '用户' }}
          </a-button>
          <template #overlay>
            <a-menu>
              <a-menu-item key="profile">
                <router-link to="/profile">个人档案</router-link>
              </a-menu-item>
              <a-menu-item key="settings">
                <router-link to="/settings">设置</router-link>
              </a-menu-item>
              <a-menu-divider />
              <a-menu-item key="logout" @click="handleLogout"> 退出登录 </a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
      </div>
    </div>

    <div class="chat-content">
      <router-view />
    </div>
  </div>
</template>

<style lang="less" scoped>
.chat-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: @spacing-md @spacing-lg;
  background: var(--header-bg);
  border-bottom: 1px solid var(--border-color);
  box-shadow: var(--box-shadow-sm);
}

.chat-header-left {
  .chat-title {
    font-size: @font-size-xl;
    font-weight: @font-weight-bold;
    color: var(--text-color);
    margin: 0 0 @spacing-xs 0;
  }

  .chat-subtitle {
    font-size: @font-size-sm;
    color: var(--text-color-secondary);
    margin: 0;
  }
}

.chat-header-right {
  display: flex;
  align-items: center;
  gap: @spacing-md;
}

.chat-content {
  flex: 1;
  overflow: hidden;
}
</style>
