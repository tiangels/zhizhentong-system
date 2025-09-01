// / <reference types="vite/client" />

// 环境变量类型声明
interface ImportMetaEnv {
  readonly VITE_APP_TITLE: string
  readonly VITE_APP_VERSION: string
  readonly VITE_APP_ENV: string
  readonly VITE_API_BASE_URL: string
  readonly VITE_API_TIMEOUT: string
  readonly VITE_API_RETRY_TIMES: string
  readonly VITE_WS_URL: string
  readonly VITE_UPLOAD_MAX_SIZE: string
  readonly VITE_UPLOAD_ACCEPT_TYPES: string
  readonly VITE_DEBUG_MODE: string
  readonly VITE_LOG_LEVEL: string
  readonly VITE_DEFAULT_LOCALE: string
  readonly VITE_TIMEZONE: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

// Vue组件类型声明
declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

// 静态资源类型声明
declare module '*.svg' {
  const content: string
  export default content
}

declare module '*.png' {
  const content: string
  export default content
}

declare module '*.jpg' {
  const content: string
  export default content
}

declare module '*.jpeg' {
  const content: string
  export default content
}

declare module '*.gif' {
  const content: string
  export default content
}

declare module '*.webp' {
  const content: string
  export default content
}

declare module '*.ico' {
  const content: string
  export default content
}

declare module '*.bmp' {
  const content: string
  export default content
}

// 样式文件类型声明
declare module '*.css' {
  const content: { [className: string]: string }
  export default content
}

declare module '*.less' {
  const content: { [className: string]: string }
  export default content
}

declare module '*.scss' {
  const content: { [className: string]: string }
  export default content
}

declare module '*.sass' {
  const content: { [className: string]: string }
  export default content
}

// 字体文件类型声明
declare module '*.woff' {
  const content: string
  export default content
}

declare module '*.woff2' {
  const content: string
  export default content
}

declare module '*.eot' {
  const content: string
  export default content
}

declare module '*.ttf' {
  const content: string
  export default content
}

declare module '*.otf' {
  const content: string
  export default content
}

// 音频文件类型声明
declare module '*.mp3' {
  const content: string
  export default content
}

declare module '*.wav' {
  const content: string
  export default content
}

declare module '*.ogg' {
  const content: string
  export default content
}

declare module '*.m4a' {
  const content: string
  export default content
}

declare module '*.aac' {
  const content: string
  export default content
}

// 视频文件类型声明
declare module '*.mp4' {
  const content: string
  export default content
}

declare module '*.webm' {
  const content: string
  export default content
}

declare module '*.avi' {
  const content: string
  export default content
}

declare module '*.mov' {
  const content: string
  export default content
}

// 文档文件类型声明
declare module '*.pdf' {
  const content: string
  export default content
}

declare module '*.doc' {
  const content: string
  export default content
}

declare module '*.docx' {
  const content: string
  export default content
}

declare module '*.txt' {
  const content: string
  export default content
}

// JSON文件类型声明
declare module '*.json' {
  const content: any
  export default content
}

// 其他文件类型声明
declare module '*.xml' {
  const content: string
  export default content
}

declare module '*.yaml' {
  const content: any
  export default content
}

declare module '*.yml' {
  const content: any
  export default content
}
