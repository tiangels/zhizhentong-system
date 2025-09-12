<script setup lang="ts">
import { defineAsyncComponent } from 'vue'

const MainLayout = defineAsyncComponent(() => import('./MainLayout.vue'))
</script>

<template>
  <div class="auth-layout">
    <MainLayout />
  </div>
</template>

<style scoped>
.auth-layout {
  width: 100%;
  height: 100vh;
}
</style>
