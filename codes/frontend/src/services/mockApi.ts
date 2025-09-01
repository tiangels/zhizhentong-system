/**
 * Mock API服务
 * 用于开发和测试阶段，模拟后端API响应
 */

import type { LoginRequest, RegisterRequest, User, ApiResponse } from '../types'

// 模拟延迟
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

// 模拟用户数据
const mockUsers: User[] = [
  {
    id: '1',
    username: 'testuser',
    email: 'test@example.com',
    avatar: '',
    roles: ['user'],
    status: 'active',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
]

// 模拟token
const mockToken = 'mock-jwt-token-' + Date.now()

/**
 * Mock认证API
 */
export const mockAuthApi = {
  /**
   * 模拟登录
   */
  async login(credentials: LoginRequest): Promise<ApiResponse<{ user: User; token: string }>> {
    console.log('Mock API - 登录请求:', credentials)

    // 模拟网络延迟
    await delay(1000)

    // 验证用户名和密码
    const user = mockUsers.find(u => u.username === credentials.username)

    if (user && credentials.password === '123456') {
      console.log('Mock API - 登录成功')
      return {
        success: true,
        message: '登录成功',
        data: {
          user,
          token: mockToken,
        },
        code: 200,
        timestamp: new Date().toISOString(),
      }
    } else {
      console.log('Mock API - 登录失败')
      throw new Error('邮箱或密码错误')
    }
  },

  /**
   * 模拟注册
   */
  async register(userData: RegisterRequest): Promise<ApiResponse<{ user: User; token: string }>> {
    console.log('Mock API - 注册请求:', userData)

    // 模拟网络延迟
    await delay(1000)

    // 检查邮箱是否已存在
    const existingUser = mockUsers.find(u => u.email === userData.email)
    if (existingUser) {
      throw new Error('邮箱已被注册')
    }

    // 创建新用户
    const newUser: User = {
      id: (mockUsers.length + 1).toString(),
      username: userData.username,
      email: userData.email,
      avatar: '',
      roles: ['user'],
      status: 'active',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }

    mockUsers.push(newUser)

    console.log('Mock API - 注册成功')
    return {
      success: true,
      message: '注册成功',
      data: {
        user: newUser,
        token: mockToken,
      },
      code: 200,
      timestamp: new Date().toISOString(),
    }
  },

  /**
   * 模拟登出
   */
  async logout(): Promise<ApiResponse<void>> {
    console.log('Mock API - 登出请求')
    await delay(500)

    return {
      success: true,
      message: '登出成功',
      data: undefined,
      code: 200,
      timestamp: new Date().toISOString(),
    }
  },

  /**
   * 模拟获取用户信息
   */
  async getUserInfo(): Promise<ApiResponse<User>> {
    console.log('Mock API - 获取用户信息')
    await delay(500)

    const user = mockUsers[0] // 返回第一个用户作为当前用户

    return {
      success: true,
      message: '获取用户信息成功',
      data: user,
      code: 200,
      timestamp: new Date().toISOString(),
    }
  },
}

export default mockAuthApi
