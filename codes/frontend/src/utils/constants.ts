/**
 * 智诊通前端系统常量定义
 * 统一管理所有常量值
 */

// ==================== API配置常量 ====================

/**
 * API配置
 */
export const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  TIMEOUT: 30000,
  RETRIES: 3,
  RETRY_DELAY: 1000,
} as const

// 强制输出配置信息用于调试
console.log('🔧 API_CONFIG 初始化:', {
  BASE_URL: API_CONFIG.BASE_URL,
  VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
  NODE_ENV: import.meta.env.NODE_ENV,
  MODE: import.meta.env.MODE,
})

/**
 * WebSocket配置
 */
export const WS_CONFIG = {
  URL: import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws',
  RECONNECT_INTERVAL: 3000,
  MAX_RECONNECT_ATTEMPTS: 5,
} as const

// ==================== 错误代码常量 ====================

/**
 * 错误代码
 */
export const ERROR_CODES = {
  NETWORK_ERROR: 'NETWORK_ERROR',
  TIMEOUT_ERROR: 'TIMEOUT_ERROR',
  UNAUTHORIZED: 'UNAUTHORIZED',
  FORBIDDEN: 'FORBIDDEN',
  NOT_FOUND: 'NOT_FOUND',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  SERVER_ERROR: 'SERVER_ERROR',
  RATE_LIMIT: 'RATE_LIMIT',
  UNKNOWN_ERROR: 'UNKNOWN_ERROR',
  MESSAGE_SEND_FAILED: 'MESSAGE_SEND_FAILED',
} as const

/**
 * 错误消息
 */
export const ERROR_MESSAGES = {
  NETWORK_ERROR: '网络连接失败，请检查网络设置',
  TIMEOUT_ERROR: '请求超时，请稍后重试',
  UNAUTHORIZED: '未授权访问，请重新登录',
  FORBIDDEN: '访问被拒绝，权限不足',
  NOT_FOUND: '请求的资源不存在',
  VALIDATION_ERROR: '输入数据验证失败',
  SERVER_ERROR: '服务器内部错误',
  RATE_LIMIT: '请求过于频繁，请稍后重试',
  UNKNOWN_ERROR: '未知错误，请稍后重试',
  MESSAGE_SEND_FAILED: '消息发送失败',
  TIMEOUT: '请求超时',
} as const

// ==================== 存储相关常量 ====================

/**
 * 本地存储键名
 */
export const STORAGE_KEYS = {
  USER_TOKEN: 'user_token',
  USER_INFO: 'user_info',
  THEME: 'theme',
  LANGUAGE: 'language',
  SIDEBAR_COLLAPSED: 'sidebar_collapsed',
  CHAT_HISTORY: 'chat_history', // 基础键名，实际使用时会加上用户ID
  CHAT_MESSAGES: 'chat_messages', // 基础键名，实际使用时会加上用户ID
  USER_SETTINGS: 'user_settings',
} as const

/**
 * 生成用户专用的存储键名
 * @param baseKey 基础键名
 * @param userId 用户ID
 * @returns 用户专用的存储键名
 */
export const getUserStorageKey = (baseKey: string, userId: string | number): string => {
  return `${baseKey}_user_${userId}`
}

/**
 * 清理指定用户的所有本地存储数据
 * @param userId 用户ID
 */
export const clearUserStorage = (userId: string | number): void => {
  const userKeys = [
    getUserStorageKey(STORAGE_KEYS.CHAT_HISTORY, userId),
    getUserStorageKey(STORAGE_KEYS.CHAT_MESSAGES, userId),
    getUserStorageKey(STORAGE_KEYS.USER_SETTINGS, userId)
  ]
  
  userKeys.forEach(key => {
    try {
      localStorage.removeItem(key)
      console.log(`清理用户存储: ${key}`)
    } catch (error) {
      console.error(`清理用户存储失败: ${key}`, error)
    }
  })
}

/**
 * 存储过期时间（毫秒）
 */
export const STORAGE_EXPIRY = {
  USER_TOKEN: 7 * 24 * 60 * 60 * 1000, // 7天
  USER_INFO: 24 * 60 * 60 * 1000, // 1天
  CHAT_HISTORY: 30 * 24 * 60 * 60 * 1000, // 30天
  CHAT_MESSAGES: 30 * 24 * 60 * 60 * 1000, // 30天
} as const

// ==================== 文件相关常量 ====================

/**
 * 文件类型
 */
export const FILE_TYPES = {
  IMAGE: ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp'],
  AUDIO: ['audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/m4a', 'audio/aac'],
  VIDEO: ['video/mp4', 'video/webm', 'video/ogg', 'video/avi', 'video/mov'],
  DOCUMENT: [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/plain',
  ],
} as const

/**
 * 文件大小限制（字节）
 */
export const FILE_SIZE_LIMITS = {
  IMAGE: 10 * 1024 * 1024, // 10MB
  AUDIO: 50 * 1024 * 1024, // 50MB
  VIDEO: 100 * 1024 * 1024, // 100MB
  DOCUMENT: 20 * 1024 * 1024, // 20MB
} as const

/**
 * 上传配置
 */
export const UPLOAD_CONFIG = {
  MAX_FILE_SIZE: 100 * 1024 * 1024, // 100MB
  ALLOWED_TYPES: [
    ...FILE_TYPES.IMAGE,
    ...FILE_TYPES.AUDIO,
    ...FILE_TYPES.VIDEO,
    ...FILE_TYPES.DOCUMENT,
  ].join(','),
  CHUNK_SIZE: 1024 * 1024, // 1MB
  CONCURRENT_UPLOADS: 3,
} as const

// ==================== 时间格式常量 ====================

/**
 * 时间格式
 */
export const TIME_FORMAT = {
  DATE: 'YYYY-MM-DD',
  TIME: 'HH:mm:ss',
  DATETIME: 'YYYY-MM-DD HH:mm:ss',
  RELATIVE: 'relative',
} as const

// ==================== 正则表达式常量 ====================

/**
 * 正则表达式
 */
export const REGEX = {
  EMAIL: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  PHONE: /^1[3-9]\d{9}$/,
  PASSWORD: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$/,
  USERNAME: /^[a-zA-Z0-9_]{3,20}$/,
  URL: /^https?:\/\/.+/,
  CHINESE_PHONE: /^1[3-9]\d{9}$/,
  ID_CARD: /^[1-9]\d{5}(18|19|20)\d{2}((0[1-9])|(1[0-2]))(([0-2][1-9])|10|20|30|31)\d{3}[0-9Xx]$/,
} as const

// ==================== 分页常量 ====================

/**
 * 分页配置
 */
export const PAGINATION = {
  DEFAULT_PAGE: 1,
  DEFAULT_PAGE_SIZE: 20,
  MAX_PAGE_SIZE: 100,
  PAGE_SIZE_OPTIONS: [10, 20, 50, 100],
} as const

// ==================== 路由常量 ====================

/**
 * 路由路径
 */
export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  REGISTER: '/register',
  CHAT: '/chat',
  PROFILE: '/profile',
  SETTINGS: '/settings',
  HISTORY: '/history',
  NOT_FOUND: '/404',
} as const

/**
 * 路由名称
 */
export const ROUTE_NAMES = {
  HOME: 'home',
  LOGIN: 'login',
  REGISTER: 'register',
  CHAT: 'chat',
  PROFILE: 'profile',
  SETTINGS: 'settings',
  HISTORY: 'history',
  NOT_FOUND: 'not-found',
} as const

// ==================== 主题常量 ====================

/**
 * 主题配置
 */
export const THEME = {
  LIGHT: 'light',
  DARK: 'dark',
  AUTO: 'auto',
} as const

/**
 * 主题色
 */
export const THEME_COLORS = {
  PRIMARY: '#1890ff',
  SUCCESS: '#52c41a',
  WARNING: '#faad14',
  ERROR: '#f5222d',
  INFO: '#1890ff',
} as const

// ==================== 语言常量 ====================

/**
 * 支持的语言
 */
export const LANGUAGES = {
  ZH_CN: 'zh-CN',
  EN_US: 'en-US',
} as const

/**
 * 语言名称
 */
export const LANGUAGE_NAMES = {
  [LANGUAGES.ZH_CN]: '简体中文',
  [LANGUAGES.EN_US]: 'English',
} as const

// ==================== 消息状态常量 ====================

/**
 * 消息状态
 */
export const MESSAGE_STATUS = {
  SENDING: 'sending',
  SENT: 'sent',
  DELIVERED: 'delivered',
  READ: 'read',
  ERROR: 'error',
  FAILED: 'failed',
} as const

// ==================== 通知常量 ====================

/**
 * 通知类型
 */
export const NOTIFICATION_TYPE = {
  SUCCESS: 'success',
  ERROR: 'error',
  WARNING: 'warning',
  INFO: 'info',
} as const

/**
 * 通知持续时间（毫秒）
 */
export const NOTIFICATION_DURATION = {
  SUCCESS: 3000,
  ERROR: 5000,
  WARNING: 4000,
  INFO: 3000,
} as const

// ==================== 动画常量 ====================

/**
 * 动画持续时间（毫秒）
 */
export const ANIMATION_DURATION = {
  FAST: 150,
  NORMAL: 300,
  SLOW: 500,
} as const

/**
 * 动画缓动函数
 */
export const ANIMATION_EASING = {
  EASE_IN: 'ease-in',
  EASE_OUT: 'ease-out',
  EASE_IN_OUT: 'ease-in-out',
  LINEAR: 'linear',
} as const

// ==================== 响应式断点常量 ====================

/**
 * 响应式断点
 */
export const BREAKPOINTS = {
  XS: 480,
  SM: 576,
  MD: 768,
  LG: 992,
  XL: 1200,
  XXL: 1600,
} as const

// ==================== 业务常量 ====================

/**
 * 对话类型
 */
export const CONVERSATION_TYPE = {
  DIAGNOSIS: 'diagnosis',
  CONSULTATION: 'consultation',
  GENERAL: 'general',
} as const

/**
 * 用户角色
 */
export const USER_ROLE = {
  USER: 'user',
  DOCTOR: 'doctor',
  ADMIN: 'admin',
} as const

/**
 * 用户状态
 */
export const USER_STATUS = {
  ACTIVE: 'active',
  INACTIVE: 'inactive',
  BANNED: 'banned',
} as const
