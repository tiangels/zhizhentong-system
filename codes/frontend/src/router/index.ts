/**
 * 路由配置
 * 定义应用的路由规则和导航守卫
 */

import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// 路由配置
const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/SimplePage.vue'),
    meta: { title: '首页' },
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/components/layout/AuthLayout.vue'),
    meta: { requiresAuth: true, title: '仪表盘' },
    children: [
      {
        path: '',
        name: 'DashboardContent',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '仪表盘' },
      },
    ],
  },

  {
    path: '/auth',
    name: 'Auth',
    component: () => import('@/views/auth/AuthLayout.vue'),
    meta: { requiresGuest: false, title: '认证' },
    children: [
      {
        path: 'login',
        name: 'Login',
        component: () => import('@/views/auth/Login.vue'),
        meta: { title: '登录', requiresGuest: false },
      },
      {
        path: 'register',
        name: 'Register',
        component: () => import('@/views/auth/Register.vue'),
        meta: { title: '注册', requiresGuest: false },
      },
    ],
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('@/components/layout/AuthLayout.vue'),
    meta: { requiresAuth: true, title: '智能问诊' },
    children: [
      {
        path: '',
        name: 'ChatWindow',
        component: () => import('@/views/chat/ChatWindow.vue'),
        meta: { title: '对话窗口' },
      },
      {
        path: ':id',
        name: 'ChatWithId',
        component: () => import('@/views/chat/ChatWindow.vue'),
        meta: { title: '对话详情' },
        props: true,
      },
      {
        path: 'history',
        name: 'ChatHistory',
        component: () => import('@/views/chat/ChatHistory.vue'),
        meta: { title: '对话历史' },
      },
      // Debug route temporarily disabled - DebugChat.vue not found
      // {
      //   path: 'debug',
      //   name: 'ChatDebug',
      //   component: () => import('@/views/DebugChat.vue'),
      //   meta: { title: '聊天调试' },
      // },
    ],
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/components/layout/AuthLayout.vue'),
    meta: { requiresAuth: true, title: '用户档案' },
    children: [
      {
        path: '',
        name: 'ProfileContent',
        component: () => import('@/views/profile/UserProfile.vue'),
        meta: { title: '用户档案' },
      },
    ],
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/components/layout/AuthLayout.vue'),
    meta: { requiresAuth: true, title: '应用设置' },
    children: [
      {
        path: '',
        name: 'SettingsContent',
        component: () => import('@/views/settings/AppSettings.vue'),
        meta: { title: '应用设置' },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/error/NotFound.vue'),
    meta: { title: '页面不存在' },
  },
]

// 创建路由实例
const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(_, __, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  },
})

// 全局前置守卫
router.beforeEach(async(to, from, next) => {
  console.log('路由守卫 - 从:', from.path, '到:', to.path)

  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - 智诊通`
  }

  const authStore = useAuthStore()

  // 等待状态稳定
  await new Promise(resolve => setTimeout(resolve, 100))

  console.log('路由守卫 - 用户登录状态:', authStore.isLoggedIn)
  console.log('路由守卫 - 认证状态详情:', {
    token: !!authStore.token,
    user: !!authStore.user,
    isAuthenticated: authStore.isAuthenticated,
  })

  // 特殊处理：如果访问认证页面，允许访问（无论登录状态）
  if (to.path.startsWith('/auth/')) {
    console.log('路由守卫 - 访问认证页面，允许访问')
    next()
    return
  }

  // 检查是否需要认证
  if (to.meta.requiresAuth) {
    console.log('路由守卫 - 需要认证的页面')
    if (!authStore.isLoggedIn) {
      console.log('路由守卫 - 未登录，跳转到登录页')
      // 未登录，跳转到登录页
      next({
        path: '/auth/login',
        query: { redirect: to.fullPath },
      })
      return
    }
  }

  // 检查是否需要游客访问（已登录用户不能访问）
  if (to.meta.requiresGuest) {
    console.log('路由守卫 - 游客页面')
    if (authStore.isLoggedIn) {
      console.log('路由守卫 - 已登录，跳转到聊天页')
      // 已登录，跳转到首页
      next({ path: '/chat' })
      return
    }
  }

  // 特殊处理：如果访问根路径且未登录，允许访问首页
  if (to.path === '/' && !authStore.isLoggedIn) {
    console.log('路由守卫 - 访问首页，允许访问')
    next()
    return
  }

  console.log('路由守卫 - 允许访问')
  next()
})

// 全局后置钩子
router.afterEach((to, from) => {
  // 路由切换后的处理
  console.log(`路由切换: ${from.path} -> ${to.path}`)
})

export default router
