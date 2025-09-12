<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// 侧边栏状态
const sidebarCollapsed = ref(false)

// 导航菜单项
const navItems = computed(() => {
  const items = [
    { path: '/dashboard', title: '仪表盘', icon: 'fas fa-tachometer-alt' },
    { path: '/chat', title: '智能问诊', icon: 'fas fa-comments' },
    { path: '/profile', title: '个人资料', icon: 'fas fa-user' },
    { path: '/settings', title: '系统设置', icon: 'fas fa-cog' },
  ]

  // 如果用户未登录，只显示登录页面
  if (!authStore.isLoggedIn) {
    return []
  }

  return items
})

// 切换侧边栏
const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

// 跳转到登录页
const goToLogin = () => {
  router.push('/auth/login')
}

// 退出登录
const logout = async () => {
  try {
    await authStore.logout()
    router.push('/')
  } catch (error) {
    console.error('退出登录失败:', error)
  }
}
</script>

<template>
  <div class="main-layout">
    <!-- 顶部导航栏 -->
    <header class="header">
      <div class="header-left">
        <div class="logo">
          <h2>智诊通系统</h2>
        </div>
      </div>

      <div class="header-right">
        <div class="user-info" v-if="authStore.isLoggedIn">
          <span class="username">{{ authStore.user?.username }}</span>
          <button @click="logout" class="logout-btn">退出</button>
        </div>
        <div v-else>
          <button @click="goToLogin" class="login-btn">登录</button>
        </div>
      </div>
    </header>

    <!-- 侧边栏 -->
    <aside class="sidebar" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
      <nav class="sidebar-nav">
        <ul class="nav-list">
          <li class="nav-item" v-for="item in navItems" :key="item.path">
            <router-link
              :to="item.path"
              class="nav-link"
              :class="{ active: $route.path === item.path }"
            >
              <i :class="item.icon" class="nav-icon"></i>
              <span class="nav-text" v-show="!sidebarCollapsed">{{ item.title }}</span>
            </router-link>
          </li>
        </ul>
      </nav>

      <div class="sidebar-toggle" @click="toggleSidebar">
        <i :class="sidebarCollapsed ? 'fas fa-chevron-right' : 'fas fa-chevron-left'"></i>
      </div>
    </aside>

    <!-- 主内容区域 -->
    <main class="main-content" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
      <div class="content-wrapper">
        <router-view />
      </div>
    </main>
  </div>
</template>

<style scoped lang="less">
.main-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f5f5f5;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  height: 64px;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 1000;
}

.header-left .logo h2 {
  margin: 0;
  color: #1890ff;
  font-size: 1.5rem;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.username {
  font-weight: 500;
  color: #333;
}

.logout-btn,
.login-btn {
  padding: 8px 16px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  background: white;
  color: #333;
  cursor: pointer;
  transition: all 0.3s;
}

.logout-btn:hover,
.login-btn:hover {
  border-color: #1890ff;
  color: #1890ff;
}

.sidebar {
  position: fixed;
  left: 0;
  top: 64px;
  width: 240px;
  height: calc(100vh - 64px);
  background: white;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  z-index: 999;
}

.sidebar-collapsed {
  width: 80px;
}

.sidebar-nav {
  padding: 24px 0;
}

.nav-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.nav-item {
  margin: 0;
}

.nav-link {
  display: flex;
  align-items: center;
  padding: 12px 24px;
  color: #666;
  text-decoration: none;
  transition: all 0.3s;
  gap: 12px;
}

.nav-link:hover {
  background-color: #f0f0f0;
  color: #1890ff;
}

.nav-link.active {
  background-color: #e6f7ff;
  color: #1890ff;
  border-right: 3px solid #1890ff;
}

.nav-icon {
  width: 16px;
  text-align: center;
}

.nav-text {
  white-space: nowrap;
  overflow: hidden;
}

.sidebar-toggle {
  position: absolute;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  width: 32px;
  height: 32px;
  background: #f0f0f0;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
}

.sidebar-toggle:hover {
  background: #e0e0e0;
}

.main-content {
  margin-left: 240px;
  margin-top: 64px;
  flex: 1;
  transition: all 0.3s ease;
}

.main-content.sidebar-collapsed {
  margin-left: 80px;
}

.content-wrapper {
  padding: 24px;
  min-height: calc(100vh - 64px);
}

// 响应式设计
@media (max-width: 768px) {
  .sidebar {
    transform: translateX(-100%);
  }

  .sidebar.mobile-open {
    transform: translateX(0);
  }

  .main-content {
    margin-left: 0;
  }

  .main-content.sidebar-collapsed {
    margin-left: 0;
  }
}
</style>
