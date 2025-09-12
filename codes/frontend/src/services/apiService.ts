/**
 * API服务文件
 * 提供认证、用户管理等API方法
 */

import { get, post, put, del } from './api/index'
import type { LoginRequest, RegisterRequest, User, ApiResponse, UserProfile } from '../types'
import { STORAGE_KEYS } from '../utils/constants'

/**
 * 认证相关API
 */
export const authApi = {
  /**
   * 用户登录
   */
  async login(credentials: LoginRequest): Promise<ApiResponse<{ user: User; token: string }>> {
    console.log('🌐 API Service - 登录请求:', credentials.username)

    try {
      // 认证API使用不同的baseURL，直接使用相对路径
      const response = await fetch('/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials)
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const data = await response.json()
      console.log('🌐 API Service - 登录响应成功')

      // 后端直接返回响应数据，需要转换为前端期望的格式
      const transformedResponse: ApiResponse<{ user: User; token: string }> = {
        success: true,
        data: {
          user: {
            id: data.user.id,
            username: data.user.username,
            email: data.user.email,
            phone: data.user.phone,
            avatar: data.user.avatar_url,
            status: data.user.is_active ? 'active' : 'inactive',
            roles: ['user'], // 默认角色
            createdAt: data.user.created_at,
            updatedAt: data.user.updated_at,
          },
          token: data.access_token,
        },
        message: '登录成功',
        code: 200,
        timestamp: new Date().toISOString(),
      }

      return transformedResponse
    } catch (error: any) {
      console.error('API Service - 登录请求失败:', error)
      console.error('API Service - 错误详情:', {
        message: error.message,
        status: error.response?.status,
        data: error.response?.data,
        code: error.code,
        config: error.config,
      })

      // 如果是网络错误，提供更友好的错误信息
      if (error.code === 'ERR_NETWORK' || error.message === 'Failed to fetch') {
        throw new Error('网络连接失败，请检查后端服务是否正常运行')
      }

      // 如果是HTTP错误，传递具体的错误信息
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail)
      }

      throw error
    }
  },

  /**
   * 用户注册
   */
  async register(userData: RegisterRequest): Promise<ApiResponse<{ user: User; token: string }>> {
    try {
      const response = await fetch('/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData)
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const data = await response.json()

      // 将后端响应格式转换为前端期望的格式
      const transformedResponse: ApiResponse<{ user: User; token: string }> = {
        success: true,
        data: {
          user: {
            id: data.id,
            username: data.username,
            email: data.email,
            phone: data.phone,
            avatar: data.avatar_url,
            status: data.is_active ? 'active' : 'inactive',
            roles: ['user'], // 默认角色
            createdAt: data.created_at,
            updatedAt: data.updated_at,
          },
          token: '', // 注册后没有token，需要用户登录
        },
        message: '注册成功',
        code: 200,
        timestamp: new Date().toISOString(),
      }

      return transformedResponse
    } catch (error: any) {
      console.error('注册失败:', error)
      throw error
    }
  },

  /**
   * 用户登出
   */
  async logout(): Promise<ApiResponse<void>> {
    try {
      const response = await fetch('/auth/logout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      return {
        success: true,
        data: undefined,
        message: '登出成功',
        code: 200,
        timestamp: new Date().toISOString(),
      }
    } catch (error: any) {
      console.error('登出失败:', error)
      throw error
    }
  },

  /**
   * 获取当前用户信息
   */
  async getUserInfo(): Promise<ApiResponse<User>> {
    try {
      // 使用getLocalStorage方法正确读取token
      const tokenData = JSON.parse(localStorage.getItem(STORAGE_KEYS.USER_TOKEN) || '{}')
      const token = tokenData.value
      if (!token) {
        throw new Error('未找到访问令牌')
      }
      
      const response = await fetch('/auth/me', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        }
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const data = await response.json()

      // 转换后端响应格式为前端期望的格式
      const transformedResponse: ApiResponse<User> = {
        success: true,
        data: {
          id: data.id,
          username: data.username,
          email: data.email,
          phone: data.phone,
          avatar: data.avatar_url,
          status: data.is_active ? 'active' : 'inactive',
          roles: ['user'], // 默认角色
          createdAt: data.created_at,
          updatedAt: data.updated_at,
        },
        message: '获取用户信息成功',
        code: 200,
        timestamp: new Date().toISOString(),
      }

      return transformedResponse
    } catch (error: any) {
      console.error('获取用户信息失败:', error)
      throw error
    }
  },

  /**
   * 更新用户档案
   */
  async updateUserProfile(userData: Partial<UserProfile>): Promise<ApiResponse<UserProfile>> {
    try {
      const response = await put('/auth/me', userData)
      return {
        success: true,
        data: response,
        message: '更新成功',
        code: 200,
        timestamp: new Date().toISOString(),
      }
    } catch (error: any) {
      console.error('更新用户档案失败:', error)
      throw error
    }
  },

  /**
   * 获取用户详情
   */
  async getUserById(id: string): Promise<ApiResponse<User>> {
    return get(`/users/${id}`)
  },

  /**
   * 创建用户
   */
  async createUser(userData: RegisterRequest): Promise<ApiResponse<User>> {
    return post('/users', userData)
  },

  /**
   * 更新用户
   */
  async updateUser(id: string, userData: Partial<User>): Promise<ApiResponse<User>> {
    return put(`/users/${id}`, userData)
  },

  /**
   * 删除用户
   */
  async deleteUser(id: string): Promise<ApiResponse<void>> {
    return del(`/users/${id}`)
  },
}

/**
 * 对话相关API
 */
export const conversationApi = {
  /**
   * 获取对话列表
   */
  async getConversations(params?: any): Promise<ApiResponse<any[]>> {
    console.log('🎯 获取对话列表 - 参数:', params)

    try {
      const response = await get('/conversations/', params)
      console.log('🎯 获取对话列表 - 后端响应:', response)

      // 后端直接返回对话数组，需要包装成前端期望的格式
      const transformedResponse: ApiResponse<any[]> = {
        success: true,
        data: Array.isArray(response) ? response : [],
        message: '获取对话列表成功',
        code: 200,
        timestamp: new Date().toISOString(),
      }

      console.log('🎯 获取对话列表 - 转换后响应:', transformedResponse)
      return transformedResponse
    } catch (error) {
      console.error('🎯 获取对话列表 - 错误:', error)
      throw error
    }
  },

  /**
   * 获取对话详情
   */
  async getConversation(id: string): Promise<ApiResponse<any>> {
    console.log('🎯 获取对话详情 - ID:', id)

    try {
      const response = await get(`/conversations/${id}`)
      console.log('🎯 获取对话详情 - 后端响应:', response)

      // 后端直接返回对话数据，需要包装成前端期望的格式
      const transformedResponse: ApiResponse<any> = {
        success: true,
        data: response,
        message: '获取对话详情成功',
        code: 200,
        timestamp: new Date().toISOString(),
      }

      console.log('🎯 获取对话详情 - 转换后响应:', transformedResponse)
      return transformedResponse
    } catch (error) {
      console.error('🎯 获取对话详情 - 错误:', error)
      throw error
    }
  },

  /**
   * 创建对话
   */
  async createConversation(data: any): Promise<ApiResponse<any>> {
    console.log('🎯 创建对话 - 原始数据:', data)
    console.log('🎯 创建对话 - 数据类型:', typeof data)

    // 确保数据正确序列化
    const payload = {
      title: data.title || '新对话',
      conversation_type: data.conversation_type || data.type || 'chat',
      status: data.status || 'active',
      meta_data: data.meta_data || null,
    }

    console.log('🎯 创建对话 - 处理后数据:', payload)

    try {
      const response = await post('/conversations/', payload)
      console.log('🎯 创建对话 - 后端响应:', response)

      // 后端直接返回对话数据，需要包装成前端期望的格式
      const transformedResponse: ApiResponse<any> = {
        success: true,
        data: response,
        message: '对话创建成功',
        code: 200,
        timestamp: new Date().toISOString(),
      }

      console.log('🎯 创建对话 - 转换后响应:', transformedResponse)
      return transformedResponse
    } catch (error) {
      console.error('🎯 创建对话 - 错误:', error)
      throw error
    }
  },

  /**
   * 发送消息
   */
  async sendMessage(conversationId: string, message: any): Promise<ApiResponse<any>> {
    console.log('🎯 发送消息 - 对话ID:', conversationId)
    console.log('🎯 发送消息 - 原始消息内容:', message)

    // 确保数据格式符合后端期望的 SimpleMessageCreate 模型
    const payload = {
      content: message.content || message.message || message.text || '',
      message_type: message.message_type || message.contentType || message.type || 'text',
    }

    console.log('🎯 发送消息 - 处理后消息内容:', payload)

    try {
      const response = await post(`/conversations/${conversationId}/messages`, payload)
      console.log('🎯 发送消息 - 后端响应:', response)

      // 后端直接返回SendMessageResponse数据，需要包装成前端期望的格式
      const transformedResponse: ApiResponse<any> = {
        success: true,
        data: response,
        message: '消息发送成功',
        code: 200,
        timestamp: new Date().toISOString(),
      }

      console.log('🎯 发送消息 - 转换后响应:', transformedResponse)
      console.log('🎯 发送消息 - 响应数据结构:', {
        hasAiResponse: 'ai_response' in response,
        aiResponseValue: response.ai_response,
        responseKeys: Object.keys(response)
      })
      return transformedResponse
    } catch (error) {
      console.error('🎯 发送消息 - 错误:', error)
      // 改进错误处理，确保错误信息可读
      const errorMessage =
        error instanceof Error
          ? error.message
          : typeof error === 'object'
            ? JSON.stringify(error)
            : String(error)
      console.error('🎯 发送消息 - 错误详情:', errorMessage)
      throw new Error(errorMessage)
    }
  },

  /**
   * 发送消息（流式）
   */
  async sendMessageStream(
    conversationId: string, 
    message: any, 
    onMessage: (data: any) => void,
    onError?: (error: Error) => void,
    onComplete?: () => void
  ): Promise<void> {
    console.log('🎯 发送流式消息 - 对话ID:', conversationId)
    console.log('🎯 发送流式消息 - 原始消息内容:', message)

    // 确保数据格式符合后端期望的 SimpleMessageCreate 模型
    const payload = {
      content: message.content || message.message || message.text || '',
      message_type: message.message_type || message.contentType || message.type || 'text',
    }

    console.log('🎯 发送流式消息 - 处理后消息内容:', payload)

    try {
      // 获取token - 使用正确的方法读取包装后的token
      const tokenData = JSON.parse(localStorage.getItem(STORAGE_KEYS.USER_TOKEN) || '{}')
      const token = tokenData.value
      if (!token) {
        throw new Error('未找到访问令牌')
      }

      // 构建请求URL - 直接使用相对路径，让Vite代理处理
      const url = `/api/v1/conversations/${conversationId}/messages/stream`

      console.log('🎯 流式请求URL:', url)

      // 使用fetch API发送POST请求并处理流式响应
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      if (!response.body) {
        throw new Error('响应体为空')
      }

      // 创建读取器
      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      try {
        while (true) {
          const { done, value } = await reader.read()
          
          if (done) {
            console.log('🎯 流式读取完成')
            break
          }

          // 解码数据
          const chunk = decoder.decode(value, { stream: true })
          const lines = chunk.split('\n')

          for (const line of lines) {
            if (line.trim() === '') continue
            
            // 处理SSE格式的数据
            if (line.startsWith('data: ')) {
              const dataStr = line.slice(6) // 移除 'data: ' 前缀
              
              if (dataStr === '[DONE]') {
                console.log('🎯 流式数据结束')
                break
              }

              try {
                const data = JSON.parse(dataStr)
                console.log('🎯 收到流式数据:', data)
                onMessage(data)
              } catch (error) {
                console.error('🎯 解析流式数据失败:', error, '数据:', dataStr)
              }
            }
          }
        }
      } finally {
        reader.releaseLock()
      }

      onComplete?.()

    } catch (error) {
      console.error('🎯 发送流式消息 - 错误:', error)
      const errorMessage =
        error instanceof Error
          ? error.message
          : typeof error === 'object'
            ? JSON.stringify(error)
            : String(error)
      onError?.(new Error(errorMessage))
    }
  },

  /**
   * 删除对话
   */
  async deleteConversation(id: string): Promise<ApiResponse<void>> {
    console.log('🎯 删除对话 - ID:', id)

    try {
      const response = await del(`/conversations/${id}`)
      console.log('🎯 删除对话 - 后端响应:', response)

      // 后端返回删除确认消息，需要包装成前端期望的格式
      const transformedResponse: ApiResponse<void> = {
        success: true,
        data: undefined,
        message: response?.message || '对话删除成功',
        code: 200,
        timestamp: new Date().toISOString(),
      }

      console.log('🎯 删除对话 - 转换后响应:', transformedResponse)
      return transformedResponse
    } catch (error) {
      console.error('🎯 删除对话 - 错误:', error)
      throw error
    }
  },
}

/**
 * 文件上传API
 */
export const uploadApi = {
  /**
   * 上传文件
   */
  async uploadFile(
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<ApiResponse<{ url: string }>> {
    const formData = new FormData()
    formData.append('file', file)

    return post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent: any) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      },
    })
  },
}

/**
 * 默认导出认证API
 */
export default authApi
