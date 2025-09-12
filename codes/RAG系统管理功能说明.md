# RAG系统管理功能说明

## 概述

本文档说明了智诊通系统中RAG（检索增强生成）服务的管理功能，包括启动、停止和状态检查。

## 新增功能

### 1. 启动脚本 (start-all.sh)

#### 新增的RAG服务启动功能：
- **自动检测RAG服务依赖**：检查`requirements.txt`文件是否存在
- **虚拟环境管理**：自动创建和管理RAG服务的Python虚拟环境
- **依赖安装**：自动安装RAG服务所需的Python包
- **后台启动**：在端口8001上启动RAG服务
- **健康检查**：验证RAG服务是否成功启动
- **日志记录**：将RAG服务日志保存到`backend/logs/rag.log`

#### 启动流程：
1. 检查RAG服务目录和依赖文件
2. 创建或使用现有的虚拟环境
3. 安装Python依赖包
4. 在后台启动RAG服务（端口8001）
5. 等待服务启动并验证健康状态
6. 保存进程ID到`.rag.pid`文件

### 2. 停止脚本 (stop-all.sh)

#### 新增的RAG服务停止功能：
- **进程ID管理**：通过`.rag.pid`文件优雅停止RAG服务
- **端口释放**：检查并释放8001端口
- **强制停止**：如果优雅停止失败，使用强制停止
- **进程清理**：清理所有相关的RAG服务进程

#### 停止流程：
1. 读取RAG进程ID并尝试优雅停止
2. 如果进程仍在运行，使用强制停止
3. 检查并释放8001端口
4. 清理所有相关的Python进程
5. 更新状态检查结果

### 3. 状态检查脚本 (status.sh)

#### 新增的RAG服务状态检查功能：
- **服务健康检查**：检查RAG服务是否响应健康检查请求
- **端口占用检查**：显示8001端口的占用情况
- **日志文件检查**：显示RAG日志文件的大小和状态
- **健康评分**：将RAG服务纳入整体系统健康评分

#### 状态检查项目：
1. RAG服务健康状态（端口8001）
2. 端口占用情况（8001端口）
3. RAG日志文件状态
4. 系统整体健康评分（7项检查中的1项）

## 服务端口分配

| 服务 | 端口 | 说明 |
|------|------|------|
| 后端API | 8000 | 主要的后端服务 |
| RAG服务 | 8001 | 检索增强生成服务 |
| 前端界面 | 8080 | Vue.js前端应用 |

## 日志文件

| 服务 | 日志文件 | 位置 |
|------|----------|------|
| 后端 | backend.log | backend/logs/ |
| 前端 | frontend.log | backend/logs/ |
| RAG | rag.log | backend/logs/ |

## 常用命令

### 启动命令
```bash
# 一键启动所有服务（包括RAG）
./start-all.sh

# 单独启动RAG服务
cd services/knowledge_retrieval_service && python3 start_rag_service.py
```

### 停止命令
```bash
# 停止所有服务（包括RAG）
./stop-all.sh
```

### 状态检查
```bash
# 查看系统状态（包括RAG）
./status.sh

# 检查RAG服务健康状态
curl http://localhost:8001/health
```

### 日志查看
```bash
# 查看RAG服务日志
tail -f backend/logs/rag.log

# 查看所有服务日志
tail -f backend/logs/*.log
```

## 健康检查端点

- **RAG服务健康检查**：`http://localhost:8001/health`
- **RAG API文档**：`http://localhost:8001/docs`
- **后端服务健康检查**：`http://localhost:8000/health`

## 故障排除

### RAG服务启动失败
1. 检查Python虚拟环境是否正确创建
2. 验证依赖包是否安装成功
3. 查看RAG日志：`tail -f backend/logs/rag.log`
4. 检查端口8001是否被占用：`lsof -i :8001`

### RAG服务无法访问
1. 检查服务是否正在运行：`ps aux | grep start_rag_service`
2. 验证健康检查端点：`curl http://localhost:8001/health`
3. 检查防火墙设置

### 依赖问题
1. 重新安装依赖：`cd services/knowledge_retrieval_service && pip install -r requirements.txt`
2. 检查Python版本兼容性
3. 验证模型文件路径

## 配置说明

RAG服务的配置通过以下文件管理：
- **主配置**：`services/knowledge_retrieval_service/api/config/rag_config.json`
- **启动脚本**：`services/knowledge_retrieval_service/start_rag_service.py`
- **依赖管理**：`services/knowledge_retrieval_service/requirements.txt`

## 注意事项

1. **端口冲突**：确保8001端口未被其他服务占用
2. **资源需求**：RAG服务需要较多内存和CPU资源
3. **模型文件**：确保AI模型文件已正确下载和配置
4. **虚拟环境**：RAG服务使用独立的Python虚拟环境
5. **日志轮转**：定期清理日志文件以避免磁盘空间不足

## 更新历史

- **2024-09-10**：添加RAG系统管理功能到启动、停止和状态检查脚本
- **功能包括**：自动启动、优雅停止、健康检查、日志管理
- **端口分配**：RAG服务使用8001端口
- **集成度**：完全集成到现有的系统管理脚本中


