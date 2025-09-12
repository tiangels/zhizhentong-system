/**
 * 智诊通前端系统辅助工具函数
 * 提供常用的工具函数和辅助方法
 */

import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'

dayjs.extend(relativeTime)
import { cloneDeep, debounce, throttle } from 'lodash-es'
import type {
  User,
  // UserProfile,
  Message,
  Conversation,
  InputData,
  // ProcessedInput,
  UploadProgress,
} from '@/types'
import {
  // STORAGE_KEYS,
  // STORAGE_EXPIRY,
  FILE_TYPES,
  FILE_SIZE_LIMITS,
  TIME_FORMAT,
  REGEX,
} from './constants'

// ==================== 存储相关工具函数 ====================

/**
 * 设置本地存储数据
 * @param key 存储键名
 * @param value 存储值
 * @param expiry 过期时间（毫秒）
 */
export function setLocalStorage<T>(key: string, value: T, expiry?: number): void {
  try {
    const data = {
      value,
      timestamp: Date.now(),
      expiry: expiry ? Date.now() + expiry : null,
    }
    localStorage.setItem(key, JSON.stringify(data))
  } catch (error) {
    console.error('设置本地存储失败:', error)
  }
}

/**
 * 获取本地存储数据
 * @param key 存储键名
 * @returns 存储的值或null
 */
export function getLocalStorage<T>(key: string): T | null {
  try {
    const item = localStorage.getItem(key)
    if (!item) return null

    const data = JSON.parse(item)

    // 检查是否过期
    if (data.expiry && Date.now() > data.expiry) {
      localStorage.removeItem(key)
      return null
    }

    return data.value
  } catch (error) {
    console.error('获取本地存储失败:', error)
    return null
  }
}

/**
 * 移除本地存储数据
 * @param key 存储键名
 */
export function removeLocalStorage(key: string): void {
  try {
    localStorage.removeItem(key)
  } catch (error) {
    console.error('移除本地存储失败:', error)
  }
}

/**
 * 清空本地存储
 */
export function clearLocalStorage(): void {
  try {
    localStorage.clear()
  } catch (error) {
    console.error('清空本地存储失败:', error)
  }
}

// ==================== 时间处理工具函数 ====================

/**
 * 格式化时间
 * @param date 日期对象或时间戳
 * @param format 格式化字符串
 * @returns 格式化后的时间字符串
 */
export function formatDateTime(
  date: Date | string | number,
  format: string = TIME_FORMAT.DATETIME
): string {
  return dayjs(date).format(format)
}

/**
 * 获取相对时间
 * @param date 日期对象或时间戳
 * @returns 相对时间字符串
 */
export function getRelativeTime(date: Date | string | number): string {
  return dayjs(date).fromNow()
}

/**
 * 检查日期是否为今天
 * @param date 日期对象或时间戳
 * @returns 是否为今天
 */
export function isToday(date: Date | string | number): boolean {
  return dayjs(date).isSame(dayjs(), 'day')
}

/**
 * 检查日期是否为昨天
 * @param date 日期对象或时间戳
 * @returns 是否为昨天
 */
export function isYesterday(date: Date | string | number): boolean {
  return dayjs(date).isSame(dayjs().subtract(1, 'day'), 'day')
}

/**
 * 获取时间戳
 * @returns 当前时间戳
 */
export function getTimestamp(): number {
  return Date.now()
}

// ==================== 文件处理工具函数 ====================

/**
 * 获取文件大小的人类可读格式
 * @param bytes 字节数
 * @returns 格式化后的文件大小
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'

  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return parseFloat((bytes / k ** i).toFixed(2)) + ' ' + sizes[i]
}

/**
 * 检查文件类型是否支持
 * @param file 文件对象
 * @returns 是否支持该文件类型
 */
export function isSupportedFileType(file: File): boolean {
  const allSupportedTypes = [
    ...FILE_TYPES.IMAGE,
    ...FILE_TYPES.AUDIO,
    ...FILE_TYPES.VIDEO,
    ...FILE_TYPES.DOCUMENT,
  ]
  return allSupportedTypes.includes(file.type as any)
}

/**
 * 检查文件大小是否在限制范围内
 * @param file 文件对象
 * @returns 是否在大小限制范围内
 */
export function isFileSizeValid(file: File): boolean {
  const fileType = file.type.split('/')[0]
  const maxSize =
    FILE_SIZE_LIMITS[fileType as keyof typeof FILE_SIZE_LIMITS] || FILE_SIZE_LIMITS.DOCUMENT
  return file.size <= maxSize
}

/**
 * 获取文件类型
 * @param file 文件对象
 * @returns 文件类型
 */
export function getFileType(file: File): 'image' | 'audio' | 'video' | 'document' | 'unknown' {
  const type = file.type.split('/')[0]
  switch (type) {
    case 'image':
      return 'image'
    case 'audio':
      return 'audio'
    case 'video':
      return 'video'
    case 'application':
    case 'text':
      return 'document'
    default:
      return 'unknown'
  }
}

/**
 * 创建文件URL
 * @param file 文件对象
 * @returns 文件URL
 */
export function createFileURL(file: File): string {
  return URL.createObjectURL(file)
}

/**
 * 释放文件URL
 * @param url 文件URL
 */
export function revokeFileURL(url: string): void {
  URL.revokeObjectURL(url)
}

// ==================== 数据验证工具函数 ====================

/**
 * 验证邮箱格式
 * @param email 邮箱地址
 * @returns 是否有效
 */
export function isValidEmail(email: string): boolean {
  return REGEX.EMAIL.test(email)
}

/**
 * 验证手机号格式
 * @param phone 手机号
 * @returns 是否有效
 */
export function isValidPhone(phone: string): boolean {
  return REGEX.PHONE.test(phone)
}

/**
 * 验证密码强度
 * @param password 密码
 * @returns 是否有效
 */
export function isValidPassword(password: string): boolean {
  return REGEX.PASSWORD.test(password)
}

/**
 * 验证用户名格式
 * @param username 用户名
 * @returns 是否有效
 */
export function isValidUsername(username: string): boolean {
  return REGEX.USERNAME.test(username)
}

/**
 * 验证URL格式
 * @param url URL地址
 * @returns 是否有效
 */
export function isValidURL(url: string): boolean {
  return REGEX.URL.test(url)
}

// ==================== 数据处理工具函数 ====================

/**
 * 深拷贝对象
 * @param obj 要拷贝的对象
 * @returns 拷贝后的对象
 */
export function deepClone<T>(obj: T): T {
  return cloneDeep(obj)
}

/**
 * 防抖函数
 * @param func 要防抖的函数
 * @param wait 等待时间
 * @returns 防抖后的函数
 */
export function debounceFunc<T extends (...args: any[]) => any>(
  func: T,
  wait: number = 300
): (...args: Parameters<T>) => void {
  return debounce(func, wait)
}

/**
 * 节流函数
 * @param func 要节流的函数
 * @param wait 等待时间
 * @returns 节流后的函数
 */
export function throttleFunc<T extends (...args: any[]) => any>(
  func: T,
  wait: number = 300
): (...args: Parameters<T>) => void {
  return throttle(func, wait)
}

/**
 * 生成唯一ID
 * @returns 唯一ID字符串
 */
export function generateId(): string {
  return Date.now().toString(36) + Math.random().toString(36).substr(2)
}

/**
 * 生成UUID
 * @returns UUID字符串
 */
export function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

// ==================== 数组处理工具函数 ====================

/**
 * 数组去重
 * @param array 要去重的数组
 * @param key 去重的键名（对象数组）
 * @returns 去重后的数组
 */
export function uniqueArray<T>(array: T[], key?: keyof T): T[] {
  if (key) {
    const seen = new Set()
    return array.filter(item => {
      const value = item[key]
      if (seen.has(value)) {
        return false
      }
      seen.add(value)
      return true
    })
  }
  return [...new Set(array)]
}

/**
 * 数组分组
 * @param array 要分组的数组
 * @param key 分组的键名
 * @returns 分组后的对象
 */
export function groupArray<T>(array: T[], key: keyof T): Record<string, T[]> {
  return array.reduce(
    (groups, item) => {
      const groupKey = String(item[key])
      if (!groups[groupKey]) {
        groups[groupKey] = []
      }
      groups[groupKey].push(item)
      return groups
    },
    {} as Record<string, T[]>
  )
}

/**
 * 数组排序
 * @param array 要排序的数组
 * @param key 排序的键名
 * @param order 排序顺序
 * @returns 排序后的数组
 */
export function sortArray<T>(array: T[], key: keyof T, order: 'asc' | 'desc' = 'asc'): T[] {
  return [...array].sort((a, b) => {
    const aValue = a[key]
    const bValue = b[key]

    if (aValue < bValue) return order === 'asc' ? -1 : 1
    if (aValue > bValue) return order === 'asc' ? 1 : -1
    return 0
  })
}

// ==================== 字符串处理工具函数 ====================

/**
 * 截断字符串
 * @param str 要截断的字符串
 * @param length 最大长度
 * @param suffix 后缀
 * @returns 截断后的字符串
 */
export function truncateString(str: string, length: number, suffix: string = '...'): string {
  if (str.length <= length) return str
  return str.substring(0, length) + suffix
}

/**
 * 首字母大写
 * @param str 字符串
 * @returns 首字母大写的字符串
 */
export function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1)
}

/**
 * 驼峰转下划线
 * @param str 驼峰字符串
 * @returns 下划线字符串
 */
export function camelToSnake(str: string): string {
  return str.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`)
}

/**
 * 下划线转驼峰
 * @param str 下划线字符串
 * @returns 驼峰字符串
 */
export function snakeToCamel(str: string): string {
  return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase())
}

// ==================== 数字处理工具函数 ====================

/**
 * 格式化数字
 * @param num 数字
 * @param decimals 小数位数
 * @returns 格式化后的数字字符串
 */
export function formatNumber(num: number, decimals: number = 2): string {
  return num.toFixed(decimals)
}

/**
 * 数字千分位分隔
 * @param num 数字
 * @returns 千分位分隔的字符串
 */
export function formatNumberWithCommas(num: number): string {
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

/**
 * 限制数字范围
 * @param num 数字
 * @param min 最小值
 * @param max 最大值
 * @returns 限制后的数字
 */
export function clampNumber(num: number, min: number, max: number): number {
  return Math.min(Math.max(num, min), max)
}

// ==================== 对象处理工具函数 ====================

/**
 * 移除对象中的空值
 * @param obj 对象
 * @returns 移除空值后的对象
 */
export function removeEmptyValues<T extends Record<string, any>>(obj: T): Partial<T> {
  const result: Partial<T> = {}
  for (const [key, value] of Object.entries(obj)) {
    if (value !== null && value !== undefined && value !== '') {
      result[key as keyof T] = value
    }
  }
  return result
}

/**
 * 获取对象嵌套属性值
 * @param obj 对象
 * @param path 属性路径
 * @returns 属性值
 */
export function getNestedValue(obj: any, path: string): any {
  return path.split('.').reduce((current, key) => current?.[key], obj)
}

/**
 * 设置对象嵌套属性值
 * @param obj 对象
 * @param path 属性路径
 * @param value 属性值
 */
export function setNestedValue(obj: any, path: string, value: any): void {
  const keys = path.split('.')
  const lastKey = keys.pop()!
  const target = keys.reduce((current, key) => {
    if (!current[key]) current[key] = {}
    return current[key]
  }, obj)
  target[lastKey] = value
}

// ==================== 浏览器相关工具函数 ====================

/**
 * 检查是否为移动设备
 * @returns 是否为移动设备
 */
export function isMobile(): boolean {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
}

/**
 * 检查是否为iOS设备
 * @returns 是否为iOS设备
 */
export function isIOS(): boolean {
  return /iPad|iPhone|iPod/.test(navigator.userAgent)
}

/**
 * 检查是否为Android设备
 * @returns 是否为Android设备
 */
export function isAndroid(): boolean {
  return /Android/.test(navigator.userAgent)
}

/**
 * 复制文本到剪贴板
 * @param text 要复制的文本
 * @returns 是否复制成功
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(text)
      return true
    } else {
      // 降级方案
      const textArea = document.createElement('textarea')
      textArea.value = text
      document.body.appendChild(textArea)
      textArea.select()
      document.execCommand('copy')
      document.body.removeChild(textArea)
      return true
    }
  } catch (error) {
    console.error('复制到剪贴板失败:', error)
    return false
  }
}

/**
 * 下载文件
 * @param url 文件URL
 * @param filename 文件名
 */
export function downloadFile(url: string, filename?: string): void {
  const link = document.createElement('a')
  link.href = url
  link.download = filename || 'download'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

// ==================== 调试工具函数 ====================

/**
 * 调试日志
 * @param message 日志消息
 * @param data 日志数据
 */
export function debugLog(message: string, data?: any): void {
  if (import.meta.env.DEV) {
    console.log(`[DEBUG] ${message}`, data)
  }
}

/**
 * 性能测量
 * @param name 测量名称
 * @param fn 要测量的函数
 * @returns 函数执行结果
 */
export async function measurePerformance<T>(name: string, fn: () => T | Promise<T>): Promise<T> {
  const start = performance.now()
  const result = await fn()
  const end = performance.now()
  debugLog(`${name} 执行时间: ${end - start}ms`)
  return result
}

// ==================== 业务相关工具函数 ====================

/**
 * 获取用户显示名称
 * @param user 用户对象
 * @returns 显示名称
 */
export function getUserDisplayName(user: User): string {
  return user.username || user.email || '未知用户'
}

/**
 * 获取消息预览文本
 * @param message 消息对象
 * @param maxLength 最大长度
 * @returns 预览文本
 */
export function getMessagePreview(message: Message, maxLength: number = 50): string {
  if (message.contentType === 'text') {
    return truncateString(message.content, maxLength)
  }

  const typeMap = {
    image: '[图片]',
    audio: '[语音]',
    video: '[视频]',
    file: '[文件]',
  }

  return typeMap[message.contentType] || '[未知类型]'
}

/**
 * 检查对话是否为空
 * @param conversation 对话对象
 * @returns 是否为空
 */
export function isConversationEmpty(conversation: Conversation): boolean {
  return conversation.messageCount === 0
}

/**
 * 获取文件上传进度百分比
 * @param progress 上传进度对象
 * @returns 进度百分比
 */
export function getUploadProgressPercentage(progress: UploadProgress): number {
  return Math.round((progress.loaded / progress.total) * 100)
}

/**
 * 验证输入数据
 * @param input 输入数据
 * @returns 验证结果
 */
export function validateInputData(input: InputData): { isValid: boolean; errors: string[] } {
  const errors: string[] = []

  if (!input.content) {
    errors.push('输入内容不能为空')
  }

  if (
    input.type === 'text' &&
    typeof input.content === 'string' &&
    input.content.trim().length === 0
  ) {
    errors.push('文本内容不能为空')
  }

  if (input.type !== 'text' && input.content instanceof File) {
    if (!isSupportedFileType(input.content)) {
      errors.push('不支持的文件类型')
    }

    if (!isFileSizeValid(input.content)) {
      errors.push('文件大小超出限制')
    }
  }

  return {
    isValid: errors.length === 0,
    errors,
  }
}
