<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { UserOutlined, MailOutlined, LockOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '@/stores/auth'
import type { RegisterRequest } from '@/types'

const router = useRouter()
const authStore = useAuthStore()

// 表单数据
const formData = reactive<RegisterRequest & { confirmPassword: string }>({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  agreeToTerms: false,
})

// 表单引用
const formRef = ref()

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
        if (value && value !== formData.password) {
          return Promise.reject('两次输入的密码不一致')
        }
        return Promise.resolve()
      },
      trigger: 'blur',
    },
  ],
  agreeToTerms: [
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
const handleRegister = async (values: any) => {
  try {
    console.log('=== 注册调试信息 ===')
    console.log('1. 表单提交的values参数:', values)
    console.log('2. 当前formData状态:', JSON.stringify(formData, null, 2))
    console.log('3. values是否为空:', !values || Object.keys(values).length === 0)

    // 检查数据来源
    let finalData
    if (values && Object.keys(values).length > 0) {
      console.log('4. 使用values数据')
      finalData = {
        username: values.username,
        email: values.email,
        password: values.password,
        full_name: values.username,
        phone: '',
      }
    } else {
      console.log('4. values为空，使用formData数据')
      finalData = {
        username: formData.username,
        email: formData.email,
        password: formData.password,
        full_name: formData.username,
        phone: '',
      }
    }

    console.log('5. 最终发送给后端的数据:', finalData)
    console.log('6. 数据验证:')
    console.log('   - 用户名:', finalData.username, finalData.username ? '✅' : '❌')
    console.log('   - 邮箱:', finalData.email, finalData.email ? '✅' : '❌')
    console.log('   - 密码:', finalData.password ? '✅' : '❌')

    await authStore.register(finalData)
    message.success('注册成功')
    router.push('/chat')
  } catch (error: any) {
    console.error('注册错误:', error)
    message.error(error.message || '注册失败')
  }
}

// 手动验证表单
const validateForm = async () => {
  try {
    await formRef.value.validate()
    return true
  } catch (error) {
    console.log('表单验证失败:', error)
    return false
  }
}

// 调试表单状态
const debugForm = () => {
  console.log('=== 调试表单状态 ===')
  console.log('1. formData:', JSON.stringify(formData, null, 2))
  console.log('2. formRef.value:', formRef.value)

  // 检查表单实例的字段值
  if (formRef.value) {
    const formValues = formRef.value.getFieldsValue()
    console.log('3. 表单实例字段值:', formValues)
  }

  console.log('4. 表单验证状态:')

  // 手动触发验证
  formRef.value
    ?.validate()
    .then(() => {
      console.log('✅ 表单验证通过')
    })
    .catch((errors: any) => {
      console.log('❌ 表单验证失败:', errors)
    })

  // 检查每个字段的值
  console.log('5. 字段值检查:')
  console.log('   - username:', formData.username, formData.username ? '✅' : '❌')
  console.log('   - email:', formData.email, formData.email ? '✅' : '❌')
  console.log('   - password:', formData.password ? '✅' : '❌')
  console.log('   - confirmPassword:', formData.confirmPassword ? '✅' : '❌')
  console.log('   - agreeToTerms:', formData.agreeToTerms ? '✅' : '❌')
}

// 添加实时监控函数
const monitorFormData = () => {
  console.log('=== 实时监控表单数据 ===')
  console.log('当前 formData:', formData)

  // 监听 formData 的变化
  const unwatch = watch(
    formData,
    (newVal, oldVal) => {
      console.log('formData 发生变化:', { oldVal, newVal })
    },
    { deep: true }
  )

  return unwatch
}
</script>

<template>
  <div class="register-page">
    <a-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      @finish="handleRegister"
      layout="vertical"
      class="register-form"
      :validate-trigger="['blur', 'change']"
    >
      <a-form-item label="用户名" name="username">
        <a-input
          v-model="formData.username"
          placeholder="请输入用户名"
          size="large"
          @input="
            e => {
              formData.username = e.target.value
              console.log('用户名输入:', e.target.value)
            }
          "
        >
          <template #prefix>
            <UserOutlined />
          </template>
        </a-input>
      </a-form-item>

      <a-form-item label="邮箱" name="email">
        <a-input
          v-model="formData.email"
          placeholder="请输入邮箱"
          size="large"
          @input="
            e => {
              formData.email = e.target.value
              console.log('邮箱输入:', e.target.value)
            }
          "
        >
          <template #prefix>
            <MailOutlined />
          </template>
        </a-input>
      </a-form-item>

      <a-form-item label="密码" name="password">
        <a-input-password
          v-model="formData.password"
          placeholder="请输入密码"
          size="large"
          @input="
            e => {
              formData.password = e.target.value
              console.log('密码输入:', e.target.value)
            }
          "
        >
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
          @input="
            e => {
              formData.confirmPassword = e.target.value
              console.log('确认密码输入:', e.target.value)
            }
          "
        >
          <template #prefix>
            <LockOutlined />
          </template>
        </a-input-password>
      </a-form-item>

      <a-form-item name="agreeToTerms">
        <a-checkbox
          v-model="formData.agreeToTerms"
          @change="
            e => {
              formData.agreeToTerms = e.target.checked
              console.log('协议勾选:', e.target.checked)
            }
          "
        >
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

      <!-- 临时调试按钮 -->
      <a-form-item>
        <a-button
          @click="debugForm"
          size="large"
          style="background: #ff4d4f; color: white; width: 100%"
        >
          调试表单状态
        </a-button>
      </a-form-item>

      <a-form-item>
        <a-button
          @click="monitorFormData"
          size="large"
          style="background: #1890ff; color: white; width: 100%"
        >
          开始监控数据绑定
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
