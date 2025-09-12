<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { UserOutlined, LockOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '../../stores/auth'
import type { LoginRequest } from '../../types'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// 表单引用（用于手动验证）
const formRef = ref()

// 表单数据 - 确保初始值正确
const formData = reactive<LoginRequest>({
  username: '',
  password: '',
  rememberMe: false,
})

// 补充表单验证规则（可选，但推荐）
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: ['blur', 'change'] }],
  password: [{ required: true, message: '请输入密码', trigger: ['blur', 'change'] }],
}

// 监听表单数据变化（验证是否正确更新）
watch(
  () => [formData.username, formData.password],
  ([newUser, newPwd], [oldUser, oldPwd]) => {
    console.log('🔍 用户名变化:', oldUser, '->', newUser)
    console.log('🔍 密码变化:', oldPwd, '->', newPwd)
  },
  { deep: true }
)

// 处理登录提交
const handleSubmit = async () => {
  try {
    // 手动触发表单验证（可选，根据需求决定）
    if (formRef.value) {
      const valid = await formRef.value.validate()
      if (!valid) return
    }

    // 再次检查数据是否为空（双重保险）
    if (!formData.username.trim() || !formData.password.trim()) {
      message.error('用户名和密码不能为空')
      return
    }

    // 调用登录接口
    await authStore.login(formData)
    message.success('登录成功')

    // 跳转页面
    const redirect = route.query.redirect as string
    await router.push(redirect || '/chat')
  } catch (error: unknown) {
    console.error('登录失败:', error)
    const errorMsg = (error as Error).message || '登录失败，请重试'
    message.error(errorMsg)
  }
}

// 测试表单数据（用于调试）
const testFormData = () => {
  message.info(`用户名: ${formData.username || '空'}, 密码长度: ${formData.password?.length || 0}`)
}
</script>

<template>
  <div class="login-page">
    <div class="test-account-info">
      <a-alert
        message="测试账号"
        description="管理员: admin / admin123 | 普通用户: test / test123"
        type="info"
        show-icon
        closable
      />
    </div>

    <!-- 表单核心：确保 model 与 v-model 绑定一致 -->
    <a-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      layout="vertical"
      class="login-form"
      @submit.prevent="handleSubmit"
    >
      <!-- 用户名输入框：name 与 formData 的 key 保持一致 -->
      <a-form-item label="用户名、邮箱或手机号" name="username">
        <a-input v-model:value="formData.username" placeholder="请输入用户名" size="large">
          <template #prefix><UserOutlined /></template>
        </a-input>
      </a-form-item>

      <!-- 密码输入框：同样显式绑定 value -->
      <a-form-item label="密码" name="password">
        <a-input-password v-model:value="formData.password" placeholder="请输入密码" size="large">
          <template #prefix><LockOutlined /></template>
        </a-input-password>
      </a-form-item>

      <a-form-item>
        <a-checkbox v-model:checked="formData.rememberMe"> 记住我 </a-checkbox>
        <a class="forgot-password" href="#"> 忘记密码？ </a>
      </a-form-item>

      <a-form-item>
        <a-button
          type="primary"
          size="large"
          :loading="authStore.isLoading"
          block
          @click="handleSubmit"
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

<style scoped>
.login-page {
  width: 100%;
  max-width: 360px;
  margin: 0 auto;
  padding: 24px;
}

.test-account-info {
  margin-bottom: 24px;
}

.login-form .ant-form-item {
  margin-bottom: 24px;
}

.forgot-password {
  float: right;
  color: #1890ff;
}

.login-footer {
  text-align: center;
  margin-top: 24px;
  color: #666;
}

.login-footer a {
  color: #1890ff;
  margin-left: 8px;
}
</style>
