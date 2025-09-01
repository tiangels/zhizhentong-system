/**
 * 工具函数导出文件
 * 统一导出所有工具函数
 */

// 导出常量
export * from './constants'

// 导出辅助函数
export {
  setLocalStorage,
  getLocalStorage,
  removeLocalStorage,
  clearLocalStorage,
  formatDateTime,
  getRelativeTime,
  isToday,
  isYesterday,
  getTimestamp,
  formatFileSize,
  isSupportedFileType,
  isFileSizeValid,
  getFileType,
  createFileURL,
  revokeFileURL,
  isValidEmail,
  isValidPhone,
  isValidPassword,
  isValidUsername,
  isValidURL,
  deepClone,
  debounceFunc,
  throttleFunc,
  generateId,
  generateUUID,
  uniqueArray,
  groupArray,
  sortArray,
  truncateString,
  capitalize,
  camelToSnake,
  snakeToCamel,
  formatNumber,
  formatNumberWithCommas,
  clampNumber,
  removeEmptyValues,
  getNestedValue,
  setNestedValue,
  isMobile,
  isIOS,
  isAndroid,
  copyToClipboard,
  downloadFile,
  debugLog,
  measurePerformance,
  getUserDisplayName,
  getMessagePreview,
  isConversationEmpty,
  getUploadProgressPercentage,
  validateInputData,
} from './helpers'

// 导出验证函数
export { validateInputData as validateInputDataFromValidators } from './validators'
