<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const goToLogin = () => {
  router.push('/auth/login')
}

const goToRegister = () => {
  router.push('/auth/register')
}
</script>

<template>
  <div class="simple-page">
    <h1>智诊通系统</h1>
    <p>欢迎使用智诊通多模态智能医生问诊系统</p>
    <div class="buttons">
      <button @click="goToLogin" class="btn btn-primary">登录</button>
      <button @click="goToRegister" class="btn">注册</button>
    </div>
  </div>
</template>

<style scoped>
.simple-page {
  padding: 40px;
  text-align: center;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.simple-page h1 {
  font-size: 2.5rem;
  margin-bottom: 1rem;
}

.simple-page p {
  font-size: 1.2rem;
  margin-bottom: 2rem;
  opacity: 0.9;
}

.buttons {
  display: flex;
  gap: 1rem;
}

.btn {
  padding: 12px 24px;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary {
  background: #1890ff;
  color: white;
}

.btn-primary:hover {
  background: #40a9ff;
}

.btn {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.btn:hover {
  background: rgba(255, 255, 255, 0.3);
}
</style>
