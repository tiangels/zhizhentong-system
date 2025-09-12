<script setup lang="ts">
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { UserOutlined, MailOutlined, LockOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '@/stores/auth'
import type { RegisterRequest } from '@/types'

const router = useRouter()
const authStore = useAuthStore()

// 表单数据
const formData = reactive<RegisterRequest & { confirmPassword: string; agree: boolean }>({
  username: '',
  email: '',
  password: '',
  agreeToTerms: false,
  confirmPassword: '',
  agree: false,
})

// 表单验证规则
const rules: any = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (_: any, value: string) => {
        if (value !== formData.password) {
          return Promise.reject('两次输入的密码不一致')
        }
        return Promise.resolve()
      },
      trigger: 'blur',
    },
  ],
  agree: [
    {
      validator: (_: any, value: boolean) => {
        if (!value) {
          return Promise.reject('请阅读并同意用户协议和隐私政策')
        }
        return Promise.resolve()
      },
      trigger: 'change',
    },
  ],
}

// 处理注册
const handleRegister = async (values: RegisterRequest) => {
  try {
    await authStore.register(values)
    message.success('注册成功')
    router.push('/chat')
  } catch (error: any) {
    message.error(error.message || '注册失败')
  }
}
</script>

<template>
  <div class="register-page">
    <a-form
      :model="formData"
      :rules="rules"
      @finish="handleRegister"
      layout="vertical"
      class="register-form"
    >
      <a-form-item label="用户名" name="username">
        <a-input v-model="formData.username" placeholder="请输入用户名" size="large">
          <template #prefix>
            <UserOutlined />
          </template>
        </a-input>
      </a-form-item>

      <a-form-item label="邮箱" name="email">
        <a-input v-model="formData.email" placeholder="请输入邮箱" size="large">
          <template #prefix>
            <MailOutlined />
          </template>
        </a-input>
      </a-form-item>

      <a-form-item label="密码" name="password">
        <a-input-password v-model="formData.password" placeholder="请输入密码" size="large">
          <template #prefix>
            <LockOutlined />
          </template>
        </a-input-password>
      </a-form-item>

      <a-form-item label="确认密码" name="confirmPassword">
        <a-input-password
          v-model="formData.confirmPassword"
          placeholder="请再次输入密码"
          size="large"
        >
          <template #prefix>
            <LockOutlined />
          </template>
        </a-input-password>
      </a-form-item>

      <a-form-item>
        <a-checkbox v-model="formData.agree">
          我已阅读并同意
          <a href="#" target="_blank">用户协议</a>
          和
          <a href="#" target="_blank">隐私政策</a>
        </a-checkbox>
      </a-form-item>

      <a-form-item>
        <a-button
          type="primary"
          html-type="submit"
          size="large"
          :loading="authStore.isLoading"
          block
        >
          注册
        </a-button>
      </a-form-item>

      <div class="register-footer">
        <span>已有账号？</span>
        <router-link to="/auth/login">立即登录</router-link>
      </div>
    </a-form>
  </div>
</template>

<style lang="less" scoped>
.register-page {
  width: 100%;
}

.register-form {
  .ant-form-item {
    margin-bottom: @spacing-lg;
  }
}

.register-footer {
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
