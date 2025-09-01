<script setup lang="ts">
import { reactive, onMounted } from 'vue'
import { useUIStore } from '../../stores/ui'

const uiStore = useUIStore()

// 设置状态
const settings = reactive({
  theme: 'light',
  primaryColor: '#1890ff',
  messageNotifications: true,
  systemNotifications: true,
  emailNotifications: false,
  dataCollection: true,
  personalization: true,
  autoSave: true,
  messagePreview: true,
  inputSuggestions: true,
  debugMode: false,
  performanceMonitoring: false,
})

// 颜色选项
const colorOptions = [
  { value: '#1890ff', name: '蓝色' },
  { value: '#52c41a', name: '绿色' },
  { value: '#fa8c16', name: '橙色' },
  { value: '#f5222d', name: '红色' },
  { value: '#722ed1', name: '紫色' },
  { value: '#13c2c2', name: '青色' },
]

// 更新主题
const updateTheme = (event: Event) => {
  const theme = (event.target as HTMLSelectElement).value as 'light' | 'dark'
  uiStore.setTheme(theme)
  saveSettings()
}

// 更新主色调
const updatePrimaryColor = (color: string) => {
  settings.primaryColor = color
  // 暂时不调用UI store，因为还没有这个方法
  // uiStore.setPrimaryColor(color)
  saveSettings()
}

// 更新消息通知
const updateMessageNotifications = () => {
  saveSettings()
}

// 更新系统通知
const updateSystemNotifications = () => {
  saveSettings()
}

// 更新邮件通知
const updateEmailNotifications = () => {
  saveSettings()
}

// 更新数据收集
const updateDataCollection = () => {
  saveSettings()
}

// 更新个性化推荐
const updatePersonalization = () => {
  saveSettings()
}

// 更新自动保存
const updateAutoSave = () => {
  saveSettings()
}

// 更新消息预览
const updateMessagePreview = () => {
  saveSettings()
}

// 更新输入提示
const updateInputSuggestions = () => {
  saveSettings()
}

// 更新调试模式
const updateDebugMode = () => {
  saveSettings()
}

// 更新性能监控
const updatePerformanceMonitoring = () => {
  saveSettings()
}

// 保存设置
const saveSettings = () => {
  try {
    localStorage.setItem('app-settings', JSON.stringify(settings))
    console.log('设置已保存')
  } catch (error) {
    console.error('保存设置失败:', error)
  }
}

// 加载设置
const loadSettings = () => {
  try {
    const saved = localStorage.getItem('app-settings')
    if (saved) {
      const savedSettings = JSON.parse(saved)
      Object.assign(settings, savedSettings)
    }
  } catch (error) {
    console.error('加载设置失败:', error)
  }
}

// 恢复默认设置
const resetToDefaults = () => {
  if (confirm('确定要恢复默认设置吗？这将清除所有自定义设置。')) {
    Object.assign(settings, {
      theme: 'light',
      primaryColor: '#1890ff',
      messageNotifications: true,
      systemNotifications: true,
      emailNotifications: false,
      dataCollection: true,
      personalization: true,
      autoSave: true,
      messagePreview: true,
      inputSuggestions: true,
      debugMode: false,
      performanceMonitoring: false,
    })

    // 更新UI
    uiStore.setTheme(settings.theme as 'light' | 'dark')
    // 暂时不调用UI store，因为还没有这个方法
    // uiStore.setPrimaryColor(settings.primaryColor)

    // 保存设置
    saveSettings()

    alert('设置已恢复默认值')
  }
}

// 导出设置
const exportSettings = () => {
  try {
    const dataStr = JSON.stringify(settings, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'app-settings.json'
    link.click()
    URL.revokeObjectURL(url)
  } catch (error) {
    console.error('导出设置失败:', error)
    alert('导出失败，请重试')
  }
}

// 导入设置
const importSettings = () => {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.json'
  input.onchange = event => {
    const file = (event.target as HTMLInputElement).files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = e => {
        try {
          const importedSettings = JSON.parse(e.target?.result as string)
          Object.assign(settings, importedSettings)

          // 更新UI
          uiStore.setTheme(settings.theme as 'light' | 'dark')
          // 暂时不调用UI store，因为还没有这个方法
          // uiStore.setPrimaryColor(settings.primaryColor)

          // 保存设置
          saveSettings()

          alert('设置导入成功')
        } catch (error) {
          console.error('导入设置失败:', error)
          alert('导入失败，文件格式不正确')
        }
      }
      reader.readAsText(file)
    }
  }
  input.click()
}

onMounted(() => {
  loadSettings()

  // 同步UI状态
  uiStore.setTheme(settings.theme as 'light' | 'dark')
  // 暂时不调用UI store，因为还没有这个方法
  // uiStore.setPrimaryColor(settings.primaryColor)
})
</script>

<template>
  <div class="app-settings">
    <div class="settings-header">
      <h1>应用设置</h1>
      <p>自定义您的应用体验和偏好设置</p>
    </div>

    <div class="settings-content">
      <div class="settings-section">
        <h2>外观设置</h2>
        <div class="setting-item">
          <div class="setting-info">
            <h4>主题模式</h4>
            <p>选择您喜欢的主题外观</p>
          </div>
          <div class="setting-control">
            <select v-model="settings.theme" @change="updateTheme" class="setting-select">
              <option value="light">浅色主题</option>
              <option value="dark">深色主题</option>
              <option value="auto">跟随系统</option>
            </select>
          </div>
        </div>

        <div class="setting-item">
          <div class="setting-info">
            <h4>主色调</h4>
            <p>选择应用的主色调</p>
          </div>
          <div class="setting-control">
            <div class="color-options">
              <div
                v-for="color in colorOptions"
                :key="color.value"
                class="color-option"
                :class="[{ active: settings.primaryColor === color.value }]"
                :style="{ backgroundColor: color.value }"
                @click="updatePrimaryColor(color.value)"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <div class="settings-section">
        <h2>通知设置</h2>
        <div class="setting-item">
          <div class="setting-info">
            <h4>消息通知</h4>
            <p>接收新消息时的通知提醒</p>
          </div>
          <div class="setting-control">
            <label class="toggle-switch">
              <input
                type="checkbox"
                v-model="settings.messageNotifications"
                @change="updateMessageNotifications"
              />
              <span class="toggle-slider"></span>
            </label>
          </div>
        </div>

        <div class="setting-item">
          <div class="setting-info">
            <h4>系统通知</h4>
            <p>接收系统更新和维护通知</p>
          </div>
          <div class="setting-control">
            <label class="toggle-switch">
              <input
                type="checkbox"
                v-model="settings.systemNotifications"
                @change="updateSystemNotifications"
              />
              <span class="toggle-slider"></span>
            </label>
          </div>
        </div>

        <div class="setting-item">
          <div class="setting-info">
            <h4>邮件通知</h4>
            <p>通过邮件接收重要通知</p>
          </div>
          <div class="setting-control">
            <label class="toggle-switch">
              <input
                type="checkbox"
                v-model="settings.emailNotifications"
                @change="updateEmailNotifications"
              />
              <span class="toggle-slider"></span>
            </label>
          </div>
        </div>
      </div>

      <div class="settings-section">
        <h2>隐私设置</h2>
        <div class="setting-item">
          <div class="setting-info">
            <h4>数据收集</h4>
            <p>允许收集匿名使用数据以改进服务</p>
          </div>
          <div class="setting-control">
            <label class="toggle-switch">
              <input
                type="checkbox"
                v-model="settings.dataCollection"
                @change="updateDataCollection"
              />
              <span class="toggle-slider"></span>
            </label>
          </div>
        </div>

        <div class="setting-item">
          <div class="setting-info">
            <h4>个性化推荐</h4>
            <p>基于使用习惯提供个性化内容推荐</p>
          </div>
          <div class="setting-control">
            <label class="toggle-switch">
              <input
                type="checkbox"
                v-model="settings.personalization"
                @change="updatePersonalization"
              />
              <span class="toggle-slider"></span>
            </label>
          </div>
        </div>
      </div>

      <div class="settings-section">
        <h2>聊天设置</h2>
        <div class="setting-item">
          <div class="setting-info">
            <h4>自动保存</h4>
            <p>自动保存聊天记录到本地</p>
          </div>
          <div class="setting-control">
            <label class="toggle-switch">
              <input type="checkbox" v-model="settings.autoSave" @change="updateAutoSave" />
              <span class="toggle-slider"></span>
            </label>
          </div>
        </div>

        <div class="setting-item">
          <div class="setting-info">
            <h4>消息预览</h4>
            <p>在通知中显示消息内容预览</p>
          </div>
          <div class="setting-control">
            <label class="toggle-switch">
              <input
                type="checkbox"
                v-model="settings.messagePreview"
                @change="updateMessagePreview"
              />
              <span class="toggle-slider"></span>
            </label>
          </div>
        </div>

        <div class="setting-item">
          <div class="setting-info">
            <h4>输入提示</h4>
            <p>显示智能输入提示和建议</p>
          </div>
          <div class="setting-control">
            <label class="toggle-switch">
              <input
                type="checkbox"
                v-model="settings.inputSuggestions"
                @change="updateInputSuggestions"
              />
              <span class="toggle-slider"></span>
            </label>
          </div>
        </div>
      </div>

      <div class="settings-section">
        <h2>高级设置</h2>
        <div class="setting-item">
          <div class="setting-info">
            <h4>调试模式</h4>
            <p>启用调试信息和控制台日志</p>
          </div>
          <div class="setting-control">
            <label class="toggle-switch">
              <input type="checkbox" v-model="settings.debugMode" @change="updateDebugMode" />
              <span class="toggle-slider"></span>
            </label>
          </div>
        </div>

        <div class="setting-item">
          <div class="setting-info">
            <h4>性能监控</h4>
            <p>监控应用性能并收集性能数据</p>
          </div>
          <div class="setting-control">
            <label class="toggle-switch">
              <input
                type="checkbox"
                v-model="settings.performanceMonitoring"
                @change="updatePerformanceMonitoring"
              />
              <span class="toggle-slider"></span>
            </label>
          </div>
        </div>
      </div>

      <div class="settings-actions">
        <button @click="resetToDefaults" class="btn btn-secondary">
          <i class="fas fa-undo"></i>
          恢复默认设置
        </button>
        <button @click="exportSettings" class="btn btn-outline">
          <i class="fas fa-download"></i>
          导出设置
        </button>
        <button @click="importSettings" class="btn btn-outline">
          <i class="fas fa-upload"></i>
          导入设置
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped lang="less">
.app-settings {
  padding: 24px;
}

.settings-header {
  margin-bottom: 32px;

  h1 {
    margin: 0 0 8px 0;
    color: #333;
    font-size: 2rem;
  }

  p {
    margin: 0;
    color: #666;
    font-size: 1.1rem;
  }
}

.settings-content {
  display: grid;
  gap: 24px;
}

.settings-section {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

  h2 {
    margin: 0 0 20px 0;
    color: #333;
    font-size: 1.3rem;
    border-bottom: 2px solid #f0f0f0;
    padding-bottom: 12px;
  }
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid #f0f0f0;

  &:last-child {
    border-bottom: none;
  }

  .setting-info {
    flex: 1;

    h4 {
      margin: 0 0 4px 0;
      color: #333;
      font-size: 1rem;
    }

    p {
      margin: 0;
      color: #666;
      font-size: 0.9rem;
    }
  }

  .setting-control {
    flex-shrink: 0;
  }
}

.setting-select {
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 0.9rem;
  background: white;
  cursor: pointer;

  &:focus {
    outline: none;
    border-color: #1890ff;
  }
}

.color-options {
  display: flex;
  gap: 8px;
}

.color-option {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.3s;

  &:hover {
    transform: scale(1.1);
  }

  &.active {
    border-color: #333;
    transform: scale(1.1);
  }
}

// 开关样式
.toggle-switch {
  position: relative;
  display: inline-block;
  width: 50px;
  height: 24px;

  input {
    opacity: 0;
    width: 0;
    height: 0;

    &:checked + .toggle-slider {
      background-color: #1890ff;
    }

    &:checked + .toggle-slider:before {
      transform: translateX(26px);
    }
  }
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: 0.3s;
  border-radius: 24px;

  &:before {
    position: absolute;
    content: '';
    height: 18px;
    width: 18px;
    left: 3px;
    bottom: 3px;
    background-color: white;
    transition: 0.3s;
    border-radius: 50%;
  }
}

.settings-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  padding: 24px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.3s;
  display: inline-flex;
  align-items: center;
  gap: 8px;

  &.btn-primary {
    background: #1890ff;
    color: white;

    &:hover {
      background: #40a9ff;
    }
  }

  &.btn-secondary {
    background: #f5f5f5;
    color: #666;
    border: 1px solid #d9d9d9;

    &:hover {
      background: #e6e6e6;
    }
  }

  &.btn-outline {
    background: white;
    color: #1890ff;
    border: 1px solid #1890ff;

    &:hover {
      background: #f0f8ff;
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .app-settings {
    padding: 16px;
  }

  .settings-section {
    padding: 16px;
  }

  .setting-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;

    .setting-control {
      align-self: flex-end;
    }
  }

  .settings-actions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
