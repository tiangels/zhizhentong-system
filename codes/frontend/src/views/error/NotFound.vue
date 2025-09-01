<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ExclamationCircleOutlined } from '@ant-design/icons-vue'

const router = useRouter()

const goHome = () => {
  router.push('/')
}

const goBack = () => {
  router.go(-1)
}
</script>

<template>
  <div class="not-found-page">
    <div class="not-found-content">
      <div class="not-found-icon">
        <ExclamationCircleOutlined />
      </div>
      <h1 class="not-found-title">404</h1>
      <p class="not-found-subtitle">页面不存在</p>
      <p class="not-found-description">抱歉，您访问的页面不存在或已被删除。</p>
      <div class="not-found-actions">
        <a-button type="primary" @click="goHome"> 返回首页 </a-button>
        <a-button @click="goBack"> 返回上页 </a-button>
      </div>
    </div>
  </div>
</template>

<style lang="less" scoped>
.not-found-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: @bg-color;
  padding: @spacing-lg;
}

.not-found-content {
  text-align: center;
  max-width: 500px;
}

.not-found-icon {
  font-size: 120px;
  color: @primary-color;
  margin-bottom: @spacing-lg;
  opacity: 0.8;
}

.not-found-title {
  font-size: 72px;
  font-weight: @font-weight-bold;
  color: @text-color;
  margin: 0 0 @spacing-sm 0;
}

.not-found-subtitle {
  font-size: @font-size-xl;
  color: @text-color;
  margin: 0 0 @spacing-md 0;
}

.not-found-description {
  font-size: @font-size-base;
  color: @text-color-secondary;
  margin: 0 0 @spacing-xl 0;
  line-height: 1.6;
}

.not-found-actions {
  display: flex;
  gap: @spacing-md;
  justify-content: center;

  .ant-btn {
    min-width: 120px;
  }
}
</style>
