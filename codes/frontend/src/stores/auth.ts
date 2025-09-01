/**
 * 认证状态管理Store
 * 管理用户登录、注册、权限等认证相关状态
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, LoginRequest, RegisterRequest, UserRole } from '../types'
import { authApi } from '../services/apiService'
// import { mockAuthApi } from '../services/mockApi'
import { setLocalStorage, removeLocalStorage, getLocalStorage } from '../utils/helpers'
import { STORAGE_KEYS } from '../utils/constants'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const user = ref<User | null>(getLocalStorage<User>(STORAGE_KEYS.USER_INFO))
  const token = ref<string | null>(getLocalStorage<string>(STORAGE_KEYS.USER_TOKEN))
  const isLoading = ref<boolean>(false)
  const error = ref<string | null>(null)

  // 计算属性 - 直接基于当前状态计算，不依赖中间变量
  const isAuthenticated = computed(() => {
    const authenticated = !!token.value && !!user.value
    console.log('Auth store - isAuthenticated计算:', {
      token: !!token.value,
      user: !!user.value,
      result: authenticated,
    })
    return authenticated
  })

  const isLoggedIn = computed(() => {
    const loggedIn = isAuthenticated.value
    console.log('Auth store - isLoggedIn计算:', {
      token: !!token.value,
      user: !!user.value,
      isAuthenticated: isAuthenticated.value,
      result: loggedIn,
    })
    return loggedIn
  })
  const currentUser = computed(() => user.value)
  const hasRole = computed(() => (role: UserRole) => user.value?.roles?.includes(role) || false)

  // 登录
  const login = async(credentials: LoginRequest) => {
    console.log('Auth store - 开始登录:', credentials)

    try {
      isLoading.value = true
      error.value = null

      console.log('Auth store - 调用真实API服务...')
      console.log(
        'Auth store - API基础URL:',
        import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
      )

      // 调用真实的后端API
      const response = await authApi.login({
        username: credentials.username,
        password: credentials.password,
      })

      console.log('Auth store - API响应:', response)

      // API服务已经将后端响应转换为包装格式
      if (response && response.success && response.data) {
        const userData = response.data.user
        const userToken = response.data.token

        // 先保存到本地存储
        setLocalStorage(STORAGE_KEYS.USER_TOKEN, userToken)
        setLocalStorage(STORAGE_KEYS.USER_INFO, userData)

        // 更新状态
        user.value = userData
        token.value = userToken

        console.log('Auth store - 登录成功，用户信息:', userData)
        console.log('Auth store - 当前登录状态:', isAuthenticated.value)
        console.log('Auth store - isLoggedIn状态:', isLoggedIn.value)
        
        // 初始化用户专用的 chat 数据
        try {
          const { useChatStore } = await import('@/stores/chat')
          const chatStore = useChatStore()
          chatStore.initializeUserData()
        } catch (chatError) {
          console.error('初始化用户 chat 数据失败:', chatError)
        }
        
        return userData
      } else {
        throw new Error('登录响应格式不正确')
      }
    } catch (err: any) {
      console.error('Auth store - 登录错误:', err)
      console.error('Auth store - 错误详情:', {
        message: err.message,
        status: err.response?.status,
        data: err.response?.data,
        code: err.code,
      })

      // 根据错误类型提供更友好的错误信息
      let errorMessage = '登录失败'
      if (err.response?.status === 401) {
        errorMessage = '用户名或密码错误'
      } else if (err.response?.status === 422) {
        errorMessage = '输入数据验证失败'
      } else if (err.code === 'ERR_NETWORK' || err.message === 'Failed to fetch') {
        errorMessage = '网络连接失败，请检查后端服务是否正常运行'
      } else if (err.message) {
        errorMessage = err.message
      }

      error.value = errorMessage
      throw new Error(errorMessage)
    } finally {
      isLoading.value = false
    }
  }

  // 注册
  const register = async(userData: RegisterRequest) => {
    try {
      isLoading.value = true
      error.value = null

      const response = await authApi.register({
        username: userData.username,
        email: userData.email,
        password: userData.password,
        confirmPassword: userData.confirmPassword,
        agreeToTerms: userData.agreeToTerms,
      })

      // API服务已经将后端响应转换为包装格式
      if (response && response.success && response.data) {
        const newUser = response.data.user
        const userToken = response.data.token

        // 保存到本地存储
        setLocalStorage(STORAGE_KEYS.USER_TOKEN, userToken)
        setLocalStorage(STORAGE_KEYS.USER_INFO, newUser)

        // 更新状态
        user.value = newUser
        token.value = userToken

        return newUser
      } else {
        throw new Error('注册响应格式不正确')
      }
    } catch (err: any) {
      error.value = err.message || '注册失败'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // 登出
  const logout = async() => {
    try {
      if (token.value) {
        await authApi.logout()
      }
    } catch (err) {
      console.error('登出请求失败:', err)
    } finally {
      // 清除本地存储
      removeLocalStorage(STORAGE_KEYS.USER_TOKEN)
      removeLocalStorage(STORAGE_KEYS.USER_INFO)

      // 清除本地状态
      user.value = null
      token.value = null
      error.value = null
      
      // 清理用户专用的 chat 数据
      try {
        const { useChatStore } = await import('@/stores/chat')
        const chatStore = useChatStore()
        chatStore.clearUserData()
        
        // 同时清理localStorage中的用户数据
        const userId = user.value?.id
        if (userId) {
          const { clearUserStorage } = await import('@/utils/constants')
          clearUserStorage(userId)
          
          // 清理当前对话ID
          localStorage.removeItem(`currentConversationId_${userId}`)
        }
      } catch (chatError) {
        console.error('清理用户 chat 数据失败:', chatError)
      }
    }
  }

  // 刷新token
  const refreshToken = async() => {
    try {
      // 模拟刷新token
      const newToken = 'mock-jwt-token-' + Date.now()
      token.value = newToken
      setLocalStorage(STORAGE_KEYS.USER_TOKEN, newToken)
      return newToken
    } catch (err) {
      console.error('刷新token失败:', err)
      await logout()
    }
  }

  // 检查认证状态
  const checkAuthStatus = async() => {
    try {
      console.log('Auth store - 开始检查认证状态')
      console.log('Auth store - 当前token:', !!token.value)
      console.log('Auth store - 当前user:', !!user.value)

      // 如果没有token，直接返回false
      if (!token.value) {
        console.log('Auth store - 没有token，返回false')
        return false
      }

      // 如果有token但没有用户信息，尝试获取用户信息
      if (token.value && !user.value) {
        console.log('Auth store - 有token但没有用户信息，尝试获取')
        try {
          // 使用真实API获取用户信息
          const response = await authApi.getUserInfo()
          if (response && response.success && response.data) {
            user.value = response.data
            setLocalStorage(STORAGE_KEYS.USER_INFO, response.data)
            console.log('Auth store - 成功获取用户信息')
            return true
          } else {
            console.log('Auth store - 获取用户信息失败，清除认证状态')
            await logout()
            return false
          }
        } catch (err) {
          console.log('Auth store - 获取用户信息出错，清除认证状态')
          await logout()
          return false
        }
      }

      // 如果token和用户信息都存在，验证token有效性
      if (token.value && user.value) {
        console.log('Auth store - token和用户信息都存在，验证有效性')
        try {
          const response = await authApi.getUserInfo()
          if (response && response.success && response.data) {
            console.log('Auth store - token有效，认证状态正常')
            return true
          } else {
            console.log('Auth store - token无效，清除认证状态')
            await logout()
            return false
          }
        } catch (err) {
          console.log('Auth store - 验证token出错，清除认证状态')
          await logout()
          return false
        }
      }

      return false
    } catch (err) {
      console.error('检查认证状态失败:', err)
      await logout()
      return false
    }
  }

  // 更新用户信息
  const updateUserInfo = async(userData: Partial<User>) => {
    try {
      const response = await authApi.updateUserProfile(userData)

      if (response && response.success && response.data && user.value) {
        user.value = { ...user.value, ...response.data }
        setLocalStorage(STORAGE_KEYS.USER_INFO, user.value)
        return user.value
      }
    } catch (err) {
      console.error('更新用户信息失败:', err)
      throw err
    }
  }

  return {
    // 状态
    user,
    token,
    isAuthenticated,
    isLoading,
    error,

    // 计算属性
    isLoggedIn,
    currentUser,
    hasRole,

    // 方法
    login,
    register,
    logout,
    refreshToken,
    checkAuthStatus,
    updateUserInfo,
  }
})
