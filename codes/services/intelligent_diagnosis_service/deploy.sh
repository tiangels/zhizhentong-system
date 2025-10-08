#!/bin/bash

# 智诊通智能诊断服务部署脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 服务配置
SERVICE_NAME="intelligent_diagnosis_service"
SERVICE_PORT=8003
SERVICE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SERVICE_DIR/logs"
PID_FILE="$SERVICE_DIR/$SERVICE_NAME.pid"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# 检查服务是否运行
is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    else
        return 1
    fi
}

# 启动服务
start_service() {
    log_info "启动智诊通智能诊断服务..."
    
    if is_running; then
        log_warn "服务已在运行中 (PID: $(cat $PID_FILE))"
        return 0
    fi
    
    # 检查Python环境
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装"
        return 1
    fi
    
    # 检查依赖
    log_info "检查依赖..."
    if ! python3 -c "import fastapi, uvicorn" 2>/dev/null; then
        log_error "缺少必要依赖，请安装: pip install fastapi uvicorn"
        return 1
    fi
    
    # 启动服务
    log_info "启动服务进程..."
    cd "$SERVICE_DIR"
    nohup python3 start_diagnosis_service.py --host 0.0.0.0 --port $SERVICE_PORT > "$LOG_DIR/service.log" 2>&1 &
    local pid=$!
    echo $pid > "$PID_FILE"
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 3
    
    if is_running; then
        log_info "✅ 服务启动成功 (PID: $pid)"
        log_info "服务地址: http://localhost:$SERVICE_PORT"
        log_info "API文档: http://localhost:$SERVICE_PORT/diagnosis/docs"
        log_info "健康检查: http://localhost:$SERVICE_PORT/diagnosis/health"
        return 0
    else
        log_error "❌ 服务启动失败"
        return 1
    fi
}

# 停止服务
stop_service() {
    log_info "停止智诊通智能诊断服务..."
    
    if ! is_running; then
        log_warn "服务未运行"
        return 0
    fi
    
    local pid=$(cat "$PID_FILE")
    log_info "停止服务进程 (PID: $pid)..."
    
    # 优雅停止
    kill -TERM "$pid" 2>/dev/null || true
    
    # 等待进程结束
    local count=0
    while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 10 ]; do
        sleep 1
        count=$((count + 1))
    done
    
    # 强制停止
    if ps -p "$pid" > /dev/null 2>&1; then
        log_warn "强制停止服务进程..."
        kill -KILL "$pid" 2>/dev/null || true
    fi
    
    rm -f "$PID_FILE"
    log_info "✅ 服务已停止"
}

# 重启服务
restart_service() {
    log_info "重启智诊通智能诊断服务..."
    stop_service
    sleep 2
    start_service
}

# 查看服务状态
status_service() {
    log_info "智诊通智能诊断服务状态:"
    
    if is_running; then
        local pid=$(cat "$PID_FILE")
        log_info "✅ 服务运行中 (PID: $pid)"
        log_info "服务地址: http://localhost:$SERVICE_PORT"
        
        # 检查健康状态
        log_info "检查服务健康状态..."
        if command -v curl &> /dev/null; then
            if curl -s "http://localhost:$SERVICE_PORT/diagnosis/health" > /dev/null; then
                log_info "✅ 服务健康检查通过"
            else
                log_warn "⚠️ 服务健康检查失败"
            fi
        else
            log_warn "curl 未安装，无法进行健康检查"
        fi
    else
        log_error "❌ 服务未运行"
    fi
}

# 查看日志
view_logs() {
    log_info "查看服务日志..."
    if [ -f "$LOG_DIR/service.log" ]; then
        tail -f "$LOG_DIR/service.log"
    else
        log_warn "日志文件不存在: $LOG_DIR/service.log"
    fi
}

# 测试服务
test_service() {
    log_info "测试智诊通智能诊断服务..."
    
    if ! is_running; then
        log_error "服务未运行，无法测试"
        return 1
    fi
    
    cd "$SERVICE_DIR"
    python3 test_diagnosis_service.py --url "http://localhost:$SERVICE_PORT"
}

# 显示帮助
show_help() {
    echo "智诊通智能诊断服务管理脚本"
    echo ""
    echo "用法: $0 {start|stop|restart|status|logs|test|help}"
    echo ""
    echo "命令:"
    echo "  start    - 启动服务"
    echo "  stop     - 停止服务"
    echo "  restart  - 重启服务"
    echo "  status   - 查看服务状态"
    echo "  logs     - 查看服务日志"
    echo "  test     - 测试服务"
    echo "  help     - 显示帮助"
    echo ""
    echo "服务信息:"
    echo "  服务名称: $SERVICE_NAME"
    echo "  服务端口: $SERVICE_PORT"
    echo "  服务目录: $SERVICE_DIR"
    echo "  日志目录: $LOG_DIR"
}

# 主函数
main() {
    case "${1:-help}" in
        start)
            start_service
            ;;
        stop)
            stop_service
            ;;
        restart)
            restart_service
            ;;
        status)
            status_service
            ;;
        logs)
            view_logs
            ;;
        test)
            test_service
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
