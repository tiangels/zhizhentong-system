# 🏥 智诊通系统 - 多模态智能医生问诊系统

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3.4+-brightgreen.svg)](https://vuejs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.3+-blue.svg)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> 基于人工智能的多模态智能医生问诊系统，支持文本、语音、图像等多种输入方式，为用户提供便捷、智能的医疗咨询服务。

## ✨ 主要特性

- 🧠 **智能问诊**: AI驱动的症状分析和医疗建议
- 🎯 **多模态输入**: 支持文本、语音、图像输入
- 💬 **实时对话**: WebSocket实现流畅的对话体验
- 🔐 **用户认证**: 完整的注册登录和权限管理
- 📱 **响应式设计**: 适配桌面端和移动端
- 🚀 **微服务架构**: 模块化设计，易于扩展
- 📊 **实时监控**: 系统状态和性能监控
- 🐳 **容器化部署**: Docker支持一键部署

## 🏗️ 技术架构

### 技术栈

**后端**:
- Python 3.8+ + FastAPI + SQLAlchemy
- SQLite/PostgreSQL + Redis + Milvus
- JWT认证 + Swagger文档

**前端**:
- Vue 3 + TypeScript + Vite
- Pinia + Vue Router + Ant Design Vue
- Axios + Less

**部署**:
- Docker + Docker Compose
- Nginx + SSL证书

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        用户层                                │
│  Web浏览器  │  移动端APP  │  微信小程序  │  桌面应用        │
└─────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────┐
│                      前端层 (Vue 3)                         │
│  页面组件  │  状态管理  │  路由管理  │  HTTP客户端         │
└─────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────┐
│                    API网关层 (FastAPI)                      │
│  认证授权  │  请求路由  │  参数验证  │  响应格式化         │
└─────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────┐
│                      业务逻辑层                              │
│ 用户管理 │ 对话管理 │ 诊断分析 │ 知识检索 │ 多模态处理    │
└─────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────┐
│                       AI服务层                               │
│  大语言模型  │  语音识别  │  图像识别  │  知识图谱        │
└─────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────┐
│                      数据存储层                              │
│   关系数据库   │   向量数据库   │   缓存数据库   │  文件存储  │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 环境要求

- **Python**: 3.8+
- **Node.js**: 18.0+
- **Docker**: 20.0+ (可选)
- **Redis**: 6.0+ (可选)
- **PostgreSQL**: 13.0+ (可选)

### 方式一：一键启动（推荐）

```bash
# 1. 克隆项目
git clone <repository-url>
cd zhi_zhen_tong_system

# 2. 一键启动所有服务
cd codes
chmod +x start-all.sh
./start-all.sh
```

### 方式二：分步启动

#### 启动后端服务
```bash
cd codes/backend
chmod +x start-dev.sh
./start-dev.sh
```

#### 启动前端服务
```bash
cd codes/frontend
chmod +x start-dev.sh
./start-dev.sh
```

#### 启动RAG检索服务
```bash
cd codes/services/knowledge_retrieval_service
chmod +x quick_start.sh
./quick_start.sh
```

### 方式三：Docker启动

```bash
# 启动基础服务
cd codes/backend
docker-compose up -d postgres redis

# 启动RAG服务
cd ../services/knowledge_retrieval_service
docker-compose up -d

# 查看服务状态
docker-compose ps
```

### 访问系统

- 🌐 **前端界面**: http://localhost:8080
- 🔧 **后端API**: http://localhost:8000
- 🤖 **RAG服务**: http://localhost:8000 (RAG服务)
- 📚 **API文档**: http://localhost:8000/docs
- ❤️ **健康检查**: http://localhost:8000/health
- 📊 **系统状态**: 运行 `./status.sh` 查看

## 📁 项目结构

```
zhi_zhen_tong_system/
├── codes/                        # 核心代码目录
│   ├── backend/                  # 后端服务 (FastAPI + PostgreSQL)
│   │   ├── app/                  # FastAPI应用
│   │   │   ├── api/              # API路由层
│   │   │   ├── models/           # 数据模型层
│   │   │   ├── modules/          # 业务逻辑层
│   │   │   └── main.py           # 应用入口
│   │   ├── logs/                 # 日志文件
│   │   ├── uploads/              # 上传文件
│   │   ├── docker-compose.yml    # Docker编排
│   │   ├── start-dev.sh          # 开发启动脚本
│   │   └── requirements.txt      # Python依赖
│   │
│   ├── frontend/                 # 前端服务 (Vue 3 + TypeScript)
│   │   ├── src/                  # 源代码
│   │   │   ├── components/       # Vue组件
│   │   │   ├── views/            # 页面组件
│   │   │   ├── stores/           # 状态管理 (Pinia)
│   │   │   ├── services/         # API服务
│   │   │   └── router/           # 路由配置
│   │   ├── package.json          # 前端依赖
│   │   ├── vite.config.ts        # Vite配置
│   │   └── start-dev.sh          # 开发启动脚本
│   │
│   ├── ai_models/                # AI模型目录
│   │   ├── embedding_models/     # 向量化模型模块 ⭐
│   │   │   ├── core/             # 核心功能
│   │   │   ├── processors/       # 数据处理器
│   │   │   ├── models/           # 模型相关
│   │   │   └── config/           # 配置文件
│   │   └── llm_models/           # 大语言模型 ⭐
│   │       ├── Medical_Qwen3_17B/ # 医疗大模型
│   │       └── text2vec-base-chinese/ # 文本向量化模型
│   │
│   ├── services/                 # 微服务模块
│   │   ├── knowledge_retrieval_service/ # RAG检索服务 ⭐
│   │   │   ├── core/             # 核心服务
│   │   │   ├── api/              # API接口
│   │   │   ├── start_rag_service.py # 启动脚本
│   │   │   ├── mock_rag_service.py # 模拟服务
│   │   │   └── docker-compose.yml # 容器编排
│   │   ├── intellect_diagnose_service/ # 智能诊断服务
│   │   ├── multi_model_processing_service/ # 多模态处理服务
│   │   └── session_management_service/ # 会话管理服务
│   │
│   ├── chroma_db/                # 向量数据库 ⭐
│   │   ├── chroma.sqlite3        # 数据库文件
│   │   └── [collection_id]/      # 集合数据
│   │
│   ├── start-all.sh              # 一键启动脚本
│   ├── status.sh                 # 状态检查脚本
│   └── stop-all.sh               # 停止服务脚本
│
├── datas/                        # 数据目录 ⭐
│   ├── medical_knowledge/        # 医疗知识库
│   │   ├── text_data/            # 文本数据
│   │   ├── image_text_data/      # 图像文本数据
│   │   ├── voice_data/           # 语音数据
│   │   ├── vector_databases/     # 向量数据库
│   │   ├── dialogue_data/        # 对话数据
│   │   └── training_data/        # 训练数据
│   ├── vector_databases/         # 向量数据库备份
│   └── test_data/                # 测试数据
│
├── docs/                         # 项目文档
│   ├── 智诊通系统架构设计.md       # 系统架构设计
│   ├── 智诊通模块设计.md           # 模块详细设计
│   └── 智诊通项目实施指南.md       # 项目实施指南
│
├── 项目启动指南.md                 # 项目启动说明
├── 系统架构与功能说明.md           # 系统架构文档
├── SYSTEM_STATUS.md              # 系统状态报告
└── README.md                     # 项目说明
```

## 📖 核心功能

### 1. 智能问诊系统
- **症状描述**: 用户可描述身体不适症状
- **智能分析**: 基于Medical_Qwen3_17B的AI分析
- **建议推荐**: 给出治疗建议和注意事项
- **紧急提醒**: 识别紧急情况并提醒就医

### 2. RAG检索增强系统 ⭐
- **知识检索**: 基于向量相似度的语义搜索
- **多模态支持**: 文本、图像、语音数据的统一处理
- **跨模态检索**: 图像查询返回相关文本，文本查询支持图像结果
- **智能生成**: 基于检索结果生成回答

### 3. 多模态输入处理
- **文本输入**: 支持中文症状描述
- **语音输入**: 语音转文字功能
- **图像输入**: 皮肤、伤口等图像识别
- **混合输入**: 多种输入方式组合使用

### 4. 向量化知识库 ⭐
- **文档处理**: 支持Word、PDF、TXT、Excel等格式
- **智能切分**: 医疗文档的结构化切分
- **向量化**: 基于text2vec-base-chinese的文本向量化
- **索引构建**: 高效的向量数据库索引

### 5. 用户管理系统
- **用户注册**: 支持邮箱和手机号注册
- **身份验证**: JWT token认证机制
- **会话管理**: 多设备登录支持
- **隐私保护**: 数据加密和访问控制

### 6. 对话管理系统
- **历史记录**: 保存所有问诊对话
- **上下文理解**: 连续对话的上下文保持
- **多轮对话**: 支持追问和澄清
- **导出功能**: 对话记录导出为文档

## 🔧 开发指南

### 环境配置

```bash
# 后端环境
cd codes/backend
# 使用conda nlp环境
source $(conda info --base)/etc/profile.d/conda.sh
conda activate nlp
pip install -r requirements.txt

# 前端环境
cd codes/frontend
npm install
```

### 开发命令

```bash
# 后端开发
cd codes/backend
python3 -m uvicorn app.main:app --reload

# 前端开发
cd codes/frontend
npm run dev

# 代码检查
npm run lint
npm run type-check

# 构建生产版本
npm run build
```

### 测试

```bash
# 后端测试
cd codes/backend
pytest

# 前端测试
cd codes/frontend
npm run test
```

## 📚 文档

- 📖 [项目启动指南](./项目启动指南.md) - 详细的启动流程说明
- 🏗️ [系统架构与功能说明](./系统架构与功能说明.md) - 完整的架构文档
- 🤖 [RAG检索增强系统完整说明文档](./codes/services/knowledge_retrieval_service/智诊通RAG检索增强系统完整说明文档.md) - RAG系统详细文档
- 🧠 [多模态向量化系统完整说明文档](./codes/ai_models/embedding_models/智诊通多模态向量化系统完整说明文档.md) - 向量化系统详细文档
- 📋 [API文档](http://localhost:8000/docs) - Swagger自动生成的API文档
- 🎯 [开发规范](./docs/) - 代码规范和开发指南
- 📊 [系统状态报告](./SYSTEM_STATUS.md) - 当前系统运行状态

## 🤝 贡献指南

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的修改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 👥 开发团队

- **项目负责人**: 智诊通开发团队
- **技术支持**: support@zhizhentong.com
- **项目地址**: https://github.com/your-org/zhi_zhen_tong_system

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者和用户！

---

**⭐ 如果这个项目对你有帮助，请给我们一个星标！**
