<script setup lang="ts">
/**
 * Vue根组件
 * 应用的主入口组件
 */

import { onMounted } from 'vue'
import { useUIStore } from '@/stores/ui'
import { useAuthStore } from '@/stores/auth'

// 获取状态管理store
const uiStore = useUIStore()
const authStore = useAuthStore()

// 组件挂载时的初始化
onMounted(async () => {
  try {
    console.log('App.vue - 开始初始化应用')

    // 初始化主题
    uiStore.initTheme()

    // 检查认证状态
    console.log('App.vue - 检查认证状态')
    await authStore.checkAuthStatus()

    console.log('App.vue - 应用初始化完成')
  } catch (error) {
    console.error('应用初始化失败:', error)
  }
})
</script>

<template>
  <div id="app">
    <router-view />
  </div>
</template>

<style lang="less">
#app {
  width: 100%;
  height: 100vh;
  font-family: @font-family;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
</style>
