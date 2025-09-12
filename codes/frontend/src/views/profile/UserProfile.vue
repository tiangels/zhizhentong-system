<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useAuthStore } from '../../stores/auth'

const authStore = useAuthStore()

// 编辑状态
const isEditing = ref(false)
const showChangePassword = ref(false)

// 个人信息表单
const profileForm = reactive({
  username: '',
  email: '',
  phone: '',
})

// 密码表单
const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
})

// 用户统计
const userStats = ref({
  totalChats: 0,
  daysActive: 0,
  lastLogin: '未知',
})

// 开始编辑
const startEdit = () => {
  // 填充表单数据
  profileForm.username = authStore.user?.username || ''
  profileForm.email = authStore.user?.email || ''
  profileForm.phone = authStore.user?.phone || ''
  isEditing.value = true
}

// 保存个人信息
const saveProfile = async () => {
  try {
    // 这里应该调用API更新用户信息
    // await authStore.updateProfile(profileForm)

    // 暂时模拟成功
    console.log('保存个人信息:', profileForm)
    isEditing.value = false

    // 显示成功提示
    alert('个人信息更新成功！')
  } catch (error) {
    console.error('保存个人信息失败:', error)
    alert('保存失败，请重试')
  }
}

// 取消编辑
const cancelEdit = () => {
  isEditing.value = false
  // 重置表单
  Object.assign(profileForm, {
    username: authStore.user?.username || '',
    email: authStore.user?.email || '',
    phone: authStore.user?.phone || '',
  })
}

// 修改密码
const changePassword = async () => {
  try {
    // 验证密码
    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      alert('两次输入的新密码不一致')
      return
    }

    if (passwordForm.newPassword.length < 6) {
      alert('新密码长度不能少于6位')
      return
    }

    // 这里应该调用API修改密码
    // await authStore.changePassword(passwordForm)

    // 暂时模拟成功
    console.log('修改密码:', passwordForm)
    showChangePassword.value = false

    // 清空表单
    Object.assign(passwordForm, {
      currentPassword: '',
      newPassword: '',
      confirmPassword: '',
    })

    alert('密码修改成功！')
  } catch (error) {
    console.error('修改密码失败:', error)
    alert('修改失败，请重试')
  }
}

// 查看登录历史
const viewLoginHistory = () => {
  alert('登录历史功能开发中...')
}

// 格式化日期
const formatDate = (timestamp?: string) => {
  if (!timestamp) return '未知'
  return new Date(timestamp).toLocaleDateString('zh-CN')
}

// 加载用户统计
const loadUserStats = async () => {
  try {
    // 这里应该调用API获取用户统计
    // 暂时使用模拟数据
    userStats.value = {
      totalChats: 12,
      daysActive: 15,
      lastLogin: '2小时前',
    }
  } catch (error) {
    console.error('加载用户统计失败:', error)
  }
}

onMounted(async () => {
  await loadUserStats()

  // 初始化表单数据
  Object.assign(profileForm, {
    username: authStore.user?.username || '',
    email: authStore.user?.email || '',
    phone: authStore.user?.phone || '',
  })
})
</script>

<template>
  <div class="user-profile">
    <div class="profile-header">
      <h1>个人档案</h1>
      <p>管理您的个人信息和账户设置</p>
    </div>

    <div class="profile-content">
      <div class="profile-section">
        <h2>基本信息</h2>
        <div class="profile-form">
          <div class="form-group">
            <label>用户名</label>
            <input
              v-model="profileForm.username"
              type="text"
              class="form-input"
              :disabled="!isEditing"
            />
          </div>

          <div class="form-group">
            <label>邮箱</label>
            <input
              v-model="profileForm.email"
              type="email"
              class="form-input"
              :disabled="!isEditing"
            />
          </div>

          <div class="form-group">
            <label>手机号</label>
            <input
              v-model="profileForm.phone"
              type="tel"
              class="form-input"
              :disabled="!isEditing"
            />
          </div>

          <div class="form-group">
            <label>注册时间</label>
            <input
              :value="formatDate(authStore.user?.createdAt)"
              type="text"
              class="form-input"
              disabled
            />
          </div>

          <div class="form-actions">
            <button v-if="!isEditing" @click="startEdit" class="btn btn-primary">
              <i class="fas fa-edit"></i>
              编辑信息
            </button>
            <div v-else class="edit-actions">
              <button @click="saveProfile" class="btn btn-success">
                <i class="fas fa-save"></i>
                保存
              </button>
              <button @click="cancelEdit" class="btn btn-secondary">
                <i class="fas fa-times"></i>
                取消
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="profile-section">
        <h2>账户安全</h2>
        <div class="security-options">
          <div class="security-item">
            <div class="security-info">
              <h4>修改密码</h4>
              <p>定期更新密码以确保账户安全</p>
            </div>
            <button @click="showChangePassword = true" class="btn btn-outline">修改密码</button>
          </div>

          <div class="security-item">
            <div class="security-info">
              <h4>登录历史</h4>
              <p>查看最近的登录记录</p>
            </div>
            <button @click="viewLoginHistory" class="btn btn-outline">查看记录</button>
          </div>
        </div>
      </div>

      <div class="profile-section">
        <h2>使用统计</h2>
        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-icon">
              <i class="fas fa-comments"></i>
            </div>
            <div class="stat-content">
              <h3>{{ userStats.totalChats }}</h3>
              <p>总对话数</p>
            </div>
          </div>

          <div class="stat-item">
            <div class="stat-icon">
              <i class="fas fa-calendar"></i>
            </div>
            <div class="stat-content">
              <h3>{{ userStats.daysActive }}</h3>
              <p>活跃天数</p>
            </div>
          </div>

          <div class="stat-item">
            <div class="stat-icon">
              <i class="fas fa-clock"></i>
            </div>
            <div class="stat-content">
              <h3>{{ userStats.lastLogin }}</h3>
              <p>最后登录</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 修改密码弹窗 -->
    <div v-if="showChangePassword" class="modal-overlay" @click="showChangePassword = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>修改密码</h3>
          <button @click="showChangePassword = false" class="modal-close">
            <i class="fas fa-times"></i>
          </button>
        </div>

        <div class="modal-body">
          <div class="form-group">
            <label>当前密码</label>
            <input
              v-model="passwordForm.currentPassword"
              type="password"
              class="form-input"
              placeholder="请输入当前密码"
            />
          </div>

          <div class="form-group">
            <label>新密码</label>
            <input
              v-model="passwordForm.newPassword"
              type="password"
              class="form-input"
              placeholder="请输入新密码"
            />
          </div>

          <div class="form-group">
            <label>确认新密码</label>
            <input
              v-model="passwordForm.confirmPassword"
              type="password"
              class="form-input"
              placeholder="请再次输入新密码"
            />
          </div>
        </div>

        <div class="modal-footer">
          <button @click="showChangePassword = false" class="btn btn-secondary">取消</button>
          <button @click="changePassword" class="btn btn-primary">确认修改</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="less">
.user-profile {
  padding: 24px;
}

.profile-header {
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

.profile-content {
  display: grid;
  gap: 24px;
}

.profile-section {
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

.profile-form {
  .form-group {
    margin-bottom: 20px;

    label {
      display: block;
      margin-bottom: 8px;
      color: #333;
      font-weight: 500;
    }

    .form-input {
      width: 100%;
      padding: 12px 16px;
      border: 1px solid #d9d9d9;
      border-radius: 8px;
      font-size: 0.9rem;
      transition: border-color 0.3s;

      &:focus {
        outline: none;
        border-color: #1890ff;
      }

      &:disabled {
        background-color: #f5f5f5;
        color: #999;
        cursor: not-allowed;
      }
    }
  }
}

.form-actions {
  margin-top: 24px;

  .edit-actions {
    display: flex;
    gap: 12px;
  }
}

.security-options {
  .security-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 0;
    border-bottom: 1px solid #f0f0f0;

    &:last-child {
      border-bottom: none;
    }

    .security-info {
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
  }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;

  .stat-icon {
    width: 50px;
    height: 50px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 1.2rem;
  }

  .stat-content h3 {
    margin: 0 0 4px 0;
    color: #333;
    font-size: 1.5rem;
  }

  .stat-content p {
    margin: 0;
    color: #666;
    font-size: 0.9rem;
  }
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

  &.btn-success {
    background: #52c41a;
    color: white;

    &:hover {
      background: #73d13d;
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

// 弹窗样式
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #f0f0f0;

  h3 {
    margin: 0;
    color: #333;
  }

  .modal-close {
    background: none;
    border: none;
    font-size: 1.2rem;
    color: #999;
    cursor: pointer;
    padding: 4px;

    &:hover {
      color: #666;
    }
  }
}

.modal-body {
  padding: 24px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid #f0f0f0;
}

// 响应式设计
@media (max-width: 768px) {
  .user-profile {
    padding: 16px;
  }

  .profile-section {
    padding: 16px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .security-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style>
