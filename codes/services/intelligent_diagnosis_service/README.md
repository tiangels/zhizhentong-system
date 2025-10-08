# 智诊通智能诊断服务

## 📋 服务概述

智诊通智能诊断服务是一个专门负责医疗智能诊断的微服务，基于大语言模型和文本摘要技术，为医疗领域提供智能诊断建议和流式响应服务。

### 🎯 核心功能

- **文本摘要处理**: 基于 T5 模型的医学文本摘要
- **智能诊断生成**: 基于大语言模型的医疗诊断建议
- **提示词构建**: 专业的医疗提示词引擎
- **流式响应**: 实时流式诊断结果输出
- **多模态支持**: 支持文本和图像诊断

### 🏗️ 服务架构

```
intelligent_diagnosis_service/
├── core/                    # 核心业务逻辑
│   ├── models/             # 数据模型
│   ├── services/           # 业务服务
│   └── prompt_engine.py   # 提示词引擎
├── api/                    # API 接口
│   ├── config/            # API 配置
│   └── diagnosis_api.py   # 诊断 API
├── config/                 # 服务配置
├── utils/                  # 工具函数
├── tests/                  # 测试文件
└── docs/                   # 文档
```

### 🔌 API 接口

- **POST /diagnosis/summarize** - 文本摘要处理
- **POST /diagnosis/generate** - 生成诊断建议
- **POST /diagnosis/stream** - 流式诊断响应
- **GET /diagnosis/health** - 健康检查

### 🚀 启动方式

```bash
cd codes/services/intelligent_diagnosis_service
python start_diagnosis_service.py --host 0.0.0.0 --port 8003
```

### 📊 服务端口

- **主服务端口**: 8003
- **健康检查**: http://localhost:8003/diagnosis/health

### 🔗 服务依赖

- **知识检索服务**: 8002 (提供检索结果)
- **向量化服务**: 8001 (文本向量化)

---

**服务版本**: v1.0.0  
**创建时间**: 2024 年 9 月 29 日  
**服务状态**: ✅ 运行中
