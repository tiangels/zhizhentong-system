/**
 * API服务文件
 * 提供认证、用户管理等API方法
 */

import { get, post, put, del } from './api/index'
import type { LoginRequest, RegisterRequest, User, ApiResponse, UserProfile } from '../types'

/**
 * 认证相关API
 */
export const authApi = {
  /**
   * 用户登录
   */
  async login(credentials: LoginRequest): Promise<ApiResponse<{ user: User; token: string }>> {
    console.log('API Service - 登录请求:', credentials)
    console.log('API Service - 请求URL:', '/auth/login')
    console.log(
      'API Service - 完整URL:',
      `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/v1/auth/login`,
    )

    try {
      const response = await post('/auth/login', credentials)
      console.log('API Service - 登录响应:', response)

      // 后端直接返回响应数据，需要转换为前端期望的格式
      const transformedResponse: ApiResponse<{ user: User; token: string }> = {
        success: true,
        data: {
          user: {
            id: response.user.id,
            username: response.user.username,
            email: response.user.email,
            phone: response.user.phone,
            avatar: response.user.avatar_url,
            status: response.user.is_active ? 'active' : 'inactive',
            roles: ['user'], // 默认角色
            createdAt: response.user.created_at,
            updatedAt: response.user.updated_at,
          },
          token: response.access_token,
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
      const response = await post('/auth/register', userData)

      // 将后端响应格式转换为前端期望的格式
      const transformedResponse: ApiResponse<{ user: User; token: string }> = {
        success: true,
        data: {
          user: {
            id: response.id,
            username: response.username,
            email: response.email,
            phone: response.phone,
            avatar: response.avatar_url,
            status: response.is_active ? 'active' : 'inactive',
            roles: ['user'], // 默认角色
            createdAt: response.created_at,
            updatedAt: response.updated_at,
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
      await post('/auth/logout')
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
      const response = await get('/auth/me')

      // 转换后端响应格式为前端期望的格式
      const transformedResponse: ApiResponse<User> = {
        success: true,
        data: {
          id: response.id,
          username: response.username,
          email: response.email,
          phone: response.phone,
          avatar: response.avatar_url,
          status: response.is_active ? 'active' : 'inactive',
          roles: ['user'], // 默认角色
          createdAt: response.created_at,
          updatedAt: response.updated_at,
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
        timestamp: new Date().toISOString()
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
        timestamp: new Date().toISOString()
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
      title: data.title || "新对话",
      conversation_type: data.conversation_type || data.type || "chat",
      status: data.status || "active",
      meta_data: data.meta_data || null
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
        timestamp: new Date().toISOString()
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
      message_type: message.message_type || message.contentType || message.type || 'text'
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
        timestamp: new Date().toISOString()
      }
      
      console.log('🎯 发送消息 - 转换后响应:', transformedResponse)
      return transformedResponse
    } catch (error) {
      console.error('🎯 发送消息 - 错误:', error)
      // 改进错误处理，确保错误信息可读
      const errorMessage = error instanceof Error ? error.message : 
                          typeof error === 'object' ? JSON.stringify(error) : 
                          String(error)
      console.error('🎯 发送消息 - 错误详情:', errorMessage)
      throw new Error(errorMessage)
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
        timestamp: new Date().toISOString()
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
    onProgress?: (progress: number) => void,
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
