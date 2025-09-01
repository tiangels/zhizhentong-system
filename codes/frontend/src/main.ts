/**
 * Vue应用入口文件
 * 配置Vue应用、路由、状态管理、插件等
 */

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Antd from 'ant-design-vue'
import App from './App.vue'
import router from './router'
import 'ant-design-vue/dist/reset.css'
import '@fortawesome/fontawesome-free/css/all.css'
import './assets/styles/global.less'
import './assets/styles/theme.less'

// 创建Vue应用实例
const app = createApp(App)

// 配置Pinia状态管理
const pinia = createPinia()
app.use(pinia)

// 配置路由
app.use(router)

// 配置Ant Design Vue
app.use(Antd)

// 挂载应用
app.mount('#app')
