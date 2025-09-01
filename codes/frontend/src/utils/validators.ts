/**
 * 智诊通前端系统验证函数
 * 提供各种数据验证功能
 */

import type {
  LoginRequest,
  RegisterRequest,
  UserProfile,
  InputData,
  ValidationError,
} from '@/types'
import { REGEX } from './constants'

// ==================== 基础验证函数 ====================

/**
 * 验证必填字段
 * @param value 要验证的值
 * @param fieldName 字段名称
 * @returns 验证结果
 */
export function validateRequired(value: any, fieldName: string): ValidationError | null {
  if (value === null || value === undefined || value === '') {
    return {
      field: fieldName,
      message: `${fieldName}不能为空`,
      value,
    }
  }
  return null
}

/**
 * 验证字符串长度
 * @param value 要验证的字符串
 * @param fieldName 字段名称
 * @param min 最小长度
 * @param max 最大长度
 * @returns 验证结果
 */
export function validateStringLength(
  value: string,
  fieldName: string,
  min: number,
  max: number
): ValidationError | null {
  if (value.length < min) {
    return {
      field: fieldName,
      message: `${fieldName}长度不能少于${min}个字符`,
      value,
    }
  }

  if (value.length > max) {
    return {
      field: fieldName,
      message: `${fieldName}长度不能超过${max}个字符`,
      value,
    }
  }

  return null
}

/**
 * 验证正则表达式
 * @param value 要验证的值
 * @param regex 正则表达式
 * @param fieldName 字段名称
 * @param message 错误消息
 * @returns 验证结果
 */
export function validateRegex(
  value: string,
  regex: RegExp,
  fieldName: string,
  message: string
): ValidationError | null {
  if (!regex.test(value)) {
    return {
      field: fieldName,
      message,
      value,
    }
  }
  return null
}

/**
 * 验证数值范围
 * @param value 要验证的数值
 * @param fieldName 字段名称
 * @param min 最小值
 * @param max 最大值
 * @returns 验证结果
 */
export function validateNumberRange(
  value: number,
  fieldName: string,
  min: number,
  max: number
): ValidationError | null {
  if (value < min || value > max) {
    return {
      field: fieldName,
      message: `${fieldName}必须在${min}到${max}之间`,
      value,
    }
  }
  return null
}

// ==================== 用户相关验证函数 ====================

/**
 * 验证用户名
 * @param username 用户名
 * @returns 验证结果
 */
export function validateUsername(username: string): ValidationError | null {
  // 必填验证
  const requiredError = validateRequired(username, '用户名')
  if (requiredError) return requiredError

  // 长度验证
  const lengthError = validateStringLength(username, '用户名', 3, 20)
  if (lengthError) return lengthError

  // 格式验证
  const formatError = validateRegex(
    username,
    REGEX.USERNAME,
    '用户名',
    '用户名只能包含字母、数字和下划线'
  )
  if (formatError) return formatError

  return null
}

/**
 * 验证邮箱
 * @param email 邮箱地址
 * @returns 验证结果
 */
export function validateEmail(email: string): ValidationError | null {
  // 必填验证
  const requiredError = validateRequired(email, '邮箱')
  if (requiredError) return requiredError

  // 格式验证
  const formatError = validateRegex(email, REGEX.EMAIL, '邮箱', '请输入有效的邮箱地址')
  if (formatError) return formatError

  return null
}

/**
 * 验证密码
 * @param password 密码
 * @returns 验证结果
 */
export function validatePassword(password: string): ValidationError | null {
  // 必填验证
  const requiredError = validateRequired(password, '密码')
  if (requiredError) return requiredError

  // 长度验证
  const lengthError = validateStringLength(password, '密码', 8, 50)
  if (lengthError) return lengthError

  // 强度验证
  const strengthError = validateRegex(
    password,
    REGEX.PASSWORD,
    '密码',
    '密码必须包含大小写字母和数字，长度至少8位'
  )
  if (strengthError) return strengthError

  return null
}

/**
 * 验证确认密码
 * @param password 密码
 * @param confirmPassword 确认密码
 * @returns 验证结果
 */
export function validateConfirmPassword(
  password: string,
  confirmPassword: string
): ValidationError | null {
  // 必填验证
  const requiredError = validateRequired(confirmPassword, '确认密码')
  if (requiredError) return requiredError

  // 一致性验证
  if (password !== confirmPassword) {
    return {
      field: 'confirmPassword',
      message: '两次输入的密码不一致',
      value: confirmPassword,
    }
  }

  return null
}

/**
 * 验证手机号
 * @param phone 手机号
 * @returns 验证结果
 */
export function validatePhone(phone: string): ValidationError | null {
  // 必填验证
  const requiredError = validateRequired(phone, '手机号')
  if (requiredError) return requiredError

  // 格式验证
  const formatError = validateRegex(phone, REGEX.PHONE, '手机号', '请输入有效的手机号码')
  if (formatError) return formatError

  return null
}

// ==================== 登录注册验证函数 ====================

/**
 * 验证登录凭据
 * @param credentials 登录凭据
 * @returns 验证结果数组
 */
export function validateLoginCredentials(credentials: LoginRequest): ValidationError[] {
  const errors: ValidationError[] = []

  // 验证用户名
  const usernameError = validateUsername(credentials.username)
  if (usernameError) errors.push(usernameError)

  // 验证密码
  const passwordError = validatePassword(credentials.password)
  if (passwordError) errors.push(passwordError)

  return errors
}

/**
 * 验证注册数据
 * @param data 注册数据
 * @returns 验证结果数组
 */
export function validateRegisterData(data: RegisterRequest): ValidationError[] {
  const errors: ValidationError[] = []

  // 验证用户名
  const usernameError = validateUsername(data.username)
  if (usernameError) errors.push(usernameError)

  // 验证邮箱
  const emailError = validateEmail(data.email)
  if (emailError) errors.push(emailError)

  // 验证密码
  const passwordError = validatePassword(data.password)
  if (passwordError) errors.push(passwordError)

  // 验证确认密码
  const confirmPasswordError = validateConfirmPassword(data.password, data.confirmPassword)
  if (confirmPasswordError) errors.push(confirmPasswordError)

  // 验证用户协议
  if (!data.agreeToTerms) {
    errors.push({
      field: 'agreeToTerms',
      message: '请同意用户协议和隐私政策',
      value: data.agreeToTerms,
    })
  }

  return errors
}

// ==================== 用户档案验证函数 ====================

/**
 * 验证用户档案
 * @param profile 用户档案
 * @returns 验证结果数组
 */
export function validateUserProfile(profile: Partial<UserProfile>): ValidationError[] {
  const errors: ValidationError[] = []

  // 验证真实姓名
  if (profile.realName) {
    const nameError = validateStringLength(profile.realName, '真实姓名', 2, 20)
    if (nameError) errors.push(nameError)
  }

  // 验证年龄
  if (profile.age !== undefined) {
    const ageError = validateNumberRange(profile.age, '年龄', 1, 120)
    if (ageError) errors.push(ageError)
  }

  // 验证身高
  // if (profile.height !== undefined) {
  //   const heightError = validateNumberRange(profile.height, '身高', 50, 250)
  //   if (heightError) errors.push(heightError)
  // }

  // 验证体重
  // if (profile.weight !== undefined) {
  //   const weightError = validateNumberRange(profile.weight, '体重', 1, 300)
  //   if (weightError) errors.push(weightError)
  // }

  // 验证紧急联系人
  if (profile.emergencyContact) {
    const { name, phone, relationship } = profile.emergencyContact

    if (name) {
      const nameError = validateStringLength(name, '紧急联系人姓名', 2, 20)
      if (nameError) errors.push(nameError)
    }

    if (phone) {
      const phoneError = validatePhone(phone)
      if (phoneError) errors.push(phoneError)
    }

    if (relationship) {
      const relationshipError = validateStringLength(relationship, '关系', 2, 10)
      if (relationshipError) errors.push(relationshipError)
    }
  }

  return errors
}

// ==================== 输入数据验证函数 ====================

/**
 * 验证输入数据
 * @param input 输入数据
 * @returns 验证结果数组
 */
export function validateInputData(input: InputData): ValidationError[] {
  const errors: ValidationError[] = []

  // 验证内容不为空
  const contentError = validateRequired(input.content, '输入内容')
  if (contentError) errors.push(contentError)

  // 根据类型进行特定验证
  switch (input.type) {
    case 'text':
      if (typeof input.content === 'string') {
        const textError = validateStringLength(input.content, '文本内容', 1, 10000)
        if (textError) errors.push(textError)
      }
      break

    case 'image':
    case 'audio':
    case 'video':
    case 'file':
      if (input.content instanceof File) {
        // 验证文件大小
        const maxSize = getMaxFileSize(input.type)
        if (input.content.size > maxSize) {
          errors.push({
            field: 'content',
            message: `文件大小不能超过${formatFileSize(maxSize)}`,
            value: input.content,
          })
        }

        // 验证文件类型
        const allowedTypes = getAllowedFileTypes(input.type)
        if (!allowedTypes.includes(input.content.type)) {
          errors.push({
            field: 'content',
            message: `不支持的文件类型: ${input.content.type}`,
            value: input.content,
          })
        }
      }
      break
  }

  return errors
}

/**
 * 获取文件类型对应的最大文件大小
 * @param type 文件类型
 * @returns 最大文件大小（字节）
 */
function getMaxFileSize(type: string): number {
  const sizeMap = {
    image: 5 * 1024 * 1024, // 5MB
    audio: 10 * 1024 * 1024, // 10MB
    video: 50 * 1024 * 1024, // 50MB
    file: 10 * 1024 * 1024, // 10MB
  }
  return sizeMap[type as keyof typeof sizeMap] || 10 * 1024 * 1024
}

/**
 * 获取文件类型对应的允许的文件类型
 * @param type 文件类型
 * @returns 允许的文件类型数组
 */
function getAllowedFileTypes(type: string): string[] {
  const typeMap = {
    image: ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp'],
    audio: ['audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/m4a', 'audio/aac'],
    video: ['video/mp4', 'video/webm', 'video/ogg', 'video/avi', 'video/mov'],
    file: [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain',
    ],
  }
  return typeMap[type as keyof typeof typeMap] || []
}

/**
 * 格式化文件大小
 * @param bytes 字节数
 * @returns 格式化后的文件大小
 */
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'

  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return parseFloat((bytes / k ** i).toFixed(2)) + ' ' + sizes[i]
}

// ==================== 通用验证函数 ====================

/**
 * 验证对象的所有字段
 * @param obj 要验证的对象
 * @param validators 验证器映射
 * @returns 验证结果数组
 */
export function validateObject<T>(
  obj: T,
  validators: Record<keyof T, (value: any) => ValidationError | null>
): ValidationError[] {
  const errors: ValidationError[] = []

  for (const [field, validator] of Object.entries(validators)) {
    const error = (validator as any)(obj[field as keyof T])
    if (error) {
      error.field = field
      errors.push(error)
    }
  }

  return errors
}

/**
 * 验证数组中的每个元素
 * @param array 要验证的数组
 * @param validator 验证器函数
 * @returns 验证结果数组
 */
export function validateArray<T>(
  array: T[],
  validator: (item: T, index: number) => ValidationError | null
): ValidationError[] {
  const errors: ValidationError[] = []

  array.forEach((item, index) => {
    const error = validator(item, index)
    if (error) {
      error.field = `array[${index}]`
      errors.push(error)
    }
  })

  return errors
}

/**
 * 组合多个验证器
 * @param validators 验证器数组
 * @returns 组合后的验证器
 */
export function combineValidators<T>(
  ...validators: ((value: T) => ValidationError | null)[]
): (value: T) => ValidationError | null {
  return (value: T) => {
    for (const validator of validators) {
      const error = validator(value)
      if (error) return error
    }
    return null
  }
}

// ==================== 验证工具函数 ====================

/**
 * 检查验证结果是否有效
 * @param errors 验证错误数组
 * @returns 是否有效
 */
export function isValid(errors: ValidationError[]): boolean {
  return errors.length === 0
}

/**
 * 获取第一个验证错误
 * @param errors 验证错误数组
 * @returns 第一个错误或null
 */
export function getFirstError(errors: ValidationError[]): ValidationError | null {
  return errors.length > 0 ? errors[0] : null
}

/**
 * 获取指定字段的验证错误
 * @param errors 验证错误数组
 * @param field 字段名
 * @returns 字段错误或null
 */
export function getFieldError(errors: ValidationError[], field: string): ValidationError | null {
  return errors.find(error => error.field === field) || null
}

/**
 * 清除指定字段的验证错误
 * @param errors 验证错误数组
 * @param field 字段名
 * @returns 清除后的错误数组
 */
export function clearFieldError(errors: ValidationError[], field: string): ValidationError[] {
  return errors.filter(error => error.field !== field)
}
