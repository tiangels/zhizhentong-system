# 智诊通系统 - 词向量模型集成指南

## 🎯 集成目标

将词向量模型集成到智诊通系统中，实现基于医疗知识库的智能检索和问答功能。

## 📋 集成步骤

### 1. 后端集成

#### 1.1 创建RAG服务模块

在智诊通后端创建 `backend/app/services/rag_service.py`:

```python
import os
import logging
from typing import List, Dict, Any
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document

logger = logging.getLogger(__name__)

class MedicalRAGService:
    """医疗知识检索增强生成服务"""
    
    def __init__(self):
        self.embeddings = None
        self.vector_db = None
        self._initialize_rag()
    
    def _initialize_rag(self):
        """初始化RAG服务"""
        try:
            # 向量数据库路径
            db_path = os.path.join(
                os.path.dirname(__file__), 
                "../../ai_models/embedding_models/vector_database/chroma_db"
            )
            
            if not os.path.exists(db_path):
                logger.warning(f"向量数据库不存在: {db_path}")
                return
            
            # 初始化嵌入模型
            self.embeddings = HuggingFaceEmbeddings(
                model_name="shibing624/text2vec-base-chinese",
                model_kwargs={"device": "cpu"}
            )
            
            # 加载向量数据库
            self.vector_db = Chroma(
                persist_directory=db_path,
                embedding_function=self.embeddings
            )
            
            logger.info("RAG服务初始化成功")
            
        except Exception as e:
            logger.error(f"RAG服务初始化失败: {e}")
            self.embeddings = None
            self.vector_db = None
    
    def is_available(self) -> bool:
        """检查RAG服务是否可用"""
        return self.vector_db is not None
    
    def search_medical_cases(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """搜索相似医疗病例"""
        if not self.is_available():
            return []
        
        try:
            results = self.vector_db.similarity_search(query, k=k)
            
            return [
                {
                    "content": result.page_content,
                    "metadata": result.metadata,
                    "relevance_score": self._calculate_relevance_score(query, result.page_content)
                }
                for result in results
            ]
        except Exception as e:
            logger.error(f"搜索医疗病例失败: {e}")
            return []
    
    def search_with_score(self, query: str, k: int = 5, score_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """带相似度分数的搜索"""
        if not self.is_available():
            return []
        
        try:
            results = self.vector_db.similarity_search_with_score(query, k=k)
            
            filtered_results = []
            for doc, score in results:
                if score >= score_threshold:  # ChromaDB返回的是距离，越小越相似
                    filtered_results.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "similarity_score": 1 - score,  # 转换为相似度分数
                        "distance": score
                    })
            
            return filtered_results
        except Exception as e:
            logger.error(f"带分数搜索失败: {e}")
            return []
    
    def _calculate_relevance_score(self, query: str, content: str) -> float:
        """计算相关性分数（简单实现）"""
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        
        if not query_words:
            return 0.0
        
        intersection = query_words.intersection(content_words)
        return len(intersection) / len(query_words)
    
    def get_medical_advice(self, symptoms: str, context: str = "") -> Dict[str, Any]:
        """获取医疗建议"""
        if not self.is_available():
            return {"error": "RAG服务不可用"}
        
        # 构建查询
        query = f"{symptoms} {context}".strip()
        
        # 搜索相关病例
        similar_cases = self.search_medical_cases(query, k=3)
        
        if not similar_cases:
            return {"error": "未找到相关医疗信息"}
        
        # 提取关键信息
        advice = {
            "query": query,
            "similar_cases": similar_cases,
            "summary": self._generate_summary(similar_cases),
            "recommendations": self._extract_recommendations(similar_cases)
        }
        
        return advice
    
    def _generate_summary(self, cases: List[Dict[str, Any]]) -> str:
        """生成病例摘要"""
        if not cases:
            return "无相关病例信息"
        
        # 简单的摘要生成逻辑
        contents = [case["content"][:200] for case in cases[:2]]
        return "基于相似病例分析：" + "；".join(contents)
    
    def _extract_recommendations(self, cases: List[Dict[str, Any]]) -> List[str]:
        """提取治疗建议"""
        recommendations = []
        
        for case in cases:
            content = case["content"]
            # 简单的关键词提取
            if "建议" in content:
                recommendations.append("请参考相似病例的治疗建议")
            if "检查" in content:
                recommendations.append("建议进行相关检查")
            if "治疗" in content:
                recommendations.append("建议咨询专业医生制定治疗方案")
        
        return list(set(recommendations))  # 去重

# 全局RAG服务实例
rag_service = MedicalRAGService()
```

#### 1.2 创建API接口

在 `backend/app/api/medical.py` 中添加RAG相关接口:

```python
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.services.rag_service import rag_service
from app.core.auth import get_current_user

router = APIRouter()

class MedicalQueryRequest(BaseModel):
    symptoms: str
    context: Optional[str] = ""
    k: Optional[int] = 5

class MedicalQueryResponse(BaseModel):
    query: str
    similar_cases: List[Dict[str, Any]]
    summary: str
    recommendations: List[str]
    success: bool
    error: Optional[str] = None

@router.post("/search-cases", response_model=MedicalQueryResponse)
async def search_medical_cases(
    request: MedicalQueryRequest,
    current_user: dict = Depends(get_current_user)
):
    """搜索相似医疗病例"""
    try:
        if not rag_service.is_available():
            raise HTTPException(
                status_code=503, 
                detail="医疗知识库服务不可用"
            )
        
        # 搜索相似病例
        similar_cases = rag_service.search_medical_cases(
            request.symptoms, 
            k=request.k
        )
        
        # 生成建议
        advice = rag_service.get_medical_advice(
            request.symptoms, 
            request.context
        )
        
        return MedicalQueryResponse(
            query=request.symptoms,
            similar_cases=similar_cases,
            summary=advice.get("summary", ""),
            recommendations=advice.get("recommendations", []),
            success=True
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"搜索失败: {str(e)}"
        )

@router.get("/rag-status")
async def get_rag_status(current_user: dict = Depends(get_current_user)):
    """获取RAG服务状态"""
    return {
        "available": rag_service.is_available(),
        "status": "ready" if rag_service.is_available() else "not_ready"
    }
```

#### 1.3 更新依赖

在 `backend/requirements.txt` 中添加:

```txt
langchain==0.1.0
langchain-community==0.0.10
chromadb==0.4.18
sentence-transformers==2.2.2
```

### 2. 前端集成

#### 2.1 创建RAG服务API

在 `frontend/src/services/ragService.ts` 中:

```typescript
import { apiClient } from './apiClient'

export interface MedicalCase {
  content: string
  metadata: any
  relevance_score: number
}

export interface MedicalQueryRequest {
  symptoms: string
  context?: string
  k?: number
}

export interface MedicalQueryResponse {
  query: string
  similar_cases: MedicalCase[]
  summary: string
  recommendations: string[]
  success: boolean
  error?: string
}

export class RAGService {
  /**
   * 搜索相似医疗病例
   */
  static async searchMedicalCases(
    request: MedicalQueryRequest
  ): Promise<MedicalQueryResponse> {
    try {
      const response = await apiClient.post('/medical/search-cases', request)
      return response.data
    } catch (error) {
      console.error('搜索医疗病例失败:', error)
      throw error
    }
  }

  /**
   * 获取RAG服务状态
   */
  static async getRAGStatus(): Promise<{ available: boolean; status: string }> {
    try {
      const response = await apiClient.get('/medical/rag-status')
      return response.data
    } catch (error) {
      console.error('获取RAG状态失败:', error)
      return { available: false, status: 'error' }
    }
  }
}
```

#### 2.2 创建医疗咨询组件

在 `frontend/src/components/MedicalConsultation.vue` 中:

```vue
<template>
  <div class="medical-consultation">
    <div class="consultation-header">
      <h3>智能医疗咨询</h3>
      <div class="rag-status" :class="{ 'available': ragStatus.available }">
        <span class="status-indicator"></span>
        {{ ragStatus.available ? '知识库已就绪' : '知识库未就绪' }}
      </div>
    </div>

    <div class="consultation-form">
      <el-form :model="queryForm" @submit.prevent="handleSearch">
        <el-form-item label="症状描述">
          <el-input
            v-model="queryForm.symptoms"
            type="textarea"
            :rows="3"
            placeholder="请描述您的症状，如：胸痛、发热、咳嗽等"
            :disabled="!ragStatus.available"
          />
        </el-form-item>
        
        <el-form-item label="补充信息">
          <el-input
            v-model="queryForm.context"
            type="textarea"
            :rows="2"
            placeholder="其他相关信息（可选）"
            :disabled="!ragStatus.available"
          />
        </el-form-item>

        <el-form-item>
          <el-button 
            type="primary" 
            @click="handleSearch"
            :loading="loading"
            :disabled="!ragStatus.available"
          >
            智能分析
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <div v-if="searchResults" class="search-results">
      <div class="summary-section">
        <h4>分析摘要</h4>
        <p>{{ searchResults.summary }}</p>
      </div>

      <div class="recommendations-section">
        <h4>建议</h4>
        <ul>
          <li v-for="rec in searchResults.recommendations" :key="rec">
            {{ rec }}
          </li>
        </ul>
      </div>

      <div class="similar-cases-section">
        <h4>相似病例参考</h4>
        <div 
          v-for="(case_, index) in searchResults.similar_cases" 
          :key="index"
          class="case-item"
        >
          <div class="case-content">
            {{ case_.content.substring(0, 200) }}...
          </div>
          <div class="case-metadata">
            相关性: {{ (case_.relevance_score * 100).toFixed(1) }}%
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { RAGService, type MedicalQueryRequest, type MedicalQueryResponse } from '@/services/ragService'

const ragStatus = ref({ available: false, status: 'checking' })
const loading = ref(false)
const queryForm = ref<MedicalQueryRequest>({
  symptoms: '',
  context: '',
  k: 5
})
const searchResults = ref<MedicalQueryResponse | null>(null)

// 检查RAG服务状态
const checkRAGStatus = async () => {
  try {
    const status = await RAGService.getRAGStatus()
    ragStatus.value = status
  } catch (error) {
    ragStatus.value = { available: false, status: 'error' }
  }
}

// 搜索医疗病例
const handleSearch = async () => {
  if (!queryForm.value.symptoms.trim()) {
    ElMessage.warning('请输入症状描述')
    return
  }

  loading.value = true
  try {
    const results = await RAGService.searchMedicalCases(queryForm.value)
    searchResults.value = results
    
    if (results.success) {
      ElMessage.success('分析完成')
    } else {
      ElMessage.error(results.error || '分析失败')
    }
  } catch (error) {
    ElMessage.error('搜索失败，请稍后重试')
    console.error('搜索错误:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  checkRAGStatus()
})
</script>

<style scoped>
.medical-consultation {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.consultation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.rag-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  border-radius: 16px;
  background: #f5f5f5;
  color: #666;
}

.rag-status.available {
  background: #e8f5e8;
  color: #52c41a;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ccc;
}

.rag-status.available .status-indicator {
  background: #52c41a;
}

.search-results {
  margin-top: 20px;
}

.summary-section,
.recommendations-section,
.similar-cases-section {
  margin-bottom: 20px;
  padding: 16px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
}

.case-item {
  margin-bottom: 12px;
  padding: 12px;
  background: #f9f9f9;
  border-radius: 6px;
}

.case-content {
  margin-bottom: 8px;
  line-height: 1.6;
}

.case-metadata {
  font-size: 12px;
  color: #666;
}
</style>
```

### 3. 数据库集成

#### 3.1 创建医疗知识表

在 `backend/app/models/medical_knowledge.py` 中:

```python
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class MedicalKnowledge(Base):
    """医疗知识库表"""
    __tablename__ = "medical_knowledge"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(100), unique=True, index=True)
    content = Column(Text, nullable=False)
    vector_id = Column(String(100), index=True)  # ChromaDB中的向量ID
    metadata = Column(JSON)
    source_type = Column(String(50))  # 数据来源类型
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

#### 3.2 创建数据库迁移

```bash
# 生成迁移文件
alembic revision --autogenerate -m "Add medical knowledge table"

# 执行迁移
alembic upgrade head
```

### 4. 配置管理

#### 4.1 环境配置

在 `backend/.env` 中添加:

```env
# RAG服务配置
RAG_ENABLED=true
RAG_VECTOR_DB_PATH=./ai_models/embedding_models/vector_database/chroma_db
RAG_EMBEDDING_MODEL=shibing624/text2vec-base-chinese
RAG_MAX_RESULTS=10
RAG_SIMILARITY_THRESHOLD=0.7
```

#### 4.2 配置类

在 `backend/app/core/config.py` 中添加:

```python
class Settings(BaseSettings):
    # ... 现有配置 ...
    
    # RAG配置
    rag_enabled: bool = True
    rag_vector_db_path: str = "./ai_models/embedding_models/vector_database/chroma_db"
    rag_embedding_model: str = "shibing624/text2vec-base-chinese"
    rag_max_results: int = 10
    rag_similarity_threshold: float = 0.7
```

## 🚀 部署指南

### 1. 数据准备

```bash
# 1. 运行数据预处理
cd codes/ai_models/embedding_models
python3 run_cross_platform.py --all

# 2. 验证向量数据库
python3 test_retrieval.py
```

### 2. 后端部署

```bash
# 1. 安装依赖
cd codes/backend
pip install -r requirements.txt

# 2. 运行数据库迁移
alembic upgrade head

# 3. 启动后端服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. 前端部署

```bash
# 1. 安装依赖
cd codes/frontend
npm install

# 2. 构建生产版本
npm run build

# 3. 启动前端服务
npm run preview
```

## 🧪 测试验证

### 1. API测试

```bash
# 测试RAG服务状态
curl -X GET "http://localhost:8000/api/medical/rag-status" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 测试医疗病例搜索
curl -X POST "http://localhost:8000/api/medical/search-cases" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "symptoms": "胸痛发热",
    "context": "持续3天",
    "k": 5
  }'
```

### 2. 前端测试

1. 访问医疗咨询页面
2. 输入症状描述
3. 查看智能分析结果
4. 验证相似病例检索

## 📊 监控和维护

### 1. 性能监控

```python
# 在RAG服务中添加性能监控
import time
from functools import wraps

def monitor_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        logger.info(f"{func.__name__} 执行时间: {end_time - start_time:.3f}秒")
        return result
    return wrapper
```

### 2. 数据更新

```bash
# 定期更新向量数据库
# 可以设置定时任务
0 2 * * * cd /path/to/embedding_models && python3 run_cross_platform.py --build-vector-db
```

## 🔧 故障排除

### 1. 常见问题

**问题**: RAG服务初始化失败
**解决**: 检查向量数据库路径和模型文件是否存在

**问题**: 搜索结果为空
**解决**: 检查查询文本质量和相似度阈值设置

**问题**: 内存不足
**解决**: 减少批处理大小或使用更小的模型

### 2. 日志配置

```python
# 在RAG服务中添加详细日志
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 📈 优化建议

1. **缓存机制**: 对频繁查询的结果进行缓存
2. **异步处理**: 使用异步IO提高并发性能
3. **模型优化**: 使用量化模型减少内存占用
4. **索引优化**: 使用FAISS等高效向量索引
5. **负载均衡**: 支持多实例部署

通过以上集成步骤，词向量模型将完全集成到智诊通系统中，为用户提供智能的医疗咨询和病例检索服务。

## 🎯 集成目标

将词向量模型集成到智诊通系统中，实现基于医疗知识库的智能检索和问答功能。

## 📋 集成步骤

### 1. 后端集成

#### 1.1 创建RAG服务模块

在智诊通后端创建 `backend/app/services/rag_service.py`:

```python
import os
import logging
from typing import List, Dict, Any
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document

logger = logging.getLogger(__name__)

class MedicalRAGService:
    """医疗知识检索增强生成服务"""
    
    def __init__(self):
        self.embeddings = None
        self.vector_db = None
        self._initialize_rag()
    
    def _initialize_rag(self):
        """初始化RAG服务"""
        try:
            # 向量数据库路径
            db_path = os.path.join(
                os.path.dirname(__file__), 
                "../../ai_models/embedding_models/vector_database/chroma_db"
            )
            
            if not os.path.exists(db_path):
                logger.warning(f"向量数据库不存在: {db_path}")
                return
            
            # 初始化嵌入模型
            self.embeddings = HuggingFaceEmbeddings(
                model_name="shibing624/text2vec-base-chinese",
                model_kwargs={"device": "cpu"}
            )
            
            # 加载向量数据库
            self.vector_db = Chroma(
                persist_directory=db_path,
                embedding_function=self.embeddings
            )
            
            logger.info("RAG服务初始化成功")
            
        except Exception as e:
            logger.error(f"RAG服务初始化失败: {e}")
            self.embeddings = None
            self.vector_db = None
    
    def is_available(self) -> bool:
        """检查RAG服务是否可用"""
        return self.vector_db is not None
    
    def search_medical_cases(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """搜索相似医疗病例"""
        if not self.is_available():
            return []
        
        try:
            results = self.vector_db.similarity_search(query, k=k)
            
            return [
                {
                    "content": result.page_content,
                    "metadata": result.metadata,
                    "relevance_score": self._calculate_relevance_score(query, result.page_content)
                }
                for result in results
            ]
        except Exception as e:
            logger.error(f"搜索医疗病例失败: {e}")
            return []
    
    def search_with_score(self, query: str, k: int = 5, score_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """带相似度分数的搜索"""
        if not self.is_available():
            return []
        
        try:
            results = self.vector_db.similarity_search_with_score(query, k=k)
            
            filtered_results = []
            for doc, score in results:
                if score >= score_threshold:  # ChromaDB返回的是距离，越小越相似
                    filtered_results.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "similarity_score": 1 - score,  # 转换为相似度分数
                        "distance": score
                    })
            
            return filtered_results
        except Exception as e:
            logger.error(f"带分数搜索失败: {e}")
            return []
    
    def _calculate_relevance_score(self, query: str, content: str) -> float:
        """计算相关性分数（简单实现）"""
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        
        if not query_words:
            return 0.0
        
        intersection = query_words.intersection(content_words)
        return len(intersection) / len(query_words)
    
    def get_medical_advice(self, symptoms: str, context: str = "") -> Dict[str, Any]:
        """获取医疗建议"""
        if not self.is_available():
            return {"error": "RAG服务不可用"}
        
        # 构建查询
        query = f"{symptoms} {context}".strip()
        
        # 搜索相关病例
        similar_cases = self.search_medical_cases(query, k=3)
        
        if not similar_cases:
            return {"error": "未找到相关医疗信息"}
        
        # 提取关键信息
        advice = {
            "query": query,
            "similar_cases": similar_cases,
            "summary": self._generate_summary(similar_cases),
            "recommendations": self._extract_recommendations(similar_cases)
        }
        
        return advice
    
    def _generate_summary(self, cases: List[Dict[str, Any]]) -> str:
        """生成病例摘要"""
        if not cases:
            return "无相关病例信息"
        
        # 简单的摘要生成逻辑
        contents = [case["content"][:200] for case in cases[:2]]
        return "基于相似病例分析：" + "；".join(contents)
    
    def _extract_recommendations(self, cases: List[Dict[str, Any]]) -> List[str]:
        """提取治疗建议"""
        recommendations = []
        
        for case in cases:
            content = case["content"]
            # 简单的关键词提取
            if "建议" in content:
                recommendations.append("请参考相似病例的治疗建议")
            if "检查" in content:
                recommendations.append("建议进行相关检查")
            if "治疗" in content:
                recommendations.append("建议咨询专业医生制定治疗方案")
        
        return list(set(recommendations))  # 去重

# 全局RAG服务实例
rag_service = MedicalRAGService()
```

#### 1.2 创建API接口

在 `backend/app/api/medical.py` 中添加RAG相关接口:

```python
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.services.rag_service import rag_service
from app.core.auth import get_current_user

router = APIRouter()

class MedicalQueryRequest(BaseModel):
    symptoms: str
    context: Optional[str] = ""
    k: Optional[int] = 5

class MedicalQueryResponse(BaseModel):
    query: str
    similar_cases: List[Dict[str, Any]]
    summary: str
    recommendations: List[str]
    success: bool
    error: Optional[str] = None

@router.post("/search-cases", response_model=MedicalQueryResponse)
async def search_medical_cases(
    request: MedicalQueryRequest,
    current_user: dict = Depends(get_current_user)
):
    """搜索相似医疗病例"""
    try:
        if not rag_service.is_available():
            raise HTTPException(
                status_code=503, 
                detail="医疗知识库服务不可用"
            )
        
        # 搜索相似病例
        similar_cases = rag_service.search_medical_cases(
            request.symptoms, 
            k=request.k
        )
        
        # 生成建议
        advice = rag_service.get_medical_advice(
            request.symptoms, 
            request.context
        )
        
        return MedicalQueryResponse(
            query=request.symptoms,
            similar_cases=similar_cases,
            summary=advice.get("summary", ""),
            recommendations=advice.get("recommendations", []),
            success=True
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"搜索失败: {str(e)}"
        )

@router.get("/rag-status")
async def get_rag_status(current_user: dict = Depends(get_current_user)):
    """获取RAG服务状态"""
    return {
        "available": rag_service.is_available(),
        "status": "ready" if rag_service.is_available() else "not_ready"
    }
```

#### 1.3 更新依赖

在 `backend/requirements.txt` 中添加:

```txt
langchain==0.1.0
langchain-community==0.0.10
chromadb==0.4.18
sentence-transformers==2.2.2
```

### 2. 前端集成

#### 2.1 创建RAG服务API

在 `frontend/src/services/ragService.ts` 中:

```typescript
import { apiClient } from './apiClient'

export interface MedicalCase {
  content: string
  metadata: any
  relevance_score: number
}

export interface MedicalQueryRequest {
  symptoms: string
  context?: string
  k?: number
}

export interface MedicalQueryResponse {
  query: string
  similar_cases: MedicalCase[]
  summary: string
  recommendations: string[]
  success: boolean
  error?: string
}

export class RAGService {
  /**
   * 搜索相似医疗病例
   */
  static async searchMedicalCases(
    request: MedicalQueryRequest
  ): Promise<MedicalQueryResponse> {
    try {
      const response = await apiClient.post('/medical/search-cases', request)
      return response.data
    } catch (error) {
      console.error('搜索医疗病例失败:', error)
      throw error
    }
  }

  /**
   * 获取RAG服务状态
   */
  static async getRAGStatus(): Promise<{ available: boolean; status: string }> {
    try {
      const response = await apiClient.get('/medical/rag-status')
      return response.data
    } catch (error) {
      console.error('获取RAG状态失败:', error)
      return { available: false, status: 'error' }
    }
  }
}
```

#### 2.2 创建医疗咨询组件

在 `frontend/src/components/MedicalConsultation.vue` 中:

```vue
<template>
  <div class="medical-consultation">
    <div class="consultation-header">
      <h3>智能医疗咨询</h3>
      <div class="rag-status" :class="{ 'available': ragStatus.available }">
        <span class="status-indicator"></span>
        {{ ragStatus.available ? '知识库已就绪' : '知识库未就绪' }}
      </div>
    </div>

    <div class="consultation-form">
      <el-form :model="queryForm" @submit.prevent="handleSearch">
        <el-form-item label="症状描述">
          <el-input
            v-model="queryForm.symptoms"
            type="textarea"
            :rows="3"
            placeholder="请描述您的症状，如：胸痛、发热、咳嗽等"
            :disabled="!ragStatus.available"
          />
        </el-form-item>
        
        <el-form-item label="补充信息">
          <el-input
            v-model="queryForm.context"
            type="textarea"
            :rows="2"
            placeholder="其他相关信息（可选）"
            :disabled="!ragStatus.available"
          />
        </el-form-item>

        <el-form-item>
          <el-button 
            type="primary" 
            @click="handleSearch"
            :loading="loading"
            :disabled="!ragStatus.available"
          >
            智能分析
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <div v-if="searchResults" class="search-results">
      <div class="summary-section">
        <h4>分析摘要</h4>
        <p>{{ searchResults.summary }}</p>
      </div>

      <div class="recommendations-section">
        <h4>建议</h4>
        <ul>
          <li v-for="rec in searchResults.recommendations" :key="rec">
            {{ rec }}
          </li>
        </ul>
      </div>

      <div class="similar-cases-section">
        <h4>相似病例参考</h4>
        <div 
          v-for="(case_, index) in searchResults.similar_cases" 
          :key="index"
          class="case-item"
        >
          <div class="case-content">
            {{ case_.content.substring(0, 200) }}...
          </div>
          <div class="case-metadata">
            相关性: {{ (case_.relevance_score * 100).toFixed(1) }}%
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { RAGService, type MedicalQueryRequest, type MedicalQueryResponse } from '@/services/ragService'

const ragStatus = ref({ available: false, status: 'checking' })
const loading = ref(false)
const queryForm = ref<MedicalQueryRequest>({
  symptoms: '',
  context: '',
  k: 5
})
const searchResults = ref<MedicalQueryResponse | null>(null)

// 检查RAG服务状态
const checkRAGStatus = async () => {
  try {
    const status = await RAGService.getRAGStatus()
    ragStatus.value = status
  } catch (error) {
    ragStatus.value = { available: false, status: 'error' }
  }
}

// 搜索医疗病例
const handleSearch = async () => {
  if (!queryForm.value.symptoms.trim()) {
    ElMessage.warning('请输入症状描述')
    return
  }

  loading.value = true
  try {
    const results = await RAGService.searchMedicalCases(queryForm.value)
    searchResults.value = results
    
    if (results.success) {
      ElMessage.success('分析完成')
    } else {
      ElMessage.error(results.error || '分析失败')
    }
  } catch (error) {
    ElMessage.error('搜索失败，请稍后重试')
    console.error('搜索错误:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  checkRAGStatus()
})
</script>

<style scoped>
.medical-consultation {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.consultation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.rag-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  border-radius: 16px;
  background: #f5f5f5;
  color: #666;
}

.rag-status.available {
  background: #e8f5e8;
  color: #52c41a;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ccc;
}

.rag-status.available .status-indicator {
  background: #52c41a;
}

.search-results {
  margin-top: 20px;
}

.summary-section,
.recommendations-section,
.similar-cases-section {
  margin-bottom: 20px;
  padding: 16px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
}

.case-item {
  margin-bottom: 12px;
  padding: 12px;
  background: #f9f9f9;
  border-radius: 6px;
}

.case-content {
  margin-bottom: 8px;
  line-height: 1.6;
}

.case-metadata {
  font-size: 12px;
  color: #666;
}
</style>
```

### 3. 数据库集成

#### 3.1 创建医疗知识表

在 `backend/app/models/medical_knowledge.py` 中:

```python
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class MedicalKnowledge(Base):
    """医疗知识库表"""
    __tablename__ = "medical_knowledge"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(100), unique=True, index=True)
    content = Column(Text, nullable=False)
    vector_id = Column(String(100), index=True)  # ChromaDB中的向量ID
    metadata = Column(JSON)
    source_type = Column(String(50))  # 数据来源类型
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

#### 3.2 创建数据库迁移

```bash
# 生成迁移文件
alembic revision --autogenerate -m "Add medical knowledge table"

# 执行迁移
alembic upgrade head
```

### 4. 配置管理

#### 4.1 环境配置

在 `backend/.env` 中添加:

```env
# RAG服务配置
RAG_ENABLED=true
RAG_VECTOR_DB_PATH=./ai_models/embedding_models/vector_database/chroma_db
RAG_EMBEDDING_MODEL=shibing624/text2vec-base-chinese
RAG_MAX_RESULTS=10
RAG_SIMILARITY_THRESHOLD=0.7
```

#### 4.2 配置类

在 `backend/app/core/config.py` 中添加:

```python
class Settings(BaseSettings):
    # ... 现有配置 ...
    
    # RAG配置
    rag_enabled: bool = True
    rag_vector_db_path: str = "./ai_models/embedding_models/vector_database/chroma_db"
    rag_embedding_model: str = "shibing624/text2vec-base-chinese"
    rag_max_results: int = 10
    rag_similarity_threshold: float = 0.7
```

## 🚀 部署指南

### 1. 数据准备

```bash
# 1. 运行数据预处理
cd codes/ai_models/embedding_models
python3 run_cross_platform.py --all

# 2. 验证向量数据库
python3 test_retrieval.py
```

### 2. 后端部署

```bash
# 1. 安装依赖
cd codes/backend
pip install -r requirements.txt

# 2. 运行数据库迁移
alembic upgrade head

# 3. 启动后端服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. 前端部署

```bash
# 1. 安装依赖
cd codes/frontend
npm install

# 2. 构建生产版本
npm run build

# 3. 启动前端服务
npm run preview
```

## 🧪 测试验证

### 1. API测试

```bash
# 测试RAG服务状态
curl -X GET "http://localhost:8000/api/medical/rag-status" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 测试医疗病例搜索
curl -X POST "http://localhost:8000/api/medical/search-cases" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "symptoms": "胸痛发热",
    "context": "持续3天",
    "k": 5
  }'
```

### 2. 前端测试

1. 访问医疗咨询页面
2. 输入症状描述
3. 查看智能分析结果
4. 验证相似病例检索

## 📊 监控和维护

### 1. 性能监控

```python
# 在RAG服务中添加性能监控
import time
from functools import wraps

def monitor_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        logger.info(f"{func.__name__} 执行时间: {end_time - start_time:.3f}秒")
        return result
    return wrapper
```

### 2. 数据更新

```bash
# 定期更新向量数据库
# 可以设置定时任务
0 2 * * * cd /path/to/embedding_models && python3 run_cross_platform.py --build-vector-db
```

## 🔧 故障排除

### 1. 常见问题

**问题**: RAG服务初始化失败
**解决**: 检查向量数据库路径和模型文件是否存在

**问题**: 搜索结果为空
**解决**: 检查查询文本质量和相似度阈值设置

**问题**: 内存不足
**解决**: 减少批处理大小或使用更小的模型

### 2. 日志配置

```python
# 在RAG服务中添加详细日志
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 📈 优化建议

1. **缓存机制**: 对频繁查询的结果进行缓存
2. **异步处理**: 使用异步IO提高并发性能
3. **模型优化**: 使用量化模型减少内存占用
4. **索引优化**: 使用FAISS等高效向量索引
5. **负载均衡**: 支持多实例部署

通过以上集成步骤，词向量模型将完全集成到智诊通系统中，为用户提供智能的医疗咨询和病例检索服务。




