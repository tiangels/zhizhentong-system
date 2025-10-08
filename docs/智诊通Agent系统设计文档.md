# 智诊通 Agent 系统设计文档

## 📋 目录

1. [项目概述](#1-项目概述)
2. [现有系统分析](#2-现有系统分析)
3. [Agent 系统架构设计](#3-agent系统架构设计)
4. [核心 Agent 模块设计](#4-核心agent模块设计)
5. [技术实现方案](#5-技术实现方案)
6. [部署与集成方案](#6-部署与集成方案)
7. [实施计划](#7-实施计划)

---

## 1. 项目概述

### 1.1 项目背景

智诊通系统是一个基于多模态 AI 技术的智能医生问诊系统，目前已经实现了基础的 RAG（检索增强生成）功能。为了进一步提升系统的智能化程度，我们需要将现有的"被动响应工具"升级为"主动服务实体"，即构建多模态医疗智能体系统。

### 1.2 Agent 升级目标

**核心目标**：从被动问答升级为主动诊断辅助

- **智能化程度**：从被动响应升级为主动诊断辅助
- **准确性提升**：通过多工具协作和结果验证提高回答质量
- **用户体验**：支持多轮对话和智能追问，交互更自然
- **医疗专业性**：基于医疗诊断流程的智能任务规划

### 1.3 设计理念

- **任务导向**：将复杂医疗问题拆解为可执行的子任务
- **工具集成**：将现有模块封装为智能体可调用的工具
- **记忆管理**：结合长期记忆（知识库）和短期记忆（对话上下文）
- **自我修正**：通过结果评估实现智能体自我优化

---

## 2. 现有系统分析

### 2.1 现有架构概览

基于系统文件说明文档，现有智诊通系统包含以下核心组件：

```
智诊通系统架构：
├── 前端服务 (Vue 3 + TypeScript) - 端口 8080
├── 后端服务 (FastAPI + Python) - 端口 8000
├── 向量化服务 (Embedding Service) - 端口 8001
├── 知识检索服务 (Knowledge Retrieval) - 端口 8002
├── 智能诊断服务 (Intelligent Diagnosis) - 端口 8003
└── 基础设施服务 (Elasticsearch, Kibana, ChromaDB)
```

### 2.2 现有功能模块

#### 2.2.1 后端核心模块

- **认证与授权模块**：用户管理、JWT 认证、权限控制
- **对话管理模块**：会话管理、消息处理、上下文管理
- **RAG 服务编排模块**：服务调用、结果处理、错误处理
- **系统管理模块**：健康检查、日志管理、配置管理

#### 2.2.2 微服务模块

- **向量化服务**：文本、图像、语音的向量化处理
- **知识检索服务**：RAG 检索增强生成，知识库查询
- **智能诊断服务**：AI 驱动的医疗诊断分析

#### 2.2.3 AI 模型资源

- **文本模型**：Apollo-0.5B、distilbert-base-multilingual-cased
- **多模态模型**：BiomedCLIP-PubMedBERT
- **语音模型**：whisper-tiny
- **摘要模型**：Falconsai_text_summarization
- **嵌入模型**：paraphrase-multilingual-MiniLM-L12-v2

### 2.3 现有数据资源

#### 2.3.1 医疗知识库

- **文本数据**：医疗文档、医学论文、疾病知识
- **图像数据**：胸部 X 光片、医学图像报告
- **语音数据**：医疗语音转录数据
- **对话数据**：医疗对话训练数据

#### 2.3.2 向量数据库

- **ChromaDB**：存储文档向量，支持语义检索
- **多模态向量**：图像-文本联合向量表示

---

## 3. Agent 系统架构设计

### 3.1 Agent 系统整体架构

```mermaid
graph TB
    subgraph "用户交互层"
        A1[Web前端界面]
        A2[移动端APP]
        A3[语音助手]
    end

    subgraph "Agent协调层"
        B1[主Agent协调器]
        B2[任务规划器]
        B3[工具调用管理器]
        B4[结果评估器]
    end

    subgraph "专业Agent层"
        C1[诊断Agent]
        C2[用药Agent]
        C3[护理Agent]
        C4[知识Agent]
    end

    subgraph "工具服务层"
        D1[RAG检索工具]
        D2[向量化工具]
        D3[诊断工具]
        D4[追问工具]
        D5[预约工具]
    end

    subgraph "数据存储层"
        E1[医疗知识库]
        E2[向量数据库]
        E3[对话历史库]
        E4[用户档案库]
    end

    A1 --> B1
    A2 --> B1
    A3 --> B1

    B1 --> B2
    B2 --> B3
    B3 --> B4

    B3 --> C1
    B3 --> C2
    B3 --> C3
    B3 --> C4

    C1 --> D1
    C1 --> D3
    C2 --> D4
    C3 --> D5
    C4 --> D2

    D1 --> E1
    D2 --> E2
    D3 --> E3
    D4 --> E4
```

### 3.2 Agent 工作流程

```mermaid
flowchart TD
    A[用户输入] --> B[任务理解与拆分]
    B --> C[任务规划与调度]
    C --> D[工具调用与执行]
    D --> E[结果评估与验证]
    E --> F{是否满足要求}
    F -->|是| G[生成最终回复]
    F -->|否| H[调整策略重新执行]
    H --> D
    G --> I[用户反馈收集]
    I --> J[Agent学习优化]
```

### 3.3 Agent 核心能力

#### 3.3.1 感知能力

- **多模态输入理解**：文本、语音、图像的统一理解
- **用户意图识别**：准确理解用户的医疗需求
- **上下文感知**：维护对话历史和用户状态

#### 3.3.2 决策能力

- **任务规划**：将复杂医疗问题拆解为可执行任务
- **优先级排序**：基于医疗紧急程度的任务优先级
- **策略选择**：选择最适合的医疗诊断策略

#### 3.3.3 执行能力

- **工具调用**：调用各种医疗专业工具
- **并行处理**：同时执行多个相关任务
- **结果整合**：将多个工具结果整合为统一回复

#### 3.3.4 学习能力

- **结果评估**：评估工具调用结果的质量
- **策略优化**：基于反馈优化执行策略
- **知识更新**：持续学习和知识更新

---

## 4. 核心 Agent 模块设计

### 4.1 主 Agent 协调器

#### 4.1.1 功能描述

主 Agent 协调器是整个 Agent 系统的核心，负责协调各个专业 Agent 的工作，管理任务流程，确保系统的高效运行。

#### 4.1.2 核心组件

- **任务理解器**：理解用户输入的医疗问题
- **任务拆分器**：将复杂问题拆解为子任务
- **调度器**：负责任务的分配和调度
- **协调器**：协调多个 Agent 的协作
- **结果整合器**：整合多个 Agent 的输出结果

#### 4.1.3 技术实现

```python
class MainAgentCoordinator:
    def __init__(self):
        self.task_understander = TaskUnderstander()
        self.task_splitter = TaskSplitter()
        self.scheduler = TaskScheduler()
        self.coordinator = AgentCoordinator()
        self.result_integrator = ResultIntegrator()

    def process_user_input(self, user_input, context):
        # 任务理解
        understood_task = self.task_understander.understand(user_input, context)
        # 任务拆分
        subtasks = self.task_splitter.split(understood_task)
        # 任务调度
        execution_plan = self.scheduler.schedule(subtasks)
        # 协调执行
        results = self.coordinator.execute(execution_plan)
        # 结果整合
        final_result = self.result_integrator.integrate(results)
        return final_result
```

### 4.2 专业 Agent 设计

#### 4.2.1 诊断 Agent

**功能**：负责症状分析和初步诊断
**核心能力**：

- 症状描述解析和标准化
- 症状严重程度评估
- 疾病可能性分析
- 诊断置信度评估

#### 4.2.2 用药 Agent

**功能**：负责药物推荐和用药指导
**核心能力**：

- 药物信息查询
- 药物相互作用检查
- 用法用量建议
- 副作用预警

#### 4.2.3 护理 Agent

**功能**：负责护理建议和康复指导
**核心能力**：

- 护理方案制定
- 康复指导
- 生活建议
- 预防措施

#### 4.2.4 知识 Agent

**功能**：负责医疗知识检索和问答
**核心能力**：

- 医疗知识检索
- 疾病信息查询
- 健康知识问答
- 医学概念解释

---

## 5. 技术实现方案

### 5.1 Agent 框架选择

#### 5.1.1 LangGraph 框架

**优势**：

- 支持复杂的 Agent 工作流
- 内置状态管理
- 支持条件分支和循环
- 与 LangChain 生态集成良好

**适用场景**：复杂的医疗诊断流程

#### 5.1.2 ReAct 智能体模式

**特点**：推理（Reasoning）+ 行动（Acting）循环
**适用场景**：需要多步推理的复杂医疗诊断

#### 5.1.3 Plan-and-Execute 智能体

**特点**：先制定详细计划，再执行具体任务
**适用场景**：需要系统性分析的医疗咨询

### 5.2 工具集成方案

#### 5.2.1 现有工具封装

将现有系统模块封装为 Agent 可调用的工具：

```python
# RAG检索工具
class RAGRetrievalTool:
    def __init__(self):
        self.retrieval_service = RetrievalService()

    def retrieve_knowledge(self, query, top_k=5):
        return self.retrieval_service.retrieve(query, top_k)

# 向量化工具
class VectorizationTool:
    def __init__(self):
        self.embedding_service = EmbeddingService()

    def vectorize_text(self, text):
        return self.embedding_service.embed_text(text)

# 诊断工具
class DiagnosisTool:
    def __init__(self):
        self.diagnosis_service = DiagnosisService()

    def analyze_symptoms(self, symptoms):
        return self.diagnosis_service.analyze(symptoms)
```

#### 5.2.2 新增工具开发

开发医疗场景专用的新工具：

```python
# 追问系统工具
class QuestioningTool:
    def __init__(self):
        self.question_generator = QuestionGenerator()

    def generate_follow_up_questions(self, context):
        return self.question_generator.generate(context)

# 预约挂号工具
class AppointmentTool:
    def __init__(self):
        self.appointment_service = AppointmentService()

    def recommend_department(self, symptoms):
        return self.appointment_service.recommend(symptoms)

# 检查建议工具
class ExaminationTool:
    def __init__(self):
        self.examination_service = ExaminationService()

    def recommend_examinations(self, diagnosis):
        return self.examination_service.recommend(diagnosis)
```

### 5.3 记忆管理系统

#### 5.3.1 长期记忆（知识存储）

- **医疗知识库**：通过 RAG 系统存储的医疗专业知识
- **结构化病历**：通过 ES 存储的患者历史医疗记录
- **知识图谱**：通过 Neo4j 存储的疾病关联和家族史信息

#### 5.3.2 短期记忆（对话管理）

- **对话历史**：用户输入、智能追问、中间结论
- **任务状态**：当前执行的任务、已完成的任务、待执行的任务
- **上下文信息**：本轮对话的关键信息、用户意图变化

---

## 6. 部署与集成方案

### 6.1 Agent 服务部署

#### 6.1.1 服务架构

```yaml
# docker-compose.agent.yml
version: "3.8"
services:
  agent-coordinator:
    build: ./services/agent_coordinator
    ports:
      - "8005:8005"
    environment:
      - RAG_SERVICE_URL=http://knowledge_retrieval_service:8002
      - DIAGNOSIS_SERVICE_URL=http://intelligent_diagnosis_service:8003
      - EMBEDDING_SERVICE_URL=http://embedding_service:8001
    depends_on:
      - knowledge_retrieval_service
      - intelligent_diagnosis_service
      - embedding_service

  diagnosis-agent:
    build: ./services/diagnosis_agent
    ports:
      - "8006:8006"
    environment:
      - LLM_MODEL_PATH=/app/models/medical_qwen
      - KNOWLEDGE_BASE_PATH=/app/data/medical_knowledge

  medication-agent:
    build: ./services/medication_agent
    ports:
      - "8007:8007"
    environment:
      - DRUG_DATABASE_URL=postgresql://user:pass@postgres:5432/drugs

  nursing-agent:
    build: ./services/nursing_agent
    ports:
      - "8008:8008"
    environment:
      - CARE_PLAN_DATABASE_URL=postgresql://user:pass@postgres:5432/care_plans
```

#### 6.1.2 服务集成

```python
# 后端服务集成Agent
class AgentIntegrationService:
    def __init__(self):
        self.agent_client = AgentClient("http://agent-coordinator:8005")

    async def process_with_agent(self, user_input, conversation_id):
        response = await self.agent_client.process(
            input_text=user_input,
            conversation_id=conversation_id,
            context=self.get_conversation_context(conversation_id)
        )
        return response
```

### 6.2 现有系统集成

#### 6.2.1 API 接口扩展

在现有后端服务中添加 Agent 相关接口：

```python
# backend/app/api/agent.py
from fastapi import APIRouter, Depends
from app.modules.agent.agent_service import AgentService

router = APIRouter(prefix="/agent", tags=["agent"])

@router.post("/process")
async def process_with_agent(
    request: AgentProcessRequest,
    current_user: User = Depends(get_current_user)
):
    agent_service = AgentService()
    result = await agent_service.process_user_input(
        user_input=request.input_text,
        user_id=current_user.id,
        conversation_id=request.conversation_id
    )
    return result
```

#### 6.2.2 前端界面集成

在前端添加 Agent 交互界面：

```vue
<!-- frontend/src/components/agent/AgentChat.vue -->
<template>
  <div class="agent-chat">
    <div class="chat-header">
      <h3>智能医疗助手</h3>
      <div class="agent-status">
        <span :class="agentStatusClass">{{ agentStatus }}</span>
      </div>
    </div>

    <div class="chat-messages">
      <div
        v-for="message in messages"
        :key="message.id"
        :class="['message', message.type]"
      >
        <div class="message-content">
          {{ message.content }}
        </div>
        <div v-if="message.evidence" class="message-evidence">
          <h4>参考依据：</h4>
          <ul>
            <li v-for="item in message.evidence" :key="item.id">
              {{ item.title }}
            </li>
          </ul>
        </div>
      </div>
    </div>

    <div class="chat-input">
      <MultimodalInput @send="handleSend" />
    </div>
  </div>
</template>
```

---

## 7. 实施计划

### 7.1 开发阶段规划

#### 第一阶段：Agent 基础框架搭建（2 周）

- Agent 协调器基础架构
- 基础工具封装
- 简单的任务拆分和调度
- 与现有系统的初步集成

#### 第二阶段：专业 Agent 开发（3 周）

- 诊断 Agent 开发
- 用药 Agent 开发
- 护理 Agent 开发
- 知识 Agent 开发

#### 第三阶段：高级功能实现（2 周）

- 多 Agent 协作机制
- 结果评估和优化
- 用户反馈学习
- 性能优化

#### 第四阶段：系统集成测试（1 周）

- 端到端测试
- 性能测试
- 用户体验测试
- 部署优化

### 7.2 技术风险评估

#### 7.2.1 主要风险

- **Agent 协调复杂性**：多 Agent 协作的复杂性可能导致系统不稳定
- **工具集成难度**：现有工具与 Agent 框架的集成可能存在兼容性问题
- **性能影响**：Agent 系统的额外开销可能影响系统响应速度

#### 7.2.2 应对措施

- **渐进式开发**：分阶段实现，逐步增加复杂度
- **充分测试**：每个阶段都进行充分的单元测试和集成测试
- **性能监控**：建立完善的性能监控体系
- **降级机制**：在 Agent 系统出现问题时能够降级到原有系统

### 7.3 预期效果

#### 7.3.1 功能提升

- **智能化程度**：从被动问答升级为主动诊断辅助
- **准确性提升**：通过多工具协作和结果验证提高回答质量
- **用户体验**：支持多轮对话和智能追问，交互更自然

#### 7.3.2 技术优势

- **模块化设计**：易于扩展和维护
- **工具复用**：现有系统模块得到充分利用
- **可扩展性**：支持新工具和新 Agent 模式的快速集成

#### 7.3.3 业务价值

- **诊断效率**：通过智能任务规划提高诊断辅助效率
- **医疗质量**：通过多维度评估确保医疗建议的准确性
- **用户满意度**：提供更智能、更个性化的医疗服务

---

## 8. 总结

智诊通 Agent 系统设计基于现有系统的坚实基础，通过引入智能体技术，将系统从"被动响应工具"升级为"主动服务实体"。该系统采用模块化设计，支持多 Agent 协作，具备完整的记忆管理和学习能力。

通过分阶段实施，可以逐步完善 Agent 功能，确保系统的高质量交付。Agent 系统的引入将显著提升智诊通系统的智能化程度，为用户提供更专业、更智能的医疗咨询服务。

**文档版本**: v1.0.0  
**创建时间**: 2025 年 1 月  
**维护团队**: 智诊通开发团队
