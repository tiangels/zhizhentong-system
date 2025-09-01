<script setup lang="ts">
// 认证页面布局组件
</script>

<template>
  <div class="auth-layout">
    <div class="auth-container">
      <div class="auth-header">
        <h1 class="auth-title">智诊通</h1>
        <p class="auth-subtitle">多模态智能医生问诊系统</p>
      </div>
      <div class="auth-content">
        <router-view />
      </div>
    </div>
  </div>
</template>

<style lang="less" scoped>
.auth-layout {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, @primary-color 0%, @primary-color-light 100%);
  padding: @spacing-lg;
}

.auth-container {
  width: 100%;
  max-width: 400px;
  background: @card-bg;
  border-radius: @border-radius-lg;
  box-shadow: @box-shadow-lg;
  overflow: hidden;
}

.auth-header {
  text-align: center;
  padding: @spacing-xl @spacing-lg @spacing-lg;
  background: @primary-color;
  color: white;

  .auth-title {
    font-size: @font-size-2xl;
    font-weight: @font-weight-bold;
    margin: 0 0 @spacing-xs 0;
  }

  .auth-subtitle {
    font-size: @font-size-base;
    margin: 0;
    opacity: 0.9;
  }
}

.auth-content {
  padding: @spacing-xl;
}
</style>
