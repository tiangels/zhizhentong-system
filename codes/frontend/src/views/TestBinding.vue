<template>
  <div style="padding: 20px">
    <h2>数据绑定测试</h2>

    <div style="margin-bottom: 20px">
      <label>用户名:</label>
      <input v-model="formData.username" placeholder="输入用户名" />
      <p>当前值: {{ formData.username }}</p>
    </div>

    <div style="margin-bottom: 20px">
      <label>密码:</label>
      <input v-model="formData.password" type="password" placeholder="输入密码" />
      <p>当前值: {{ formData.password }}</p>
    </div>

    <div style="margin-bottom: 20px">
      <label>
        <input v-model="formData.rememberMe" type="checkbox" />
        记住我
      </label>
      <p>当前值: {{ formData.rememberMe }}</p>
    </div>

    <button @click="testData">测试数据</button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const formData = ref({
  username: '',
  password: '',
  rememberMe: false,
})

const testData = () => {
  console.log('测试数据:', formData.value)
  alert(
    `用户名: ${formData.value.username}, 密码: ${formData.value.password}, 记住我: ${formData.value.rememberMe}`
  )
}
</script>
