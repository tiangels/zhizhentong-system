// / <reference types="vite/client" />

interface ImportMetaEnv {
  readonly NODE_ENV: string
  readonly MODE: string
  readonly DEV: boolean
  readonly PROD: boolean
  readonly VITE_API_BASE_URL?: string
  readonly VITE_WS_URL?: string
  readonly VITE_APP_TITLE?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
