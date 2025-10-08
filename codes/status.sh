#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 智真通系统状态检查${NC}"
echo "=================================="

# 检查后端服务
echo -e "\n${YELLOW}📊 后端服务状态:${NC}"
if pgrep -f "uvicorn.*main:app" > /dev/null; then
    BACKEND_PID=$(pgrep -f "uvicorn.*main:app")
    echo -e "  ${GREEN}✅ 后端服务运行中 (PID: $BACKEND_PID)${NC}"
    
    # 检查端口
    if netstat -an 2>/dev/null | grep -q ":8000.*LISTEN" || lsof -i :8000 >/dev/null 2>&1; then
        echo -e "  ${GREEN}✅ 端口 8000 监听正常${NC}"
    else
        echo -e "  ${RED}❌ 端口 8000 未监听${NC}"
    fi
    
    # 测试API连接
    if curl -s --connect-timeout 3 http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "  ${GREEN}✅ API 健康检查通过${NC}"
    else
        echo -e "  ${YELLOW}⚠️  API 健康检查失败${NC}"
    fi
else
    echo -e "  ${RED}❌ 后端服务未运行${NC}"
fi

# 检查前端服务
echo -e "\n${YELLOW}🌐 前端服务状态:${NC}"
if pgrep -f "npm.*run.*dev" > /dev/null || pgrep -f "vite" > /dev/null; then
    FRONTEND_PID=$(pgrep -f "npm.*run.*dev" || pgrep -f "vite")
    echo -e "  ${GREEN}✅ 前端服务运行中 (PID: $FRONTEND_PID)${NC}"
    
    # 检查端口
    if netstat -an 2>/dev/null | grep -q ":8080.*LISTEN" || lsof -i :8080 >/dev/null 2>&1; then
        echo -e "  ${GREEN}✅ 端口 8080 监听正常${NC}"
    else
        echo -e "  ${RED}❌ 端口 8080 未监听${NC}"
    fi
    
    # 测试前端连接
    if curl -s --connect-timeout 3 http://localhost:8080 > /dev/null 2>&1; then
        echo -e "  ${GREEN}✅ 前端页面可访问${NC}"
    else
        echo -e "  ${YELLOW}⚠️  前端页面访问失败${NC}"
    fi
else
    echo -e "  ${RED}❌ 前端服务未运行${NC}"
fi

# 检查数据库
echo -e "\n${YELLOW}🗄️  数据库状态:${NC}"
if pgrep -f "redis-server" > /dev/null; then
    echo -e "  ${GREEN}✅ Redis 运行中${NC}"
else
    echo -e "  ${RED}❌ Redis 未运行${NC}"
fi

# 检查Elasticsearch
echo -e "\n${YELLOW}🔍 Elasticsearch状态:${NC}"
if curl -s --connect-timeout 3 http://localhost:9200/_cluster/health > /dev/null 2>&1; then
    echo -e "  ${GREEN}✅ Elasticsearch 运行中${NC}"
    
    # 获取集群健康状态
    CLUSTER_HEALTH=$(curl -s --connect-timeout 3 http://localhost:9200/_cluster/health 2>/dev/null)
    if [ $? -eq 0 ]; then
        STATUS=$(echo "$CLUSTER_HEALTH" | python -c "import sys, json; data=json.load(sys.stdin); print(data['status'])" 2>/dev/null || echo "unknown")
        echo -e "  ${BLUE}📊 集群状态: $STATUS${NC}"
    fi
else
    echo -e "  ${RED}❌ Elasticsearch 未运行${NC}"
fi

# 检查Kibana
echo -e "\n${YELLOW}📊 Kibana状态:${NC}"
if curl -s --connect-timeout 3 http://localhost:5601/api/status > /dev/null 2>&1; then
    echo -e "  ${GREEN}✅ Kibana 运行中${NC}"
else
    echo -e "  ${RED}❌ Kibana 未运行${NC}"
fi

# 检查ChromaDB
echo -e "\n${YELLOW}🗃️  ChromaDB状态:${NC}"
if curl -s --connect-timeout 3 http://localhost:8004/api/v1/heartbeat > /dev/null 2>&1; then
    echo -e "  ${GREEN}✅ ChromaDB 运行中${NC}"
    
    # 检查端口
    if netstat -an 2>/dev/null | grep -q ":8004.*LISTEN" || lsof -i :8004 >/dev/null 2>&1; then
        echo -e "  ${GREEN}✅ 端口 8004 监听正常${NC}"
    else
        echo -e "  ${RED}❌ 端口 8004 未监听${NC}"
    fi
else
    echo -e "  ${RED}❌ ChromaDB 未运行${NC}"
fi

# 检查向量化服务
echo -e "\n${YELLOW}🔢 向量化服务状态:${NC}"
if pgrep -f "vectorization_api" > /dev/null; then
    VECTORIZATION_PID=$(pgrep -f "vectorization_api")
    echo -e "  ${GREEN}✅ 向量化服务运行中 (PID: $VECTORIZATION_PID)${NC}"
    
    # 检查端口
    if netstat -an 2>/dev/null | grep -q ":8001.*LISTEN" || lsof -i :8001 >/dev/null 2>&1; then
        echo -e "  ${GREEN}✅ 端口 8001 监听正常${NC}"
    else
        echo -e "  ${RED}❌ 端口 8001 未监听${NC}"
    fi
    
    # 测试向量化API连接
    if curl -s --connect-timeout 3 http://localhost:8001/health > /dev/null 2>&1; then
        echo -e "  ${GREEN}✅ 向量化API 健康检查通过${NC}"
        
        # 获取向量化服务信息
        VECTORIZATION_INFO=$(curl -s --connect-timeout 3 http://localhost:8001/health 2>/dev/null)
        if [ $? -eq 0 ]; then
            echo -e "  ${BLUE}📊 向量化服务状态正常${NC}"
        fi
    else
        echo -e "  ${YELLOW}⚠️  向量化API 健康检查失败${NC}"
    fi
else
    echo -e "  ${RED}❌ 向量化服务未运行${NC}"
fi

# 检查知识检索服务
echo -e "\n${YELLOW}🧠 知识检索服务状态:${NC}"
if pgrep -f "start_retrieval_service.py" > /dev/null; then
    RAG_PID=$(pgrep -f "start_retrieval_service.py")
    echo -e "  ${GREEN}✅ 知识检索服务运行中 (PID: $RAG_PID)${NC}"
    
    # 检查端口
    if netstat -an 2>/dev/null | grep -q ":8002.*LISTEN" || lsof -i :8002 >/dev/null 2>&1; then
        echo -e "  ${GREEN}✅ 端口 8002 监听正常${NC}"
    else
        echo -e "  ${RED}❌ 端口 8002 未监听${NC}"
    fi
    
    # 测试知识检索API连接
    if curl -s --connect-timeout 3 http://localhost:8002/health > /dev/null 2>&1; then
        echo -e "  ${GREEN}✅ 知识检索API 健康检查通过${NC}"
        
        # 获取向量数据库信息
        RAG_INFO=$(curl -s --connect-timeout 3 http://localhost:8002/health 2>/dev/null)
        if [ $? -eq 0 ]; then
            TOTAL_VECTORS=$(echo "$RAG_INFO" | python -c "import sys, json; data=json.load(sys.stdin); print(data['data']['vector_database']['total_vectors'])" 2>/dev/null || echo "0")
            echo -e "  ${BLUE}📊 向量数量: $TOTAL_VECTORS${NC}"
        fi
    else
        echo -e "  ${YELLOW}⚠️  知识检索API 健康检查失败${NC}"
    fi
else
    echo -e "  ${RED}❌ 知识检索服务未运行${NC}"
fi

# 检查智能诊断服务
echo -e "\n${YELLOW}🔬 智能诊断服务状态:${NC}"
if pgrep -f "start_diagnosis_service.py" > /dev/null; then
    DIAGNOSIS_PID=$(pgrep -f "start_diagnosis_service.py")
    echo -e "  ${GREEN}✅ 智能诊断服务运行中 (PID: $DIAGNOSIS_PID)${NC}"
    
    # 检查端口
    if netstat -an 2>/dev/null | grep -q ":8003.*LISTEN" || lsof -i :8003 >/dev/null 2>&1; then
        echo -e "  ${GREEN}✅ 端口 8003 监听正常${NC}"
    else
        echo -e "  ${RED}❌ 端口 8003 未监听${NC}"
    fi
    
    # 测试智能诊断API连接
    if curl -s --connect-timeout 3 http://localhost:8003/diagnosis/health > /dev/null 2>&1; then
        echo -e "  ${GREEN}✅ 智能诊断API 健康检查通过${NC}"
        
        # 获取智能诊断服务信息
        DIAGNOSIS_INFO=$(curl -s --connect-timeout 3 http://localhost:8003/diagnosis/health 2>/dev/null)
        if [ $? -eq 0 ]; then
            echo -e "  ${BLUE}📊 智能诊断服务状态正常${NC}"
        fi
    else
        echo -e "  ${YELLOW}⚠️  智能诊断API 健康检查失败${NC}"
    fi
else
    echo -e "  ${RED}❌ 智能诊断服务未运行${NC}"
fi

:# 不再单独检查ES检索与混合检索服务（已合并入知识检索服务）

# 检查向量数据库目录
echo -e "\n${YELLOW}🗃️  向量数据库目录状态:${NC}"
MULTIMODAL_DB_DIR="../datas/chroma_db"

if [ -d "$MULTIMODAL_DB_DIR" ]; then
    DB_SIZE=$(du -sh "$MULTIMODAL_DB_DIR" 2>/dev/null | cut -f1)
    echo -e "  ${GREEN}✅ 多模态数据库目录存在 (大小: $DB_SIZE)${NC}"
else
    echo -e "  ${YELLOW}⚠️  多模态数据库目录不存在${NC}"
fi

# 检查日志文件
echo -e "\n${YELLOW}📝 日志文件状态:${NC}"
if [ -f "logs/backend.log" ]; then
    LOG_SIZE=$(du -sh logs/backend.log 2>/dev/null | cut -f1)
    echo -e "  ${GREEN}✅ 后端日志存在 (大小: $LOG_SIZE)${NC}"
    
    # 显示最近的错误
    ERROR_COUNT=$(grep -c "ERROR" logs/backend.log 2>/dev/null || echo "0")
    ERROR_COUNT=$(echo "$ERROR_COUNT" | tr -d '\n\r')
    if [ "$ERROR_COUNT" -gt 0 ] 2>/dev/null; then
        echo -e "  ${YELLOW}⚠️  发现 $ERROR_COUNT 个错误日志${NC}"
    fi
else
    echo -e "  ${RED}❌ 后端日志文件不存在${NC}"
fi

if [ -f "logs/frontend.log" ]; then
    LOG_SIZE=$(du -sh logs/frontend.log 2>/dev/null | cut -f1)
    echo -e "  ${GREEN}✅ 前端日志存在 (大小: $LOG_SIZE)${NC}"
else
    echo -e "  ${YELLOW}⚠️  前端日志文件不存在${NC}"
fi

if [ -f "logs/diagnosis_service.log" ]; then
    LOG_SIZE=$(du -sh logs/diagnosis_service.log 2>/dev/null | cut -f1)
    echo -e "  ${GREEN}✅ 智能诊断服务日志存在 (大小: $LOG_SIZE)${NC}"
    ERROR_COUNT=$(grep -c "ERROR" logs/diagnosis_service.log 2>/dev/null || echo "0")
    ERROR_COUNT=$(echo "$ERROR_COUNT" | tr -d '\n\r')
    if [ "$ERROR_COUNT" -gt 0 ] 2>/dev/null; then
        echo -e "  ${YELLOW}⚠️  发现 $ERROR_COUNT 个错误日志${NC}"
    fi
else
    echo -e "  ${YELLOW}⚠️  智能诊断服务日志文件不存在${NC}"
fi

# 系统资源使用情况
echo -e "\n${YELLOW}💻 系统资源:${NC}"
echo -e "  ${BLUE}CPU 使用率: $(top -l 1 | grep "CPU usage" | awk '{print $3}' | sed 's/%//')${NC}"
echo -e "  ${BLUE}内存使用: $(top -l 1 | grep "PhysMem" | awk '{print $2}')${NC}"

# 网络连接状态
echo -e "\n${YELLOW}🌐 网络连接:${NC}"
echo -e "  ${BLUE}后端 API: http://localhost:8000${NC}"
echo -e "  ${BLUE}前端界面: http://localhost:8080${NC}"
echo -e "  ${BLUE}向量化服务: http://localhost:8001${NC}"
echo -e "  ${BLUE}知识检索服务: http://localhost:8002${NC}"
echo -e "  ${BLUE}智能诊断服务: http://localhost:8003${NC}"
echo -e "  ${BLUE}ChromaDB: http://localhost:8004${NC}"
echo -e "  ${BLUE}Elasticsearch: http://localhost:9200${NC}"
echo -e "  ${BLUE}Kibana: http://localhost:5601${NC}"
echo -e "  ${BLUE}API 文档: http://localhost:8000/docs${NC}"
echo -e "  ${BLUE}向量化API文档: http://localhost:8001/docs${NC}"
echo -e "  ${BLUE}知识检索API文档: http://localhost:8002/docs${NC}"
echo -e "  ${BLUE}智能诊断API文档: http://localhost:8003/diagnosis/docs${NC}"

echo -e "\n${GREEN}✅ 状态检查完成${NC}"