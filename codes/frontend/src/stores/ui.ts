/**
 * UI状态管理Store
 * 管理主题、侧边栏、模态框、通知等UI状态
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Notification } from '@/types'
import { setLocalStorage, getLocalStorage } from '@/utils/helpers'
import { STORAGE_KEYS } from '@/utils/constants'

export const useUIStore = defineStore('ui', () => {
  // 状态
  const theme = ref<'light' | 'dark'>(
    getLocalStorage<'light' | 'dark'>(STORAGE_KEYS.THEME) || 'light'
  )
  const sidebarCollapsed = ref<boolean>(
    getLocalStorage<boolean>(STORAGE_KEYS.SIDEBAR_COLLAPSED) || false
  )
  const modalVisible = ref<boolean>(false)
  const modalType = ref<string | null>(null)
  const modalData = ref<any>(null)
  const notifications = ref<Notification[]>([])
  const loadingStates = ref<Record<string, boolean>>({})
  const errorStates = ref<Record<string, string | null>>({})

  // 计算属性
  const isDarkTheme = computed(() => theme.value === 'dark')
  const isSidebarCollapsed = computed(() => sidebarCollapsed.value)
  const hasNotifications = computed(() => notifications.value.length > 0)
  const isLoading = computed(() => Object.values(loadingStates.value).some(Boolean))

  // 切换主题
  const toggleTheme = () => {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
    setLocalStorage(STORAGE_KEYS.THEME, theme.value)

    // 应用主题到DOM
    document.documentElement.setAttribute('data-theme', theme.value)
  }

  // 设置主题
  const setTheme = (newTheme: 'light' | 'dark') => {
    theme.value = newTheme
    setLocalStorage(STORAGE_KEYS.THEME, theme.value)
    document.documentElement.setAttribute('data-theme', theme.value)
  }

  // 初始化主题
  const initTheme = () => {
    document.documentElement.setAttribute('data-theme', theme.value)
  }

  // 切换侧边栏
  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
    setLocalStorage(STORAGE_KEYS.SIDEBAR_COLLAPSED, sidebarCollapsed.value)
  }

  // 设置侧边栏状态
  const setSidebarCollapsed = (collapsed: boolean) => {
    sidebarCollapsed.value = collapsed
    setLocalStorage(STORAGE_KEYS.SIDEBAR_COLLAPSED, collapsed)
  }

  // 显示模态框
  const showModal = (type: string, data?: any) => {
    modalType.value = type
    modalData.value = data
    modalVisible.value = true
  }

  // 隐藏模态框
  const hideModal = () => {
    modalVisible.value = false
    modalType.value = null
    modalData.value = null
  }

  // 添加通知
  const addNotification = (notification: Omit<Notification, 'id' | 'timestamp'>) => {
    const newNotification: Notification = {
      id: Date.now().toString(),
      timestamp: new Date().toISOString(),
      ...notification,
    }

    notifications.value.push(newNotification)

    // 自动移除通知
    if (notification.duration !== 0) {
      setTimeout(() => {
        removeNotification(newNotification.id)
      }, notification.duration || 5000)
    }

    return newNotification.id
  }

  // 移除通知
  const removeNotification = (id: string) => {
    const index = notifications.value.findIndex(n => n.id === id)
    if (index !== -1) {
      notifications.value.splice(index, 1)
    }
  }

  // 清空所有通知
  const clearNotifications = () => {
    notifications.value = []
  }

  // 设置加载状态
  const setLoading = (key: string, loading: boolean) => {
    loadingStates.value[key] = loading
  }

  // 获取加载状态
  const getLoading = (key: string) => {
    return loadingStates.value[key] || false
  }

  // 设置错误状态
  const setError = (key: string, error: string | null) => {
    errorStates.value[key] = error
  }

  // 获取错误状态
  const getError = (key: string) => {
    return errorStates.value[key] || null
  }

  // 清空错误状态
  const clearError = (key: string) => {
    delete errorStates.value[key]
  }

  // 清空所有错误状态
  const clearAllErrors = () => {
    errorStates.value = {}
  }

  // 显示成功通知
  const showSuccess = (message: string, title?: string) => {
    return addNotification({
      type: 'success',
      title: title || '成功',
      message,
      duration: 3000,
      read: false,
    })
  }

  // 显示错误通知
  const showError = (message: string, title?: string) => {
    return addNotification({
      type: 'error',
      title: title || '错误',
      message,
      duration: 5000,
      read: false,
    })
  }

  // 显示警告通知
  const showWarning = (message: string, title?: string) => {
    return addNotification({
      type: 'warning',
      title: title || '警告',
      message,
      duration: 4000,
      read: false,
    })
  }

  // 显示信息通知
  const showInfo = (message: string, title?: string) => {
    return addNotification({
      type: 'info',
      title: title || '信息',
      message,
      duration: 3000,
      read: false,
    })
  }

  // 重置状态
  const reset = () => {
    modalVisible.value = false
    modalType.value = null
    modalData.value = null
    notifications.value = []
    loadingStates.value = {}
    errorStates.value = {}
  }

  return {
    // 状态
    theme,
    sidebarCollapsed,
    modalVisible,
    modalType,
    modalData,
    notifications,
    loadingStates,
    errorStates,

    // 计算属性
    isDarkTheme,
    isSidebarCollapsed,
    hasNotifications,
    isLoading,

    // 主题相关
    toggleTheme,
    setTheme,
    initTheme,

    // 侧边栏相关
    toggleSidebar,
    setSidebarCollapsed,

    // 模态框相关
    showModal,
    hideModal,

    // 通知相关
    addNotification,
    removeNotification,
    clearNotifications,
    showSuccess,
    showError,
    showWarning,
    showInfo,

    // 加载状态相关
    setLoading,
    getLoading,

    // 错误状态相关
    setError,
    getError,
    clearError,
    clearAllErrors,

    // 重置
    reset,
  }
})
