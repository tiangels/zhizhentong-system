<script setup lang="ts">
import { ref, nextTick, onMounted, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useChatStore } from '../../stores/chat'
import { useAuthStore } from '../../stores/auth'
import { multimodalApi } from '../../services/apiService'

// 接收路由参数
interface Props {
  id?: string
}

const props = defineProps<Props>()

const route = useRoute()
const chatStore = useChatStore()
const authStore = useAuthStore()

// 输入消息
const inputMessage = ref('')
const messagesContainer = ref<HTMLElement>()

// 统一多模态输入相关状态
const selectedImages = ref<File[]>([])
const selectedAudio = ref<File | null>(null)
const isRecording = ref(false)
const mediaRecorder = ref<MediaRecorder | null>(null)
const audioChunks = ref<Blob[]>([])
const audioPreviewUrl = ref<string | null>(null)
const isUploading = ref(false)
const isProcessingVoice = ref(false)
const hoveredImageIndex = ref(-1)

// 标题编辑相关状态
const isEditingTitle = ref(false)
const editingTitle = ref('')
const titleInput = ref<HTMLInputElement>()

// 计算属性：图片预览URLs
const imagePreviewUrls = computed(() => {
  return selectedImages.value.map(file => URL.createObjectURL(file))
})

// 计算属性：当前对话标题
const currentConversationTitle = computed(() => {
  return chatStore.currentConversation?.title || '新对话'
})

// 快速操作按钮
const quickActions = [
  { id: 1, text: '我最近总是头痛' },
  { id: 2, text: '我感冒了，有什么建议？' },
  { id: 3, text: '我睡眠质量不好' },
  { id: 4, text: '我想了解健康饮食' },
]

// 创建用户消息（立即显示，不等待多模态处理）
const createUserMessageImmediate = (hasText: boolean, hasImage: boolean, hasAudio: boolean) => {
  // 对于立即显示的消息，使用blob URL作为临时预览
  // 实际的消息会在多模态处理完成后更新为服务器URL
  const currentImagePreviewUrls = selectedImages.value.map(img => URL.createObjectURL(img))

  let content = ''
  let type = 'text'
  let data: Record<string, any> = { content_type: 'text' }

  if (hasText && hasImage && hasAudio && selectedAudio.value) {
    // 文字+图片+语音
    content = inputMessage.value.trim()
    type = 'multimodal'
    data = {
      content_type: 'text_image_audio',
      text: inputMessage.value.trim(),
      original_filename: {
        images: selectedImages.value.map(img => img.name),
        audio: selectedAudio.value.name,
      },
      image_preview_urls: currentImagePreviewUrls,
      audio_preview_url: audioPreviewUrl.value,
      processing_status: 'pending',
    }
  } else if (hasText && hasImage) {
    // 文字+图片
    content = inputMessage.value.trim()
    type = 'multimodal'
    data = {
      content_type: 'text_image',
      text: inputMessage.value.trim(),
      original_filename: selectedImages.value.map(img => img.name),
      image_preview_urls: currentImagePreviewUrls,
      processing_status: 'pending',
    }
  } else if (hasText && hasAudio && selectedAudio.value) {
    // 文字+语音
    content = inputMessage.value.trim()
    type = 'multimodal'
    data = {
      content_type: 'text_audio',
      text: inputMessage.value.trim(),
      original_filename: selectedAudio.value.name,
      audio_preview_url: audioPreviewUrl.value,
      processing_status: 'pending',
    }
  } else if (hasImage && hasAudio && selectedAudio.value) {
    // 图片+语音
    content = ''
    type = 'multimodal'
    data = {
      content_type: 'image_audio',
      original_filename: {
        images: selectedImages.value.map(img => img.name),
        audio: selectedAudio.value.name,
      },
      image_preview_urls: currentImagePreviewUrls,
      audio_preview_url: audioPreviewUrl.value,
      processing_status: 'pending',
    }
  } else if (hasText) {
    // 纯文字
    content = inputMessage.value.trim()
    type = 'text'
    data = { content_type: 'text' }
  } else if (hasImage) {
    // 纯图片
    content = ''
    type = 'image'
    data = {
      content_type: 'image',
      original_filename: selectedImages.value.map(img => img.name),
      image_preview_urls: currentImagePreviewUrls,
      processing_status: 'pending',
    }
  } else if (hasAudio && selectedAudio.value) {
    // 纯语音
    content = ''
    type = 'audio'
    data = {
      content_type: 'audio',
      original_filename: selectedAudio.value.name,
      audio_preview_url: audioPreviewUrl.value,
      processing_status: 'pending',
    }
  }

  return { content, type, data }
}

// 异步处理多模态内容
const processMultimodalContentAsync = async (
  userMessage: {
    content: string
    type: string
    data: Record<string, any>
  },
  savedImages: File[],
  savedAudio: File | null
) => {
  try {
    console.log('开始异步处理多模态内容...')

    // 正确检测多模态内容
    const hasText = !!userMessage.data.text || !!userMessage.content?.trim()
    const hasImage = savedImages.length > 0
    const hasAudio = !!savedAudio

    console.log('统一多模态处理:', { hasText, hasImage, hasAudio })

    // 调用多模态API处理
    const result = await handleMultimodalInputWithFiles(
      hasText,
      hasImage,
      hasAudio,
      savedImages,
      savedAudio
    )

    if (result) {
      // 更新消息数据（移除processing_status，添加处理结果）
      const updatedData: Record<string, any> = {
        ...userMessage.data,
        ...result.messageData,
        processing_status: 'completed',
      }

      // 更新消息中的图片URL为服务器URL
      if (result.messageData.image_preview_urls) {
        updatedData.image_preview_urls = result.messageData.image_preview_urls
      }

      // 找到并更新对应的消息
      const messageToUpdate = chatStore.currentMessages.find(
        msg =>
          msg.messageData &&
          msg.messageData.processing_status === 'pending' &&
          JSON.stringify(msg.messageData.image_preview_urls) ===
            JSON.stringify(userMessage.data.image_preview_urls)
      )

      if (messageToUpdate) {
        chatStore.updateMessage(messageToUpdate.id, {
          messageData: updatedData,
        })
        console.log('消息已更新为服务器URL:', messageToUpdate.id)
      }

      console.log('多模态处理完成:', updatedData)

      // 触发AI回答生成
      await generateAIResponse(updatedData)
    }
  } catch (error) {
    console.error('异步多模态处理失败:', error)
    // 可以更新消息状态为失败
  }
}

// 生成AI回答
const generateAIResponse = async (messageData: Record<string, any>) => {
  try {
    // 这里调用AI回答生成API
    console.log('生成AI回答，基于消息数据:', messageData)
    // 实际实现中，这里会调用chatStore的相关方法
  } catch (error) {
    console.error('生成AI回答失败:', error)
  }
}

// 发送消息 - 异步多模态处理
const sendMessage = async () => {
  if (chatStore.isLoading || isUploading.value || isProcessingVoice.value) return

  // 检查用户是否已登录
  if (!authStore.isLoggedIn) {
    console.error('用户未登录，无法发送消息')
    return
  }

  // 检查是否有任何输入
  const hasText = !!inputMessage.value.trim()
  const hasImage = selectedImages.value.length > 0
  const hasAudio = !!selectedAudio.value

  if (!hasText && !hasImage && !hasAudio) return

  try {
    // 如果没有当前对话，先创建一个新对话
    if (!chatStore.currentConversation) {
      console.log('创建新对话用于发送消息')
      await chatStore.createConversation({
        title: '新对话',
        type: 'diagnosis',
      })
    }

    // 确保有当前对话
    if (!chatStore.currentConversation) {
      console.error('创建对话失败，无法发送消息')
      return
    }

    // 1. 保存文件数据用于异步处理
    const savedImages = [...selectedImages.value]
    const savedAudio = selectedAudio.value

    // 2. 立即创建用户消息（不等待多模态处理）
    const userMessage = createUserMessageImmediate(hasText, hasImage, hasAudio)

    // 3. 立即清空输入（用户立即看到反馈）
    inputMessage.value = ''
    selectedImages.value = []
    selectedAudio.value = null
    audioChunks.value = []

    // 4. 立即显示用户消息
    await chatStore.sendMessageStream({
      content: userMessage.content,
      type: 'user',
      conversationId: chatStore.currentConversation.id,
      messageType: userMessage.type,
      messageData: userMessage.data,
    })

    // 5. 后台异步处理多模态内容（如果有图片或语音）
    if (hasImage || hasAudio) {
      processMultimodalContentAsync(userMessage, savedImages, savedAudio)
    }

    // 滚动到底部
    await nextTick()
    scrollToBottom()
  } catch (error) {
    console.error('发送消息失败:', error)
  } finally {
    isUploading.value = false
  }
}

// 统一多模态输入处理（带文件参数）
const handleMultimodalInputWithFiles = async (
  hasText: boolean,
  hasImage: boolean,
  hasAudio: boolean,
  imageFiles: File[],
  audioFile: File | null
) => {
  let messageContent = ''
  let messageType = 'text'
  let messageData: Record<string, unknown> = {}

  try {
    // 构建统一的多模态请求
    const requestData: Record<string, unknown> = {}

    if (hasText) {
      requestData.text = inputMessage.value.trim()
    }
    if (hasImage) {
      requestData.imageFiles = imageFiles
    }
    if (hasAudio && audioFile) {
      requestData.audioFile = audioFile
    }

    // 调用统一的多模态API
    const result = await multimodalApi.processUnified(requestData)
    console.log('统一多模态处理结果:', result)

    // 根据输入类型构建消息内容
    // 优先使用服务器返回的URL，如果没有则使用blob URL作为预览
    const getImageUrls = () => {
      if (result.data.image_result && result.data.image_result.files) {
        // 使用服务器返回的URL
        return result.data.image_result.files.map((file: any) => file.url)
      } else if (result.data.image_result && result.data.image_result.url) {
        // 单个图片的URL
        return [result.data.image_result.url]
      } else {
        // 回退到blob URL
        return imageFiles.map(img => URL.createObjectURL(img))
      }
    }

    const currentImagePreviewUrls = getImageUrls()

    if (hasText && hasImage && hasAudio && audioFile) {
      // 文字+图片+语音
      messageContent = inputMessage.value.trim()
      messageType = 'multimodal'
      messageData = {
        content_type: 'text_image_audio',
        text: inputMessage.value.trim(),
        image_result: {
          files: currentImagePreviewUrls.map((url, index) => ({
            url,
            filename: imageFiles[index]?.name || `图片${index + 1}`,
          })),
        },
        audio_result: {
          url: result.data.audio_result?.url || URL.createObjectURL(audioFile),
          filename: audioFile.name,
        },
      }
    } else if (hasText && hasImage) {
      // 文字+图片
      messageContent = inputMessage.value.trim()
      messageType = 'multimodal'
      messageData = {
        content_type: 'text_image',
        text: inputMessage.value.trim(),
        image_result: {
          files: currentImagePreviewUrls.map((url, index) => ({
            url,
            filename: imageFiles[index]?.name || `图片${index + 1}`,
          })),
        },
      }
    } else if (hasText && hasAudio && audioFile) {
      // 文字+语音
      messageContent = inputMessage.value.trim()
      messageType = 'multimodal'
      messageData = {
        content_type: 'text_audio',
        text: inputMessage.value.trim(),
        audio_result: {
          url: result.data.audio_result?.url || URL.createObjectURL(audioFile),
          filename: audioFile.name,
        },
      }
    } else if (hasImage) {
      // 仅图片
      messageContent = '发送了图片'
      messageType = 'multimodal'
      messageData = {
        content_type: 'image',
        image_result: {
          files: currentImagePreviewUrls.map((url, index) => ({
            url,
            filename: imageFiles[index]?.name || `图片${index + 1}`,
          })),
        },
      }
    } else if (hasAudio && audioFile) {
      // 仅语音
      messageContent = '发送了语音'
      messageType = 'multimodal'
      messageData = {
        content_type: 'audio',
        audio_result: {
          url: result.data.audio_result?.url || URL.createObjectURL(audioFile),
          filename: audioFile.name,
        },
      }
    } else {
      // 仅文字
      messageContent = inputMessage.value.trim()
      messageType = 'text'
      messageData = {
        content_type: 'text',
        text: inputMessage.value.trim(),
      }
    }

    return {
      content: messageContent,
      type: messageType,
      messageData,
    }
  } catch (error) {
    console.error('多模态处理失败:', error)
    return null
  }
}

// 统一多模态输入处理（兼容旧版本）
const handleMultimodalInput = async (hasText: boolean, hasImage: boolean, hasAudio: boolean) => {
  let messageContent = ''
  let messageType = 'text'
  let messageData: Record<string, unknown> = {}

  try {
    // 构建统一的多模态请求
    const requestData: Record<string, unknown> = {}

    if (hasText) {
      requestData.text = inputMessage.value.trim()
    }
    if (hasImage) {
      requestData.imageFiles = selectedImages.value
    }
    if (hasAudio && selectedAudio.value) {
      requestData.audioFile = selectedAudio.value
    }

    // 调用统一的多模态API
    const result = await multimodalApi.processUnified(requestData)
    console.log('统一多模态处理结果:', result)

    // 根据输入类型构建消息内容
    // 优先使用服务器返回的URL，如果没有则使用blob URL作为预览
    const getImageUrls = () => {
      if (result.data.image_result && result.data.image_result.files) {
        // 使用服务器返回的URL
        return result.data.image_result.files.map((file: any) => file.url)
      } else if (result.data.image_result && result.data.image_result.url) {
        // 单个图片的URL
        return [result.data.image_result.url]
      } else {
        // 回退到blob URL
        return selectedImages.value.map(img => URL.createObjectURL(img))
      }
    }

    const currentImagePreviewUrls = getImageUrls()

    if (hasText && hasImage && hasAudio && selectedAudio.value) {
      // 文字+图片+语音
      messageContent = inputMessage.value.trim()
      messageType = 'multimodal'
      messageData = {
        content_type: 'text_image_audio',
        text: inputMessage.value.trim(),
        image_result: {
          ...result.data.image_result,
          original_filename: selectedImages.value.map(img => img.name),
        },
        audio_result: result.data.audio_result,
        original_filename: {
          images: selectedImages.value.map(img => img.name),
          audio: selectedAudio.value.name,
        },
        image_preview_urls: currentImagePreviewUrls,
      }
    } else if (hasText && hasImage) {
      // 文字+图片
      messageContent = inputMessage.value.trim()
      messageType = 'multimodal'
      messageData = {
        content_type: 'text_image',
        text: inputMessage.value.trim(),
        image_result: {
          ...result.data.image_result,
          original_filename: selectedImages.value.map(img => img.name),
        },
        image_preview_urls: currentImagePreviewUrls,
      }
    } else if (hasText && hasAudio && selectedAudio.value) {
      // 文字+语音
      messageContent = inputMessage.value.trim()
      messageType = 'multimodal'
      messageData = {
        content_type: 'text_audio',
        text: inputMessage.value.trim(),
        audio_result: result.data.audio_result,
        original_filename: selectedAudio.value.name,
      }
    } else if (hasImage && hasAudio && selectedAudio.value) {
      // 图片+语音
      messageContent = ''
      messageType = 'multimodal'
      messageData = {
        content_type: 'image_audio',
        image_result: {
          ...result.data.image_result,
          original_filename: selectedImages.value.map(img => img.name),
        },
        audio_result: result.data.audio_result,
        original_filename: {
          images: selectedImages.value.map(img => img.name),
          audio: selectedAudio.value.name,
        },
        image_preview_urls: currentImagePreviewUrls,
      }
    } else if (hasText) {
      // 纯文字
      messageContent = inputMessage.value.trim()
      messageType = 'text'
      messageData = { content_type: 'text' }
    } else if (hasImage) {
      // 纯图片
      messageContent = ''
      messageType = 'image'
      messageData = {
        content_type: 'image',
        image_result: {
          ...result.data.image_result,
          original_filename: selectedImages.value.map(img => img.name),
        },
        image_preview_urls: currentImagePreviewUrls,
      }
    } else if (hasAudio && selectedAudio.value) {
      // 纯语音
      messageContent = ''
      messageType = 'audio'
      messageData = {
        content_type: 'audio',
        audio_result: result.data.audio_result,
        original_filename: selectedAudio.value.name,
      }
    }

    return {
      messageContent,
      messageType,
      messageData,
    }
  } catch (error) {
    console.error('多模态处理失败:', error)
    return null
  }
}

// 语音转文字并自动发送
const processVoiceAndSend = async (audioFile: File) => {
  try {
    isProcessingVoice.value = true

    // 调用统一的多模态API进行语音转文字
    const result = await multimodalApi.processUnified({ audioFile })
    console.log('语音转文字结果:', result)

    // 将转换后的文字显示在输入框中
    const transcription =
      result.data?.audio_result?.transcription || result.data?.transcription || ''
    if (transcription) {
      inputMessage.value = transcription

      // 自动发送消息
      await sendMessage()
    } else {
      console.error('语音转文字失败')
    }
  } catch (error) {
    console.error('语音处理失败:', error)
  } finally {
    isProcessingVoice.value = false
  }
}

// 发送快速消息
const sendQuickMessage = async (text: string) => {
  inputMessage.value = text
  await sendMessage()
}

// 开始新对话
// 标题编辑相关方法
const startEditTitle = async () => {
  isEditingTitle.value = true
  editingTitle.value = currentConversationTitle.value
  await nextTick()
  titleInput.value?.focus()
  titleInput.value?.select()
}

const saveTitle = async () => {
  if (!chatStore.currentConversation) return

  const newTitle = editingTitle.value.trim()
  if (newTitle && newTitle !== currentConversationTitle.value) {
    try {
      await chatStore.updateConversationTitle(chatStore.currentConversation.id, newTitle)
    } catch (error) {
      console.error('更新标题失败:', error)
    }
  }

  isEditingTitle.value = false
}

const cancelEditTitle = () => {
  isEditingTitle.value = false
  editingTitle.value = ''
}

const startNewConversation = async () => {
  try {
    console.log('开始新对话')

    // 如果当前有对话且有消息，确保它被保存到历史中
    if (chatStore.currentConversation && chatStore.currentMessages.length > 0) {
      console.log('保存当前对话到历史:', chatStore.currentConversation.id)
      // 当前对话会在创建新对话时自动保存到conversations列表中
    }

    await chatStore.createConversation({
      title: '新对话',
      type: 'diagnosis',
    })

    // 清空输入框
    inputMessage.value = ''

    // 滚动到底部
    await nextTick()
    scrollToBottom()
  } catch (error) {
    console.error('创建新对话失败:', error)
  }
}

// 处理回车键
const handleEnterKey = (event: KeyboardEvent) => {
  if (event.shiftKey) {
    // Shift + Enter 换行
    return
  }
  // Enter 发送
  sendMessage()
}

// 处理图片选择
const handleImageSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    // 支持多张图片选择
    const newImages = Array.from(target.files)
    selectedImages.value = [...selectedImages.value, ...newImages]
  }
  // 清空input的value，确保可以重新选择同一张图片
  target.value = ''
}

// 删除图片
const removeImage = (index: number) => {
  selectedImages.value.splice(index, 1)
}

// 开始录音
const startRecording = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    mediaRecorder.value = new MediaRecorder(stream)
    audioChunks.value = []

    mediaRecorder.value.ondataavailable = event => {
      if (event.data.size > 0) {
        audioChunks.value.push(event.data)
      }
    }

    mediaRecorder.value.onstop = () => {
      const audioBlob = new Blob(audioChunks.value, { type: 'audio/wav' })
      const audioFile = new File([audioBlob], 'recording.wav', { type: 'audio/wav' })

      // 直接处理录音并自动发送
      processVoiceAndSend(audioFile)
    }

    mediaRecorder.value.start()
    isRecording.value = true
  } catch (error) {
    console.error('无法访问麦克风:', error)
    alert('无法访问麦克风，请检查权限设置')
  }
}

// 停止录音
const stopRecording = () => {
  if (mediaRecorder.value && isRecording.value) {
    mediaRecorder.value.stop()
    isRecording.value = false

    // 停止所有音频轨道
    if (mediaRecorder.value.stream) {
      mediaRecorder.value.stream.getTracks().forEach(track => track.stop())
    }
  }
}

// 滚动到底部
const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 格式化时间
const formatTime = (timestamp: string) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  })
}

// 只返回文本内容，不处理图片
const parseMessageContent = (message: any) => {
  if (!message) return ''
  return message.content || ''
}

// 获取消息中的图片数据
const getMessageImages = (message: any) => {
  if (!message || !message.messageData) {
    console.log('getMessageImages: 消息或messageData为空', {
      message,
      messageData: message?.messageData,
    })
    return []
  }

  const messageData = message.messageData
  console.log('getMessageImages: 处理消息数据', {
    messageId: message.id,
    contentType: messageData.content_type,
    imageFiles: messageData.image_files,
    messageData: messageData,
  })
  let images: Array<{ url: string; filename: string }> = []

  // 处理包含图片的各种情况
  if (
    messageData.content_type === 'text_image' ||
    messageData.content_type === 'image' ||
    messageData.content_type === 'text_image_audio' ||
    messageData.content_type === 'image_audio' ||
    messageData.content_type === 'multimodal'
  ) {
    // 优先处理新的数据结构：image_files
    if (
      messageData.image_files &&
      Array.isArray(messageData.image_files) &&
      messageData.image_files.length > 0
    ) {
      console.log('getMessageImages: 处理image_files数据', messageData.image_files)
      images = messageData.image_files.map((file: any) => ({
        url: getImagePreviewUrl(file.filename, messageData),
        filename: file.filename || `图片${images.length + 1}`,
      }))
    }
    // 处理image_result.files数据结构（主要的数据结构）
    else if (
      messageData.image_result &&
      messageData.image_result.files &&
      Array.isArray(messageData.image_result.files) &&
      messageData.image_result.files.length > 0
    ) {
      console.log('getMessageImages: 处理image_result.files数据', messageData.image_result.files)
      images = messageData.image_result.files.map((file: any) => ({
        url: file.url || getImagePreviewUrl(file.filename, messageData),
        filename: file.filename || `图片${images.length + 1}`,
      }))
    }
    // 处理旧的数据结构：image_preview_urls（向后兼容）
    else if (messageData.image_preview_urls && messageData.image_preview_urls.length > 0) {
      let filenames: string[] = []

      // 获取文件名列表
      if (messageData.original_filename) {
        if (
          typeof messageData.original_filename === 'object' &&
          messageData.original_filename.images
        ) {
          filenames = Array.isArray(messageData.original_filename.images)
            ? messageData.original_filename.images
            : [messageData.original_filename.images]
        } else if (Array.isArray(messageData.original_filename)) {
          filenames = messageData.original_filename
        } else if (typeof messageData.original_filename === 'string') {
          filenames = [messageData.original_filename]
        }
      }

      // 生成图片数据 - 处理image_preview_urls中的URL
      images = messageData.image_preview_urls.map((url: string, index: number) => ({
        url:
          url.startsWith('http') || url.startsWith('blob:')
            ? url
            : `${window.location.protocol}//${window.location.host}${url}`, // 使用当前域名
        filename: filenames[index] || `图片${index + 1}`,
      }))
    }
    // 处理API返回的图片结果（作为备选方案）
    else if (messageData.image_result && messageData.image_result.original_filename) {
      if (Array.isArray(messageData.image_result.original_filename)) {
        images = messageData.image_result.original_filename.map((filename: string) => ({
          url: getImagePreviewUrl(filename, messageData),
          filename,
        }))
      } else {
        const filename = messageData.image_result.original_filename
        images = [
          {
            url: getImagePreviewUrl(filename, messageData),
            filename,
          },
        ]
      }
    }
    // 如果以上都没有，尝试从image_result.files获取
    else if (
      messageData.image_result &&
      messageData.image_result.files &&
      Array.isArray(messageData.image_result.files)
    ) {
      images = messageData.image_result.files.map((file: any) => ({
        url: file.url
          ? file.url.startsWith('http') || file.url.startsWith('blob:')
            ? file.url
            : `${window.location.protocol}//${window.location.host}${file.url}`
          : getImagePreviewUrl(file.filename, messageData),
        filename: file.filename || `图片${images.length + 1}`,
      }))
    }
  }

  console.log('getMessageImages: 返回图片数据', images)
  return images
}

// 获取图片预览URL
const getImagePreviewUrl = (filename: string, messageData?: any) => {
  // 清理文件名（去除前后空格）
  const cleanFilename = filename.trim()

  // 优先使用服务器返回的URL
  if (messageData && messageData.image_result) {
    const imageResult = messageData.image_result

    // 检查是否有files数组且包含URL
    if (imageResult.files && Array.isArray(imageResult.files)) {
      const fileInfo = imageResult.files.find((file: any) => file.filename === cleanFilename)
      if (fileInfo && fileInfo.url) {
        return fileInfo.url.startsWith('http') || fileInfo.url.startsWith('blob:')
          ? fileInfo.url
          : `${window.location.protocol}//${window.location.host}${fileInfo.url}`
      }
    }

    // 检查是否有URL字段（单个图片）
    if (imageResult.url) {
      return imageResult.url.startsWith('http') || imageResult.url.startsWith('blob:')
        ? imageResult.url
        : `${window.location.protocol}//${window.location.host}${imageResult.url}`
    }
  }

  // 如果消息数据中有图片预览URL，使用它们
  if (
    messageData &&
    messageData.image_preview_urls &&
    Array.isArray(messageData.image_preview_urls)
  ) {
    // 尝试通过文件名匹配找到对应的URL
    const matchingUrl = messageData.image_preview_urls.find((url: string) => {
      if (!url) return false
      // 从URL中提取文件名进行匹配
      const urlFilename = url.split('/').pop()
      return urlFilename === cleanFilename
    })

    if (matchingUrl) {
      return matchingUrl.startsWith('http') || matchingUrl.startsWith('blob:')
        ? matchingUrl
        : `${window.location.protocol}//${window.location.host}${matchingUrl}`
    }

    // 如果找不到匹配的URL，尝试按索引匹配（假设顺序一致）
    // 这里需要根据实际情况调整
    console.log('图片URL匹配失败，使用默认URL:', cleanFilename)
  }

  // 生成默认的图片访问URL
  return `${window.location.protocol}//${window.location.host}/api/v1/files/image_data/raw/${cleanFilename}`
}

// 监听消息变化，自动滚动
watch(
  () => chatStore.currentMessages,
  () => {
    nextTick(() => {
      scrollToBottom()
    })
  },
  { deep: true }
)

onMounted(async () => {
  console.log('ChatWindow mounted, route params:', route.params, 'props:', props)

  // 确保用户已登录并且 chat store 已初始化
  if (!authStore.isAuthenticated) {
    console.log('用户未登录，无法加载对话')
    return
  }

  // 确保 chat store 用户数据已初始化
  if (chatStore.conversations.length === 0 && chatStore.messages.length === 0) {
    console.log('Chat store 数据未初始化，重新初始化用户数据')
    await chatStore.initializeUserData()
  }

  // 强制刷新图片显示（解决刷新后图片不显示的问题）
  console.log('强制刷新图片显示')
  await nextTick()
  // 触发响应式更新
  chatStore.messages = [...chatStore.messages]

  // 如果有路由参数ID，加载指定对话
  const conversationId = props.id || (route.params.id as string)

  if (conversationId && conversationId !== 'new') {
    try {
      console.log('Loading conversation:', conversationId)
      await chatStore.selectConversation(conversationId)
    } catch (error) {
      console.error('加载对话失败:', error)
      // 如果加载失败，清空当前对话，等待用户发送第一条消息时创建
      chatStore.currentConversation = null
    }
  } else {
    // 智能问诊页面：检查本地存储的对话历史
    console.log('智能问诊页面：检查本地对话历史')

    // 首先检查本地是否有智能问诊对话和消息
    const localDiagnosisConversations = chatStore.conversations.filter(
      conv => conv.type === 'diagnosis' && conv.messageCount > 0
    )

    const localMessages = chatStore.messages.filter((msg: any) =>
      localDiagnosisConversations.some((conv: any) => conv.id === msg.conversationId)
    )

    console.log(
      '本地智能问诊对话数:',
      localDiagnosisConversations.length,
      '本地消息数:',
      localMessages.length
    )

    if (localDiagnosisConversations.length > 0 && localMessages.length > 0) {
      // 有本地对话和消息，直接使用本地数据
      const latestConversation = localDiagnosisConversations[0]
      console.log(
        '使用本地对话历史:',
        latestConversation.id,
        '消息数:',
        localMessages.filter((m: any) => m.conversationId === latestConversation.id).length
      )
      chatStore.currentConversation = latestConversation
    } else if (!chatStore.currentConversation) {
      // 没有本地数据，尝试从API加载
      try {
        console.log('没有本地对话历史，从API加载智能问诊对话历史')
        // 专门获取智能问诊类型的对话
        chatStore.initializeUserData()

        // 查找有消息的智能问诊对话
        const diagnosisConversations = chatStore.conversations.filter(
          conv => conv.type === 'diagnosis' && conv.messageCount > 0
        )

        if (diagnosisConversations.length > 0) {
          // 选择最近的智能问诊对话
          const latestConversation = diagnosisConversations[0]
          console.log(
            '从API找到最近的智能问诊对话:',
            latestConversation.id,
            '消息数:',
            latestConversation.messageCount
          )
          await chatStore.selectConversation(latestConversation.id)
        } else {
          console.log('没有智能问诊历史对话，等待用户创建')
        }
      } catch (error) {
        console.error('加载智能问诊对话历史失败:', error)
      }
    } else {
      console.log('智能问诊页面：已有当前对话，保持现有状态', chatStore.currentConversation.id)
    }
  }

  // 滚动到底部
  await nextTick()
  scrollToBottom()
})
</script>

<template>
  <div class="chat-window">
    <div class="chat-header">
      <div class="chat-header-left">
        <h2>智能问诊</h2>
        <p>请描述您的症状，AI医生将为您提供专业的医疗建议</p>
      </div>

      <!-- 可编辑的对话标题 -->
      <div class="chat-title-section">
        <div v-if="!isEditingTitle" class="title-display" @click="startEditTitle">
          <h3 class="conversation-title">{{ currentConversationTitle }}</h3>
          <i class="fas fa-edit edit-icon"></i>
        </div>
        <div v-else class="title-edit">
          <input
            v-model="editingTitle"
            @blur="saveTitle"
            @keyup.enter="saveTitle"
            @keyup.escape="cancelEditTitle"
            class="title-input"
            ref="titleInput"
            placeholder="输入对话标题..."
          />
        </div>
      </div>

      <div class="chat-header-right">
        <button @click="startNewConversation" class="new-chat-btn">
          <i class="fas fa-plus"></i>
          新对话
        </button>
      </div>
    </div>

    <div class="chat-container">
      <!-- 消息列表 -->
      <div class="messages-container" ref="messagesContainer">
        <div v-if="chatStore.currentMessages.length === 0" class="welcome-message">
          <div class="welcome-icon">
            <i class="fas fa-user-md"></i>
          </div>
          <h3>欢迎使用智诊通</h3>
          <p>我是您的AI医生助手，请告诉我您的症状或健康问题</p>
          <div class="quick-actions">
            <button
              v-for="action in quickActions"
              :key="action.id"
              @click="sendQuickMessage(action.text)"
              class="quick-action-btn"
            >
              {{ action.text }}
            </button>
          </div>
        </div>

        <div
          v-for="message in chatStore.currentMessages"
          :key="message.id"
          class="message"
          :class="{
            'user-message': message.type === 'user',
            'ai-message': message.type === 'assistant',
          }"
        >
          <div class="message-avatar">
            <i :class="message.type === 'user' ? 'fas fa-user' : 'fas fa-robot'"></i>
          </div>
          <div class="message-content">
            <!-- 文本内容 -->
            <div v-if="parseMessageContent(message)" class="message-text">
              {{ parseMessageContent(message) }}
            </div>

            <!-- 图片内容 - 与文本分开显示 -->
            <div v-if="getMessageImages(message).length > 0" class="message-images">
              <div
                v-for="(image, imageIndex) in getMessageImages(message)"
                :key="imageIndex"
                class="message-image-container"
              >
                <img :src="image.url" :alt="image.filename" class="message-image" loading="lazy" />
                <div class="image-filename">{{ image.filename }}</div>
              </div>
            </div>

            <div class="message-time">{{ formatTime(message.timestamp) }}</div>
          </div>
        </div>

        <!-- 正在输入指示器 -->
        <div v-if="chatStore.isTyping" class="message ai-message">
          <div class="message-avatar">
            <i class="fas fa-robot"></i>
          </div>
          <div class="message-content">
            <div class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="input-container">
        <!-- 图片预览区域 -->
        <div v-if="selectedImages.length > 0" class="image-preview-section">
          <div class="image-preview-list">
            <div
              v-for="(_, index) in selectedImages"
              :key="index"
              class="image-preview-item"
              @mouseenter="hoveredImageIndex = index"
              @mouseleave="hoveredImageIndex = -1"
            >
              <img
                :src="imagePreviewUrls[index]"
                :alt="`预览图片 ${index + 1}`"
                class="preview-image"
              />
              <button
                v-show="hoveredImageIndex === index"
                @click="removeImage(index)"
                class="remove-image-btn"
              >
                <i class="fas fa-times"></i>
              </button>
            </div>
          </div>
        </div>

        <!-- 统一输入区域 -->
        <div class="unified-input-wrapper">
          <textarea
            v-model="inputMessage"
            @keydown.enter.prevent="handleEnterKey"
            placeholder="请描述您的症状或健康问题..."
            class="message-input"
            rows="3"
            maxlength="1000"
          ></textarea>

          <!-- 输入框内按钮 -->
          <div class="input-buttons">
            <!-- 上传图片按钮 -->
            <input
              type="file"
              accept="image/*"
              @change="handleImageSelect"
              id="image-upload"
              class="file-input"
              multiple
            />
            <label for="image-upload" class="input-btn image-btn" title="上传图片">
              <i class="fas fa-image"></i>
            </label>

            <!-- 录音按钮 -->
            <button
              @click="isRecording ? stopRecording() : startRecording()"
              class="input-btn record-btn"
              :class="{ recording: isRecording }"
              :disabled="isProcessingVoice"
              :title="isRecording ? '停止录音' : '开始录音'"
            >
              <i :class="isRecording ? 'fas fa-stop' : 'fas fa-microphone'"></i>
            </button>

            <!-- 发送按钮 -->
            <button
              @click="sendMessage"
              :disabled="
                (!inputMessage.trim() && selectedImages.length === 0 && !selectedAudio) ||
                chatStore.isLoading ||
                isUploading ||
                isProcessingVoice
              "
              class="input-btn send-btn"
              title="发送消息"
            >
              <i v-if="isUploading || isProcessingVoice" class="fas fa-spinner fa-spin"></i>
              <i v-else class="fas fa-paper-plane"></i>
            </button>
          </div>
        </div>

        <!-- 状态指示器 -->
        <div v-if="isRecording" class="status-indicator recording">
          <i class="fas fa-microphone recording-icon"></i>
          <span>正在录音...</span>
        </div>

        <div v-if="isProcessingVoice" class="status-indicator processing">
          <i class="fas fa-spinner fa-spin"></i>
          <span>正在处理语音...</span>
        </div>

        <!-- 输入提示 -->
        <div class="input-tips">
          <span>按 Enter 发送，Shift + Enter 换行</span>
          <span>支持文字、图片、语音组合输入</span>
          <span v-if="inputMessage" class="char-count">{{ inputMessage.length }}/1000</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="less">
.chat-window {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
}

.chat-header {
  padding: 24px;
  background: white;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;

  .chat-header-left {
    flex: 0 0 auto;
    max-width: 300px;

    h2 {
      margin: 0 0 8px 0;
      color: #333;
      font-size: 1.5rem;
    }

    p {
      margin: 0;
      color: #666;
      font-size: 0.9rem;
    }
  }

  .chat-title-section {
    flex: 1;
    display: flex;
    justify-content: center;
    align-items: center;
    min-width: 0;

    .title-display {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      padding: 8px 12px;
      border-radius: 6px;
      transition: all 0.3s;

      &:hover {
        background: #f5f5f5;

        .edit-icon {
          opacity: 1;
        }
      }

      .conversation-title {
        margin: 0;
        font-size: 1.2rem;
        color: #333;
        font-weight: 500;
      }

      .edit-icon {
        opacity: 0;
        color: #666;
        font-size: 0.8rem;
        transition: opacity 0.3s;
      }
    }

    .title-edit {
      .title-input {
        width: 100%;
        padding: 8px 12px;
        border: 2px solid #1890ff;
        border-radius: 6px;
        font-size: 1.2rem;
        font-weight: 500;
        outline: none;
        background: white;

        &:focus {
          border-color: #40a9ff;
          box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
        }
      }
    }
  }

  .chat-header-right {
    flex: 0 0 auto;

    .new-chat-btn {
      padding: 8px 16px;
      background: #1890ff;
      color: white;
      border: none;
      border-radius: 6px;
      cursor: pointer;
      font-size: 0.9rem;
      transition: all 0.3s;
      display: flex;
      align-items: center;
      gap: 6px;

      &:hover {
        background: #40a9ff;
        transform: translateY(-1px);
      }

      &:active {
        transform: translateY(0);
      }

      i {
        font-size: 0.8rem;
      }
    }
  }
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0; /* 确保flex子元素可以收缩 */
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.welcome-message {
  text-align: center;
  padding: 40px 20px;
  color: #666;

  .welcome-icon {
    width: 80px;
    height: 80px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 20px;
    color: white;
    font-size: 2rem;
  }

  h3 {
    margin: 0 0 12px 0;
    color: #333;
    font-size: 1.3rem;
  }

  p {
    margin: 0 0 24px 0;
    color: #666;
    line-height: 1.5;
  }
}

.quick-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;

  .quick-action-btn {
    padding: 8px 16px;
    border: 1px solid #d9d9d9;
    border-radius: 20px;
    background: white;
    color: #666;
    cursor: pointer;
    transition: all 0.3s;
    font-size: 0.9rem;

    &:hover {
      border-color: #1890ff;
      color: #1890ff;
      background: #f0f8ff;
    }
  }
}

.message {
  display: flex;
  gap: 12px;
  max-width: 80%;

  &.user-message {
    align-self: flex-end;
    flex-direction: row-reverse;

    .message-content {
      background: #1890ff;
      color: white;
      border-radius: 18px 18px 4px 18px;
    }
  }

  &.ai-message {
    align-self: flex-start;

    .message-content {
      background: white;
      color: #333;
      border-radius: 18px 18px 18px 4px;
      border: 1px solid #f0f0f0;
    }
  }
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f0f0;
  color: #666;
  font-size: 1.2rem;
  flex-shrink: 0;
}

.message-content {
  padding: 12px 16px;
  max-width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;

  .message-text {
    line-height: 1.5;
    word-wrap: break-word;
  }

  // 消息中的图片区域
  .message-images {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin-top: 8px;
  }

  .message-image-container {
    max-width: 200px;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

    .message-image {
      width: 100%;
      height: auto;
      object-fit: cover;
      transition: all 0.3s;

      &:hover {
        transform: scale(1.02);
      }
    }

    .image-filename {
      font-size: 0.8rem;
      color: #999;
      padding: 4px 8px;
      background: #f9f9f9;
      text-align: center;
      word-break: break-all;
    }
  }

  .message-time {
    font-size: 0.8rem;
    color: #999;
    margin-top: 4px;
    align-self: flex-end;
  }
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 8px 0;

  span {
    width: 8px;
    height: 8px;
    background: #999;
    border-radius: 50%;
    animation: typing 1.4s infinite ease-in-out;

    &:nth-child(1) {
      animation-delay: -0.32s;
    }
    &:nth-child(2) {
      animation-delay: -0.16s;
    }
  }
}

@keyframes typing {
  0%,
  80%,
  100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.input-container {
  padding: 24px;
  background: white;
  border-top: 1px solid #f0f0f0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

// 图片预览区域
.image-preview-section {
  .image-preview-list {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
  }

  .image-preview-item {
    position: relative;
    width: 80px;
    height: 80px;
    border-radius: 8px;
    overflow: visible;
    border: 2px solid #f0f0f0;
    transition: all 0.3s;

    &:hover {
      border-color: #1890ff;
      transform: scale(1.05);
    }

    .preview-image {
      width: 100%;
      height: 100%;
      object-fit: cover;
      border-radius: 6px;
    }

    .remove-image-btn {
      position: absolute;
      top: -6px;
      right: -6px;
      width: 22px;
      height: 22px;
      background: #ff4d4f;
      color: white;
      border: 2px solid white;
      border-radius: 50%;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 11px;
      transition: all 0.3s;
      z-index: 10;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);

      &:hover {
        background: #ff7875;
        transform: scale(1.1);
        box-shadow: 0 3px 6px rgba(0, 0, 0, 0.3);
      }
    }
  }
}

// 统一输入区域
.unified-input-wrapper {
  position: relative;
  display: flex;
  align-items: flex-end;
  background: #fafafa;
  border: 1px solid #d9d9d9;
  border-radius: 12px;
  padding: 8px;
  transition: all 0.3s;

  &:focus-within {
    border-color: #1890ff;
    box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
  }

  .message-input {
    flex: 1;
    border: none;
    background: transparent;
    padding: 8px 12px;
    resize: none;
    font-family: inherit;
    font-size: 0.9rem;
    line-height: 1.5;
    outline: none;
    min-height: 40px;
    max-height: 120px;

    &::placeholder {
      color: #999;
    }
  }

  .input-buttons {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-left: 8px;

    .file-input {
      display: none;
    }

    .input-btn {
      width: 36px;
      height: 36px;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.3s;
      font-size: 14px;

      &:hover:not(:disabled) {
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
      }

      &:active {
        transform: translateY(0);
      }

      &:disabled {
        opacity: 0.5;
        cursor: not-allowed;
        transform: none;
      }

      &.image-btn {
        background: #fff2e8;
        color: #fa8c16;

        &:hover:not(:disabled) {
          background: #fff7e6;
          color: #d46b08;
        }
      }

      &.record-btn {
        background: #f6ffed;
        color: #52c41a;

        &:hover:not(:disabled) {
          background: #f6ffed;
          color: #389e0d;
        }

        &.recording {
          background: #ff4d4f;
          color: white;
          animation: pulse 1s infinite;

          &:hover {
            background: #ff7875;
          }
        }
      }

      &.send-btn {
        background: #1890ff;
        color: white;

        &:hover:not(:disabled) {
          background: #40a9ff;
        }

        &:disabled {
          background: #d9d9d9;
        }
      }
    }
  }
}

// 状态指示器
.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 0.9rem;

  &.recording {
    background: #fff2f0;
    border: 1px solid #ffccc7;
    color: #ff4d4f;

    .recording-icon {
      animation: pulse 1s infinite;
    }
  }

  &.processing {
    background: #e6f7ff;
    border: 1px solid #91d5ff;
    color: #1890ff;
  }
}

.input-tips {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 0.8rem;
  color: #999;

  .char-count {
    color: #666;
  }
}

@keyframes pulse {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1);
  }
}

// 响应式设计
@media (max-width: 768px) {
  .chat-header {
    padding: 16px;

    h2 {
      font-size: 1.3rem;
    }
  }

  .messages-container {
    padding: 16px;
  }

  .input-container {
    padding: 16px;
  }

  .message {
    max-width: 90%;
  }
}

@keyframes pulse {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
  100% {
    opacity: 1;
  }
}
</style>
