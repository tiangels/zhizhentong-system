<template>
  <div class="patient-management">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1>就诊人管理</h1>
      <p class="subtitle">管理您和家人的就诊档案，实现精准医疗检索</p>
    </div>

    <!-- 添加就诊人按钮 -->
    <div class="action-bar">
      <a-button type="primary" @click="openAddPatientDialog">
        <template #icon><PlusOutlined /></template>
        添加就诊人
      </a-button>
      <a-button type="primary" @click="showSearchDialog = true">
        <template #icon><SearchOutlined /></template>
        精准检索
      </a-button>
    </div>

    <!-- 就诊人列表 -->
    <div class="patient-list">
      <a-card
        v-for="patient in patients"
        :key="patient.patient_unique_id"
        class="patient-card"
        :class="{ 'active-patient': currentPatientId === patient.patient_unique_id }"
        @click="selectPatient(patient)"
      >
        <div class="patient-header">
          <div class="patient-info">
            <h3>{{ patient.name }}</h3>
            <p class="relationship">{{ getRelationshipText(patient.relationship) }}</p>
          </div>
          <div class="patient-actions">
            <a-button size="small" type="link" @click.stop="editPatient(patient)"> 编辑 </a-button>
            <a-button size="small" type="link" @click.stop="viewRecords(patient)">
              查看记录
            </a-button>
          </div>
        </div>

        <div class="patient-details">
          <div class="detail-item">
            <span class="label">年龄:</span>
            <span class="value">{{ patient.age || '未填写' }}</span>
          </div>
          <div class="detail-item">
            <span class="label">性别:</span>
            <span class="value">{{ patient.gender || '未填写' }}</span>
          </div>
          <div class="detail-item">
            <span class="label">手机号:</span>
            <span class="value">{{ patient.phone || '未填写' }}</span>
          </div>
        </div>

        <div class="patient-tags">
          <a-tag v-if="patient.medical_history" color="blue"> 有病史 </a-tag>
          <a-tag v-if="patient.allergies" color="orange"> 有过敏 </a-tag>
        </div>
      </a-card>
    </div>

    <!-- 添加/编辑就诊人对话框 -->
    <a-modal
      :title="editingPatient ? '编辑就诊人' : '添加就诊人'"
      :open="showAddPatientDialog"
      @cancel="handleCancelDialog"
      @after-open-change="handleDialogOpenChange"
      width="600px"
    >
      <a-form
        :model="patientForm"
        :rules="patientRules"
        ref="patientFormRef"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 18 }"
        :validate-trigger="['blur', 'change']"
      >
        <a-form-item label="姓名" name="name">
          <a-input v-model="patientForm.name" placeholder="请输入姓名" />
        </a-form-item>

        <a-form-item label="关系" name="relationship">
          <a-select v-model="patientForm.relationship" placeholder="请选择关系">
            <a-select-option value="self">本人</a-select-option>
            <a-select-option value="spouse">配偶</a-select-option>
            <a-select-option value="child">子女</a-select-option>
            <a-select-option value="parent">父母</a-select-option>
            <a-select-option value="other">其他</a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="年龄" name="age">
          <a-input-number
            v-model="patientForm.age"
            :min="0"
            :max="120"
            placeholder="请输入年龄"
            style="width: 100%"
          />
        </a-form-item>

        <a-form-item label="性别" name="gender">
          <a-radio-group v-model="patientForm.gender">
            <a-radio value="男">男</a-radio>
            <a-radio value="女">女</a-radio>
          </a-radio-group>
        </a-form-item>

        <a-form-item label="身份证号" name="id_card">
          <a-input v-model="patientForm.id_card" placeholder="请输入身份证号" />
        </a-form-item>

        <a-form-item label="手机号" name="phone">
          <a-input v-model="patientForm.phone" placeholder="请输入手机号" />
        </a-form-item>

        <a-form-item label="既往病史">
          <a-textarea
            v-model="patientForm.medical_history"
            :rows="3"
            placeholder="请输入既往病史"
          />
        </a-form-item>

        <a-form-item label="过敏史">
          <a-textarea v-model="patientForm.allergies" :rows="2" placeholder="请输入过敏史" />
        </a-form-item>

        <a-form-item label="当前用药">
          <a-textarea
            v-model="patientForm.medications"
            :rows="2"
            placeholder="请输入当前用药情况"
          />
        </a-form-item>
      </a-form>

      <template #footer>
        <a-button @click="handleCancelDialog">取消</a-button>
        <a-button type="primary" @click="savePatient">保存</a-button>
      </template>
    </a-modal>

    <!-- 精准检索对话框 -->
    <a-modal
      title="精准医疗检索"
      :open="showSearchDialog"
      @cancel="showSearchDialog = false"
      width="800px"
    >
      <div class="search-form">
        <a-form :model="searchForm" :label-col="{ span: 6 }" :wrapper-col="{ span: 18 }">
          <a-form-item label="检索内容">
            <a-textarea
              v-model="searchForm.query"
              :rows="3"
              placeholder="请输入症状、疾病、用药等关键词..."
            />
          </a-form-item>

          <a-form-item label="就诊人">
            <a-select
              v-model="searchForm.patient_unique_ids"
              mode="multiple"
              placeholder="选择就诊人（不选则搜索所有）"
            >
              <a-select-option
                v-for="patient in patients"
                :key="patient.patient_unique_id"
                :value="patient.patient_unique_id"
              >
                {{ patient.name }}
              </a-select-option>
            </a-select>
          </a-form-item>

          <a-form-item label="科室">
            <a-select v-model="searchForm.department" placeholder="选择科室">
              <a-select-option value="内科">内科</a-select-option>
              <a-select-option value="外科">外科</a-select-option>
              <a-select-option value="儿科">儿科</a-select-option>
              <a-select-option value="妇科">妇科</a-select-option>
              <a-select-option value="心血管内科">心血管内科</a-select-option>
              <a-select-option value="神经内科">神经内科</a-select-option>
            </a-select>
          </a-form-item>

          <a-form-item label="记录类型">
            <a-select v-model="searchForm.record_type" placeholder="选择记录类型">
              <a-select-option value="visit">就诊记录</a-select-option>
              <a-select-option value="diagnosis">诊断记录</a-select-option>
              <a-select-option value="treatment">治疗记录</a-select-option>
              <a-select-option value="prescription">处方记录</a-select-option>
            </a-select>
          </a-form-item>
        </a-form>
      </div>

      <template #footer>
        <a-button @click="showSearchDialog = false">取消</a-button>
        <a-button type="primary" @click="performSearch">开始检索</a-button>
      </template>
    </a-modal>

    <!-- 检索结果 -->
    <div v-if="searchResults.length > 0" class="search-results">
      <h3>检索结果 ({{ searchResults.length }} 条)</h3>
      <div class="result-list">
        <a-card v-for="result in searchResults" :key="result.id" class="result-card">
          <div class="result-header">
            <h4>{{ result.title }}</h4>
            <span class="result-score">相关度: {{ (result._hybrid_score * 100).toFixed(1) }}%</span>
          </div>

          <div class="result-content">
            <p><strong>就诊人:</strong> {{ result.patient_name }}</p>
            <p><strong>科室:</strong> {{ result.department }}</p>
            <p><strong>医生:</strong> {{ result.doctor }}</p>
            <p><strong>就诊时间:</strong> {{ result.visit_date }}</p>

            <div v-if="result.symptoms" class="symptoms">
              <strong>症状:</strong> {{ result.symptoms }}
            </div>

            <div v-if="result.diagnosis" class="diagnosis">
              <strong>诊断:</strong> {{ result.diagnosis }}
            </div>

            <div v-if="result.treatment" class="treatment">
              <strong>治疗:</strong> {{ result.treatment }}
            </div>
          </div>
        </a-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined, SearchOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { get, post, put } from '@/services/api'

// 响应式数据
const patients = ref([])
const currentPatientId = ref(null)
const showAddPatientDialog = ref(false)
const showSearchDialog = ref(false)
const editingPatient = ref(null)
const searchResults = ref([])
const patientFormRef = ref(null)

// 就诊人表单
const patientForm = ref({
  name: '',
  relationship: 'self',
  age: undefined, // 改为 undefined，这样 a-input-number 组件可以正确处理
  gender: '', // 改为空字符串而不是 null
  id_card: '',
  phone: '',
  medical_history: '',
  allergies: '',
  medications: '',
})

// 表单验证规则
const patientRules = {
  name: [{ required: true, message: '请输入姓名', trigger: ['blur', 'change'] }],
  relationship: [{ required: true, message: '请选择关系', trigger: ['blur', 'change'] }],
  age: [
    { required: true, message: '请输入年龄', trigger: ['blur', 'change'] },
    {
      validator: (rule, value) => {
        if (!value && value !== 0) {
          return Promise.reject('请输入年龄')
        }
        if (value < 0 || value > 120) {
          return Promise.reject('请输入0-120之间的整数')
        }
        return Promise.resolve()
      },
      trigger: ['blur', 'change'],
    },
  ],
  gender: [
    {
      validator: (rule, value) => {
        if (!value || value === null || value === undefined) {
          return Promise.reject('请选择性别')
        }
        return Promise.resolve()
      },
      trigger: ['blur', 'change'],
    },
  ],
  id_card: [
    { required: true, message: '请输入身份证号', trigger: ['blur', 'change'] },
    {
      pattern:
        /^[1-9]\d{5}(18|19|20)\d{2}((0[1-9])|(1[0-2]))(([0-2][1-9])|10|20|30|31)\d{3}[0-9Xx]$/,
      message: '请输入正确的身份证号',
      trigger: ['blur', 'change'],
    },
  ],
  phone: [
    { required: true, message: '请输入手机号', trigger: ['blur', 'change'] },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: ['blur', 'change'] },
  ],
}

// 搜索表单
const searchForm = ref({
  query: '',
  patient_unique_ids: [],
  department: '',
  record_type: '',
})

// 获取认证store
const authStore = useAuthStore()

// 使用统一的API服务，无需额外配置

onMounted(() => {
  loadPatients()
})

// 方法定义
const loadPatients = async () => {
  try {
    const response = await get('/patients/')
    console.log('患者列表响应:', response)
    patients.value = response.patients || []
  } catch (error) {
    message.error('加载就诊人列表失败')
    console.error('加载患者列表错误:', error)
  }
}

// 选择就诊人
const selectPatient = patient => {
  currentPatientId.value = patient.patient_unique_id
  // emit('patient-selected', patient)
}

// 打开添加就诊人对话框
const openAddPatientDialog = () => {
  resetForm()
  showAddPatientDialog.value = true
}

// 编辑就诊人
const editPatient = patient => {
  editingPatient.value = patient

  // 确保所有字段都有正确的值
  patientForm.value = {
    name: patient.name || '',
    relationship: patient.relationship || 'self',
    age: patient.age || undefined,
    gender: patient.gender || '', // 确保性别字段是字符串或空字符串
    id_card: patient.id_card || '',
    phone: patient.phone || '',
    medical_history: patient.medical_history || '',
    allergies: patient.allergies || '',
    medications: patient.medications || '',
  }

  console.log('编辑患者数据:', patient)
  console.log('表单数据:', patientForm.value)

  showAddPatientDialog.value = true

  // 清除验证状态，因为我们已经在编辑现有数据
  nextTick(() => {
    if (patientFormRef.value) {
      patientFormRef.value.clearValidate()
    }
  })
}

// 查看记录
const viewRecords = patient => {
  // router.push({
  //   name: 'PatientRecords',
  //   params: { patientId: patient.patient_unique_id },
  // })
  message.info('查看记录功能待开发')
}

// 保存就诊人
const savePatient = async () => {
  try {
    console.log('=== 保存就诊人调试信息 ===')
    console.log('当前表单数据:', JSON.stringify(patientForm.value, null, 2))

    // 手动验证表单
    await patientFormRef.value.validate()

    // 发送请求
    if (editingPatient.value) {
      await put(`/patients/${editingPatient.value.patient_unique_id}/`, patientForm.value)
    } else {
      await post('/patients/', patientForm.value)
    }

    message.success('保存成功')
    showAddPatientDialog.value = false
    loadPatients()
    resetForm()
  } catch (error) {
    // 如果是表单验证错误，不显示错误消息，让用户看到具体的验证提示
    if (error.errorFields && error.errorFields.length > 0) {
      console.log('表单验证失败:', error)
      console.log('验证失败的字段:', error.errorFields)
      return
    }

    // 网络或其他错误
    message.error('保存失败：' + (error.message || '未知错误'))
    console.error('保存就诊人失败:', error)
  }
}

// 重置表单
const resetForm = () => {
  patientForm.value = {
    name: '',
    relationship: 'self',
    age: undefined, // 改为 undefined
    gender: '', // 改为空字符串
    id_card: '',
    phone: '',
    medical_history: '',
    allergies: '',
    medications: '',
  }
  editingPatient.value = null

  // 清除表单验证状态 - 使用 nextTick 确保在 DOM 更新后执行
  nextTick(() => {
    if (patientFormRef.value) {
      patientFormRef.value.clearValidate()
    }
  })
}

// 处理对话框取消
const handleCancelDialog = () => {
  showAddPatientDialog.value = false
  resetForm()
}

// 处理对话框打开状态变化
const handleDialogOpenChange = open => {
  if (open) {
    // 对话框打开时，确保清除验证状态
    nextTick(() => {
      if (patientFormRef.value) {
        patientFormRef.value.clearValidate()
        // 重新验证一次以确保状态正确
        setTimeout(() => {
          patientFormRef.value?.validate()?.catch(() => {}) // 忽略验证错误，只是触发验证
        }, 100)
      }
    })
  }
}

// 执行精准检索
const performSearch = async () => {
  try {
    const response = await post('/knowledge/query', {
      query: searchForm.value.query,
      patient_unique_ids:
        searchForm.value.patient_unique_ids.length > 0 ? searchForm.value.patient_unique_ids : null,
      top_k: 20,
    })

    searchResults.value = response.data?.hybrid_results || response.data?.results || []
    showSearchDialog.value = false

    if (searchResults.value.length === 0) {
      message.info('未找到相关记录')
    } else {
      message.success(`找到 ${searchResults.value.length} 条相关记录`)
    }
  } catch (error) {
    message.error('检索失败')
    console.error(error)
  }
}

// 获取关系文本
const getRelationshipText = relationship => {
  const relationshipMap = {
    self: '本人',
    spouse: '配偶',
    child: '子女',
    parent: '父母',
    other: '其他',
  }
  return relationshipMap[relationship] || '未知'
}
</script>

<style scoped>
.patient-management {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 30px;
  text-align: center;
}

.page-header h1 {
  color: #2c3e50;
  margin-bottom: 10px;
  font-size: 28px;
  font-weight: 600;
}

.subtitle {
  color: #7f8c8d;
  font-size: 14px;
}

.action-bar {
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
}

.patient-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.patient-card {
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.patient-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.active-patient {
  border-color: #409eff;
  background-color: #f0f9ff;
}

.patient-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
}

.patient-info h3 {
  margin: 0 0 5px 0;
  color: #2c3e50;
}

.relationship {
  color: #7f8c8d;
  font-size: 12px;
  margin: 0;
}

.patient-actions {
  display: flex;
  gap: 5px;
}

.patient-details {
  margin-bottom: 15px;
}

.detail-item {
  display: flex;
  margin-bottom: 5px;
}

.detail-item .label {
  width: 60px;
  color: #7f8c8d;
  font-size: 12px;
}

.detail-item .value {
  color: #2c3e50;
  font-size: 12px;
}

.patient-tags {
  display: flex;
  gap: 5px;
}

.search-results {
  margin-top: 30px;
}

.search-results h3 {
  color: #2c3e50;
  margin-bottom: 20px;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.result-card {
  border-left: 4px solid #409eff;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.result-header h4 {
  margin: 0;
  color: #2c3e50;
}

.result-score {
  color: #409eff;
  font-size: 12px;
  font-weight: bold;
}

.result-content p {
  margin: 5px 0;
  font-size: 14px;
}

.symptoms,
.diagnosis,
.treatment {
  margin-top: 10px;
  padding: 8px;
  background-color: #f8f9fa;
  border-radius: 4px;
  font-size: 13px;
}

.search-form {
  margin-bottom: 20px;
}
</style>
