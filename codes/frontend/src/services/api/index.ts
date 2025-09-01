/**
 * API服务主文件
 * 配置axios实例、请求拦截器、响应拦截器等
 */

import axios, {
  type AxiosInstance,
  type InternalAxiosRequestConfig,
  type AxiosResponse,
} from 'axios'
import { message } from 'ant-design-vue'
import { API_CONFIG, ERROR_MESSAGES, STORAGE_KEYS } from '../../utils/constants'
import { getLocalStorage, removeLocalStorage } from '../../utils/helpers'

/**
 * 创建axios实例
 * 配置基础URL、超时时间等
 */
const apiService: AxiosInstance = axios.create({
  baseURL: API_CONFIG.BASE_URL,
  timeout: API_CONFIG.TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
  // 确保JSON序列化正确
  transformRequest: [
    (data, _headers) => {
      console.log('🔄 Axios transformRequest - 原始数据:', data)
      console.log('🔄 Axios transformRequest - 数据类型:', typeof data)
      
      if (data && typeof data === 'object' && !(data instanceof FormData)) {
        const serialized = JSON.stringify(data)
        console.log('🔄 Axios transformRequest - 序列化后:', serialized)
        return serialized
      }
      return data
    }
  ]
})

// 添加调试信息
console.log('🚀 API Service - 创建axios实例')
console.log('🚀 API Service - 基础URL:', API_CONFIG.BASE_URL)
console.log('🚀 API Service - 超时时间:', API_CONFIG.TIMEOUT)
console.log('🚀 API Service - axios实例baseURL:', apiService.defaults.baseURL)
console.log('🚀 API Service - 环境变量:', {
  VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
  NODE_ENV: import.meta.env.NODE_ENV,
  MODE: import.meta.env.MODE,
})

/**
 * 请求拦截器
 * 在请求发送前添加token、处理请求配置等
 */
apiService.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 从本地存储获取token
    const token = getLocalStorage<string>(STORAGE_KEYS.USER_TOKEN)

    // 如果有token，添加到请求头
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // 只为GET请求添加时间戳参数，避免缓存
    if (config.method?.toLowerCase() === 'get') {
      if (config.params) {
        config.params._t = Date.now()
      } else {
        config.params = { _t: Date.now() }
      }
    }

    return config
  },
  error => {
    console.error('请求拦截器错误:', error)
    return Promise.reject(error)
  },
)

/**
 * 响应拦截器
 * 处理响应数据、错误处理、token刷新等
 */
apiService.interceptors.response.use(
  (response: AxiosResponse) => {
    // 返回响应数据，而不是整个response对象
    return response.data
  },
  async error => {
    const { response } = error

    if (response) {
      const { status, data } = response

      switch (status) {
      case 401:
        // 未授权，清除token
        const hadToken = !!getLocalStorage(STORAGE_KEYS.USER_TOKEN)
        removeLocalStorage(STORAGE_KEYS.USER_TOKEN)
        removeLocalStorage(STORAGE_KEYS.USER_INFO)

        // 只有在用户之前有token（即已登录状态）时才显示错误和跳转
        if (hadToken) {
          // 显示错误消息
          message.error(ERROR_MESSAGES.UNAUTHORIZED)
          
          // 跳转到登录页
          window.location.href = '/auth/login'
        }
        break

      case 403:
        // 禁止访问
        message.error(ERROR_MESSAGES.FORBIDDEN)
        break

      case 404:
        // 资源不存在
        message.error(ERROR_MESSAGES.NOT_FOUND)
        break

      case 422:
        // 请求参数错误
        if (data.message) {
          message.error(data.message)
        } else {
          message.error(ERROR_MESSAGES.VALIDATION_ERROR)
        }
        break

      case 429:
        // 请求频率限制
        message.error(ERROR_MESSAGES.RATE_LIMIT)
        break

      case 500:
        // 服务器内部错误
        message.error(ERROR_MESSAGES.SERVER_ERROR)
        break

      default:
        // 其他错误
        if (data.message) {
          message.error(data.message)
        } else {
          message.error(ERROR_MESSAGES.UNKNOWN_ERROR)
        }
      }
    } else if (error.code === 'ECONNABORTED') {
      // 请求超时
      message.error(ERROR_MESSAGES.TIMEOUT)
    } else if (error.message === 'Network Error') {
      // 网络错误
      message.error(ERROR_MESSAGES.NETWORK_ERROR)
    } else {
      // 其他错误
      message.error(ERROR_MESSAGES.UNKNOWN_ERROR)
    }

    return Promise.reject(error)
  },
)

/**
 * 通用请求方法
 * @param config 请求配置
 * @returns Promise<T>
 */
export const request = async <T = any>(config: any): Promise<T> => {
  console.log('API Request - 完整配置:', config)
  console.log('API Request - 基础URL:', apiService.defaults.baseURL)
  console.log('API Request - 完整URL:', `${apiService.defaults.baseURL}${config.url}`)
  console.log('API Request - 请求方法:', config.method)
  console.log('API Request - 请求头:', config.headers)

  try {
    console.log('API Request - 发送请求...')
    const response = await apiService(config)
    console.log('API Request - 响应数据:', response)
    console.log('API Request - 响应类型:', typeof response)

    // 响应拦截器已经返回了response.data，所以这里直接返回
    return response as T
  } catch (error: any) {
    console.error('API Request - 请求失败:', error)
    console.error('API Request - 错误详情:', {
      message: error.message,
      status: error.response?.status,
      data: error.response?.data,
      config: error.config,
      isAxiosError: error.isAxiosError,
      code: error.code,
    })

    // 如果是网络错误，提供更友好的错误信息
    if (error.code === 'ERR_NETWORK') {
      throw new Error('网络连接失败，请检查网络设置和后端服务状态')
    }

    // 如果是超时错误
    if (error.code === 'ECONNABORTED') {
      throw new Error('请求超时，请稍后重试')
    }

    throw error
  }
}

/**
 * GET请求
 * @param url 请求URL
 * @param params 请求参数
 * @param config 其他配置
 * @returns Promise<T>
 */
export const get = async <T = any>(url: string, params?: any, config?: any): Promise<T> => {
  return request<T>({
    method: 'GET',
    url,
    params,
    ...config,
  })
}

/**
 * POST请求
 * @param url 请求URL
 * @param data 请求数据
 * @param config 其他配置
 * @returns Promise<T>
 */
export const post = async <T = any>(url: string, data?: any, config?: any): Promise<T> => {
  console.log('API Post - 请求URL:', url)
  console.log('API Post - 请求数据:', data)
  console.log('API Post - 数据类型:', typeof data)
  console.log('API Post - 请求配置:', config)

  // 确保JSON数据正确序列化
  let processedData = data
  if (data && typeof data === 'object' && !(data instanceof FormData)) {
    // 对于普通对象，确保正确序列化
    processedData = data
    console.log('API Post - 处理后的数据:', processedData)
  }

  try {
    const response = await request<T>({
      method: 'POST',
      url,
      data: processedData,
      ...config,
    })
    console.log('API Post - 响应数据:', response)
    return response
  } catch (error) {
    console.error('API Post - 请求失败:', error)
    throw error
  }
}

/**
 * PUT请求
 * @param url 请求URL
 * @param data 请求数据
 * @param config 其他配置
 * @returns Promise<T>
 */
export const put = async <T = any>(url: string, data?: any, config?: any): Promise<T> => {
  return request<T>({
    method: 'PUT',
    url,
    data,
    ...config,
  })
}

/**
 * DELETE请求
 * @param url 请求URL
 * @param config 其他配置
 * @returns Promise<T>
 */
export const del = async <T = any>(url: string, config?: any): Promise<T> => {
  return request<T>({
    method: 'DELETE',
    url,
    ...config,
  })
}

/**
 * 文件上传
 * @param url 上传URL
 * @param file 文件对象
 * @param onProgress 进度回调
 * @param config 其他配置
 * @returns Promise<T>
 */
export const upload = async <T = any>(
  url: string,
  file: File,
  onProgress?: (progress: number) => void,
  config?: any,
): Promise<T> => {
  const formData = new FormData()
  formData.append('file', file)

  return request<T>({
    method: 'POST',
    url,
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent: any) => {
      if (onProgress && progressEvent.total) {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        onProgress(progress)
      }
    },
    ...config,
  })
}

// 导出axios实例
export { apiService }

// 导出默认实例
export default apiService
