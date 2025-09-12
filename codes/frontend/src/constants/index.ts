/**
 * 应用常量配置
 */

// API配置
export const API_CONFIG = {
  BASE_URL: process.env.VITE_API_BASE_URL || '/api/v1',
  TIMEOUT: 300000, // 增加到300秒，适应AI模型推理时间
  RETRY_COUNT: 3,
}

// 存储键名
export const STORAGE_KEYS = {
  USER_TOKEN: 'user_token',
  USER_INFO: 'user_info',
  THEME: 'theme',
  SIDEBAR_COLLAPSED: 'sidebar_collapsed',
  CONVERSATION_HISTORY: 'conversation_history',
}

// 存储过期时间（毫秒）
export const STORAGE_EXPIRY = {
  TOKEN: 7 * 24 * 60 * 60 * 1000, // 7天
  USER_INFO: 24 * 60 * 60 * 1000, // 1天
  CONVERSATION: 30 * 24 * 60 * 60 * 1000, // 30天
}

// 错误码
export const ERROR_CODES = {
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  INTERNAL_ERROR: 500,
  NETWORK_ERROR: 'NETWORK_ERROR',
  TIMEOUT: 'TIMEOUT',
}

// 错误消息
export const ERROR_MESSAGES = {
  NETWORK_ERROR: '网络连接失败，请检查网络设置',
  TIMEOUT: '请求超时，请稍后重试',
  UNAUTHORIZED: '未授权访问，请重新登录',
  FORBIDDEN: '访问被拒绝',
  NOT_FOUND: '请求的资源不存在',
  INTERNAL_ERROR: '服务器内部错误',
  UNKNOWN_ERROR: '未知错误',
}

// 消息状态
export const MESSAGE_STATUS = {
  PENDING: 'pending',
  SENDING: 'sending',
  SENT: 'sent',
  DELIVERED: 'delivered',
  FAILED: 'failed',
}

// 对话类型
export const CONVERSATION_TYPES = {
  TEXT: 'text',
  VOICE: 'voice',
  IMAGE: 'image',
  DOCUMENT: 'document',
  MULTIMODAL: 'multimodal',
}

// 文件上传限制
export const UPLOAD_LIMITS = {
  MAX_SIZE: 10 * 1024 * 1024, // 10MB
  ALLOWED_TYPES: {
    IMAGE: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
    DOCUMENT: ['application/pdf', 'text/plain', 'application/msword'],
    AUDIO: ['audio/mp3', 'audio/wav', 'audio/ogg'],
  },
}

// 主题配置
export const THEME_CONFIG = {
  LIGHT: 'light',
  DARK: 'dark',
  AUTO: 'auto',
}

// 路由路径
export const ROUTES = {
  HOME: '/',
  LOGIN: '/auth/login',
  REGISTER: '/auth/register',
  CHAT: '/chat',
  PROFILE: '/profile',
  SETTINGS: '/settings',
  NOT_FOUND: '/404',
}

// 默认配置
export const DEFAULT_CONFIG = {
  PAGE_SIZE: 20,
  DEBOUNCE_DELAY: 300,
  ANIMATION_DURATION: 200,
}
