<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { UserOutlined, LockOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '../../stores/auth'
import type { LoginRequest } from '../../types'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// 表单引用
const formRef = ref()

// 表单数据 - 空表单，让用户自己输入
const formData = reactive<LoginRequest>({
  username: '',
  password: '',
  rememberMe: false,
})

// 表单验证规则
const rules = {
  username: [
    { required: true, message: '请输入用户名、邮箱或手机号', trigger: 'blur' as const },
    { min: 2, message: '用户名至少2个字符', trigger: 'blur' as const },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' as const },
    { min: 6, message: '密码长度至少6个字符', trigger: 'blur' as const },
  ],
}

// 手动验证表单
const validateForm = async() => {
  try {
    console.log('Login.vue - 手动验证表单开始')
    console.log('Login.vue - 当前表单数据:', formData)
    console.log('Login.vue - formData.username:', formData.username)
    console.log('Login.vue - formData.password:', formData.password)

    // 先检查数据是否存在
    if (!formData.username || !formData.password) {
      console.error('Login.vue - 表单数据为空')
      message.error('请输入用户名和密码')
      return false
    }

    await formRef.value?.validate()
    console.log('Login.vue - 表单验证通过')
    return true
  } catch (error) {
    console.error('Login.vue - 表单验证失败:', error)
    message.error('请检查输入信息')
    return false
  }
}

// 处理登录按钮点击
const handleSubmit = async() => {
  console.log('Login.vue - 登录按钮被点击')
  console.log('Login.vue - 当前表单数据:', formData)

  // 手动验证表单
  const isValid = await validateForm()
  if (!isValid) {
    return
  }

  // 调用登录处理
  await handleLogin(formData)
}

// 处理登录
const handleLogin = async(values: LoginRequest) => {
  try {
    console.log('Login.vue - 开始登录处理，用户输入:', values)
    console.log('Login.vue - 表单验证通过，准备调用API')

    await authStore.login(values)
    message.success('登录成功')

    // 等待状态更新
    await new Promise(resolve => setTimeout(resolve, 100))

    console.log('Login.vue - 登录成功，准备跳转')
    console.log('Login.vue - 当前登录状态:', authStore.isLoggedIn)

    // 跳转到目标页面或首页
    const redirect = route.query.redirect as string
    const targetPath = redirect || '/chat'
    console.log('Login.vue - 跳转目标:', targetPath)

    await router.push(targetPath)
  } catch (error: unknown) {
    console.error('Login.vue - 登录失败:', error)
    // 显示具体的错误信息
    const errorMessage = (error as Error).message || '登录失败，请检查用户名和密码'
    message.error(errorMessage)

    // 如果是网络错误，提供更友好的提示
    if ((error as Error).message && (error as Error).message.includes('网络连接失败')) {
      message.warning('请确保后端服务正在运行')
    }
  }
}
</script>

<template>
  <div class="login-page">
    <!-- 测试账号提示 -->
    <div class="test-account-info">
      <a-alert
        message="测试账号"
        description="管理员: admin / admin123 | 普通用户: test / test123"
        type="info"
        show-icon
        closable
      />
    </div>

    <a-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      @finish="handleLogin"
      layout="vertical"
      class="login-form"
    >
      <a-form-item label="用户名、邮箱或手机号" name="username">
        <a-input 
          v-model:value="formData.username" 
          placeholder="请输入用户名、邮箱或手机号" 
          size="large"
          @input="() => console.log('用户名输入:', formData.username)"
        >
          <template #prefix>
            <UserOutlined />
          </template>
        </a-input>
      </a-form-item>

      <a-form-item label="密码" name="password">
        <a-input-password 
          v-model:value="formData.password" 
          placeholder="请输入密码" 
          size="large"
          @input="() => console.log('密码输入:', formData.password)"
        >
          <template #prefix>
            <LockOutlined />
          </template>
        </a-input-password>
      </a-form-item>

      <a-form-item>
        <a-checkbox v-model="formData.rememberMe"> 记住我 </a-checkbox>
        <a class="forgot-password" href="#"> 忘记密码？ </a>
      </a-form-item>

      <a-form-item>
        <a-button
          type="primary"
          size="large"
          :loading="authStore.isLoading"
          block
          html-type="submit"
          @click.prevent="handleSubmit"
        >
          登录
        </a-button>
      </a-form-item>

      <div class="login-footer">
        <span>还没有账号？</span>
        <router-link to="/auth/register">立即注册</router-link>
      </div>
    </a-form>
  </div>
</template>

<style lang="less" scoped>
.login-page {
  width: 100%;
}

.test-account-info {
  margin-bottom: 24px;
}

.login-form {
  .ant-form-item {
    margin-bottom: @spacing-lg;
  }
}

.forgot-password {
  float: right;
  color: @primary-color;

  &:hover {
    color: @primary-color-hover;
  }
}

.login-footer {
  text-align: center;
  margin-top: @spacing-lg;
  color: @text-color-secondary;

  a {
    color: @primary-color;
    margin-left: @spacing-xs;

    &:hover {
      color: @primary-color-hover;
    }
  }
}
</style>
