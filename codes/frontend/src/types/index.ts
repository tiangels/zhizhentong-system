/**
 * 智诊通前端系统类型定义
 * 定义所有接口、类型、枚举等
 */

// ==================== 基础类型 ====================

/**
 * 用户状态枚举
 */
export type UserStatus = 'active' | 'inactive' | 'banned'

/**
 * 用户角色枚举
 */
export type UserRole = 'user' | 'doctor' | 'admin'

/**
 * 对话类型枚举
 */
export type ConversationType = 'diagnosis' | 'consultation' | 'general'

/**
 * 对话状态枚举
 */
export type ConversationStatus = 'active' | 'completed' | 'archived'

/**
 * 消息类型枚举
 */
export type MessageType = 'user' | 'assistant'

/**
 * 消息状态枚举
 */
export type MessageStatus = 'sending' | 'sent' | 'delivered' | 'read' | 'error' | 'failed'

/**
 * 消息内容类型枚举
 */
export type MessageContentType = 'text' | 'image' | 'audio' | 'video' | 'file'

/**
 * 通知类型枚举
 */
export type NotificationType = 'success' | 'error' | 'warning' | 'info'

/**
 * 主题类型枚举
 */
export type ThemeType = 'light' | 'dark'

/**
 * 输入类型枚举
 */
export type InputType = 'text' | 'image' | 'audio' | 'video' | 'file'

/**
 * 文件类型枚举
 */
export type FileType = 'image' | 'audio' | 'video' | 'document'

// ==================== 用户相关类型 ====================

/**
 * 用户信息接口
 */
export interface User {
  id: string
  username: string
  email: string
  phone?: string
  avatar?: string
  status: UserStatus
  roles: UserRole[]
  createdAt: string
  updatedAt: string
}

/**
 * 用户档案接口
 */
export interface UserProfile {
  id: string
  userId: string
  realName?: string
  bio?: string
  age?: number
  gender?: 'male' | 'female' | 'other'
  location?: string
  medicalHistory?: string
  allergies?: string[]
  medications?: string[]
  emergencyContact?: {
    name: string
    phone: string
    relationship: string
  }
  createdAt: string
  updatedAt: string
}

/**
 * 登录请求接口
 */
export interface LoginRequest {
  username: string
  password: string
  rememberMe?: boolean
}

/**
 * 注册请求接口
 */
export interface RegisterRequest {
  username: string
  email: string
  password: string
  confirmPassword: string
  phone?: string
  agreeToTerms: boolean
}

/**
 * 密码重置请求接口
 */
export interface PasswordResetRequest {
  email: string
}

/**
 * 密码重置确认接口
 */
export interface PasswordResetConfirm {
  token: string
  newPassword: string
  confirmPassword: string
}

// ==================== 对话相关类型 ====================

/**
 * 对话接口
 */
export interface Conversation {
  id: string
  userId: string
  title: string
  type: ConversationType
  status: ConversationStatus
  messageCount: number
  lastMessage?: string
  lastMessageAt: string
  createdAt: string
  updatedAt: string
}

/**
 * 消息接口
 */
export interface Message {
  id: string
  conversationId: string
  userId?: string
  type: MessageType
  contentType: MessageContentType
  content: string
  status: MessageStatus
  timestamp: string
  metadata?: Record<string, any>
  createdAt: string
  updatedAt: string
}

/**
 * 发送消息请求接口
 */
export interface SendMessageRequest {
  conversationId?: string
  content: string
  contentType?: MessageContentType
  type?: MessageType
  metadata?: Record<string, any>
}

/**
 * 创建对话请求接口
 */
export interface CreateConversationRequest {
  title: string
  type: ConversationType
  initialMessage?: string
}

/**
 * 更新对话请求接口
 */
export interface UpdateConversationRequest {
  title?: string
  type?: ConversationType
  status?: ConversationStatus
}

// ==================== 多模态输入相关类型 ====================

/**
 * 输入数据接口
 */
export interface InputData {
  type: InputType
  content: string | File
  metadata?: Record<string, any>
}

/**
 * 处理后的输入数据接口
 */
export interface ProcessedInput {
  type: InputType
  content: string
  metadata: Record<string, any>
  fileInfo?: {
    name: string
    size: number
    type: string
    url: string
  }
}

/**
 * 文件上传进度接口
 */
export interface UploadProgress {
  loaded: number
  total: number
  percentage: number
  status: 'uploading' | 'completed' | 'error'
  error?: string
}

// ==================== UI相关类型 ====================

/**
 * 通知接口
 */
export interface Notification {
  id: string
  type: NotificationType
  title: string
  message: string
  timestamp: string
  read: boolean
  duration?: number
  action?: {
    label: string
    handler: () => void
  }
}

/**
 * 模态框接口
 */
export interface Modal {
  id: string
  type: string
  title: string
  content: any
  visible: boolean
  width?: number | string
  closable?: boolean
  maskClosable?: boolean
  onOk?: () => void
  onCancel?: () => void
}

/**
 * 侧边栏菜单项接口
 */
export interface MenuItem {
  key: string
  label: string
  icon?: string
  path?: string
  children?: MenuItem[]
  disabled?: boolean
  hidden?: boolean
}

// ==================== API相关类型 ====================

/**
 * API响应接口
 */
export interface ApiResponse<T = any> {
  success: boolean
  data: T
  message: string
  code: number
  timestamp: string
}

/**
 * 分页响应接口
 */
export interface PaginatedResponse<T = any> {
  items: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
  hasNext: boolean
  hasPrev: boolean
}

/**
 * 分页查询参数接口
 */
export interface PaginationParams {
  page?: number
  pageSize?: number
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}

/**
 * 搜索参数接口
 */
export interface SearchParams extends PaginationParams {
  keyword?: string
  filters?: Record<string, any>
}

// ==================== 错误相关类型 ====================

/**
 * API错误接口
 */
export interface ApiError {
  code: string
  message: string
  details?: any
  timestamp: string
}

/**
 * 验证错误接口
 */
export interface ValidationError {
  field: string
  message: string
  value?: any
}

// ==================== 配置相关类型 ====================

/**
 * 应用配置接口
 */
export interface AppConfig {
  api: {
    baseUrl: string
    timeout: number
    retries: number
  }
  upload: {
    maxFileSize: number
    allowedTypes: string[]
    chunkSize: number
  }
  features: {
    realTimeChat: boolean
    fileUpload: boolean
    voiceInput: boolean
    imageRecognition: boolean
  }
  ui: {
    theme: ThemeType
    language: string
    timezone: string
  }
}

/**
 * 用户设置接口
 */
export interface UserSettings {
  theme: ThemeType
  language: string
  notifications: {
    enabled: boolean
    sound: boolean
    desktop: boolean
    email: boolean
  }
  privacy: {
    analytics: boolean
    marketing: boolean
    dataSharing: boolean
  }
  accessibility: {
    fontSize: number
    highContrast: boolean
    screenReader: boolean
  }
}

// ==================== 统计相关类型 ====================

/**
 * 用户统计接口
 */
export interface UserStats {
  totalConversations: number
  totalMessages: number
  activeConversations: number
  lastActiveAt: string
  joinDate: string
}

/**
 * 对话统计接口
 */
export interface ConversationStats {
  totalMessages: number
  averageResponseTime: number
  userSatisfaction: number
  completionRate: number
}
