#!/bin/bash

# RAG检索增强系统监控脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查服务状态
check_service_status() {
    log_info "检查RAG服务状态..."
    
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        log_success "RAG服务运行正常"
        return 0
    else
        log_error "RAG服务未运行或异常"
        return 1
    fi
}

# 检查进程状态
check_process_status() {
    log_info "检查进程状态..."
    
    if pgrep -f "start_rag_service.py" > /dev/null; then
        log_success "RAG服务进程正在运行"
        echo "进程ID: $(pgrep -f start_rag_service.py)"
    else
        log_error "RAG服务进程未运行"
    fi
}

# 检查端口状态
check_port_status() {
    log_info "检查端口状态..."
    
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null; then
        log_success "端口8000正在监听"
        echo "监听进程: $(lsof -Pi :8000 -sTCP:LISTEN -t)"
    else
        log_error "端口8000未被监听"
    fi
}

# 检查资源使用
check_resource_usage() {
    log_info "检查资源使用情况..."
    
    if pgrep -f "start_rag_service.py" > /dev/null; then
        pid=$(pgrep -f start_rag_service.py)
        echo "CPU使用率: $(ps -p $pid -o %cpu --no-headers)%"
        echo "内存使用: $(ps -p $pid -o %mem --no-headers)%"
        echo "内存大小: $(ps -p $pid -o rss --no-headers) KB"
    else
        log_warning "无法获取资源使用情况（进程未运行）"
    fi
}

# 检查日志文件
check_logs() {
    log_info "检查日志文件..."
    
    if [ -f "logs/rag_service.log" ]; then
        log_success "日志文件存在"
        echo "日志文件大小: $(du -h logs/rag_service.log | cut -f1)"
        echo "最后10行日志:"
        tail -10 logs/rag_service.log
    else
        log_warning "日志文件不存在"
    fi
}

# 检查API响应
check_api_response() {
    log_info "检查API响应..."
    
    # 健康检查
    echo "健康检查响应:"
    curl -s http://localhost:8000/health | /opt/anaconda3/bin/conda run -n nlp python -m json.tool 2>/dev/null || echo "健康检查失败"
    
    echo ""
    echo "API文档可访问性:"
    if curl -f http://localhost:8000/docs >/dev/null 2>&1; then
        log_success "API文档可访问"
    else
        log_error "API文档不可访问"
    fi
}

# 显示系统信息
show_system_info() {
    log_info "系统信息..."
    
    echo "操作系统: $(uname -s)"
    echo "内核版本: $(uname -r)"
    echo "Python版本: $(/opt/anaconda3/bin/conda run -n nlp python --version)"
    echo "当前时间: $(date)"
    echo "运行时间: $(uptime)"
}

# 性能测试
performance_test() {
    log_info "执行性能测试..."
    
    if [ -f "test_rag_service.py" ]; then
        echo "运行性能测试..."
        /opt/anaconda3/bin/conda run -n nlp python test_rag_service.py --performance
    else
        log_warning "性能测试文件不存在"
    fi
}

# 主监控函数
monitor() {
    echo "=========================================="
    echo "    RAG检索增强系统监控面板"
    echo "=========================================="
    echo ""
    
    show_system_info
    echo ""
    
    check_process_status
    echo ""
    
    check_port_status
    echo ""
    
    check_service_status
    echo ""
    
    check_resource_usage
    echo ""
    
    check_logs
    echo ""
    
    check_api_response
    echo ""
}

# 实时监控
realtime_monitor() {
    log_info "启动实时监控（按Ctrl+C退出）..."
    
    while true; do
        clear
        monitor
        echo ""
        echo "下次更新: 5秒后..."
        sleep 5
    done
}

# 显示帮助
show_help() {
    echo "RAG检索增强系统监控脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示帮助信息"
    echo "  -r, --realtime 实时监控模式"
    echo "  -p, --performance 执行性能测试"
    echo "  -s, --status   检查服务状态"
    echo ""
    echo "示例:"
    echo "  $0              # 显示完整监控信息"
    echo "  $0 -r           # 实时监控"
    echo "  $0 -p           # 性能测试"
    echo "  $0 -s           # 快速状态检查"
}

# 主函数
main() {
    case "${1:-}" in
        -h|--help)
            show_help
            ;;
        -r|--realtime)
            realtime_monitor
            ;;
        -p|--performance)
            performance_test
            ;;
        -s|--status)
            check_service_status
            ;;
        "")
            monitor
            ;;
        *)
            echo "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
