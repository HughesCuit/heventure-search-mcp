#!/bin/bash

# MCP Web Search Server 基准测试启动脚本
# 用于运行各种类型的性能测试

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查虚拟环境
check_venv() {
    if [ ! -d "venv" ]; then
        print_error "虚拟环境不存在，请先运行 ./start_server.sh 创建环境"
        exit 1
    fi
    
    if [ ! -f "venv/bin/activate" ]; then
        print_error "虚拟环境激活脚本不存在"
        exit 1
    fi
}

# 检查依赖
check_dependencies() {
    print_info "检查依赖..."
    
    source venv/bin/activate
    
    # 检查必要的Python包
    python -c "import aiohttp, bs4, mcp" 2>/dev/null || {
        print_error "缺少必要的依赖包，请运行 ./start_server.sh 安装依赖"
        exit 1
    }
    
    # 检查psutil（用于系统监控）
    python -c "import psutil" 2>/dev/null || {
        print_warning "psutil未安装，将安装用于系统监控"
        pip install psutil
    }
    
    print_success "依赖检查完成"
}

# 显示帮助信息
show_help() {
    echo "MCP Web Search Server 基准测试工具"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -q, --quick        运行快速基准测试 (默认)"
    echo "  -f, --full         运行完整基准测试"
    echo "  -s, --stress       运行压力测试"
    echo "  -r, --report       仅生成报告 (基于现有结果)"
    echo "  -c, --clean        清理测试结果文件"
    echo "  -h, --help         显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 --quick         # 运行快速测试"
    echo "  $0 --full          # 运行完整测试"
    echo "  $0 --stress        # 运行压力测试"
    echo "  $0 --report        # 生成报告"
    echo ""
}

# 运行快速基准测试
run_quick_benchmark() {
    print_info "开始运行快速基准测试..."
    
    source venv/bin/activate
    python quick_benchmark.py
    
    if [ $? -eq 0 ]; then
        print_success "快速基准测试完成"
        generate_report
    else
        print_error "快速基准测试失败"
        exit 1
    fi
}

# 运行完整基准测试
run_full_benchmark() {
    print_info "开始运行完整基准测试..."
    print_warning "完整测试可能需要几分钟时间，请耐心等待..."
    
    source venv/bin/activate
    python benchmark.py
    
    if [ $? -eq 0 ]; then
        print_success "完整基准测试完成"
        generate_report
    else
        print_error "完整基准测试失败"
        exit 1
    fi
}

# 运行压力测试
run_stress_test() {
    print_info "开始运行压力测试..."
    print_warning "压力测试将持续运行，可能对系统造成较高负载"
    
    read -p "确认要继续吗? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "压力测试已取消"
        exit 0
    fi
    
    source venv/bin/activate
    python -c "
import asyncio
from benchmark import MCPBenchmark

async def stress_test():
    benchmark = MCPBenchmark()
    results = await benchmark.run_stress_test(120)  # 2分钟压力测试
    benchmark.print_results('压力测试', results)
    
    # 保存结果
    import json
    with open('stress_test_results.json', 'w', encoding='utf-8') as f:
        json.dump([results.get_statistics()], f, ensure_ascii=False, indent=2)

asyncio.run(stress_test())
"
    
    if [ $? -eq 0 ]; then
        print_success "压力测试完成"
        # 为压力测试生成专门的报告
        source venv/bin/activate
        python -c "
import json
from benchmark_report import BenchmarkReportGenerator

with open('stress_test_results.json', 'r', encoding='utf-8') as f:
    results = json.load(f)

generator = BenchmarkReportGenerator()
generator.generate_markdown_report(results, 'stress_test_report.md')
print('压力测试报告已生成: stress_test_report.md')
"
    else
        print_error "压力测试失败"
        exit 1
    fi
}

# 生成报告
generate_report() {
    print_info "生成测试报告..."
    
    source venv/bin/activate
    python benchmark_report.py
    
    if [ $? -eq 0 ]; then
        print_success "测试报告生成完成"
        echo ""
        print_info "生成的文件:"
        [ -f "benchmark_report.md" ] && echo "  📄 benchmark_report.md - 详细报告"
        [ -f "benchmark_results.csv" ] && echo "  📊 benchmark_results.csv - CSV数据"
        [ -f "quick_benchmark_results.json" ] && echo "  📋 quick_benchmark_results.json - JSON结果"
        [ -f "benchmark_results.json" ] && echo "  📋 benchmark_results.json - 完整结果"
        [ -f "stress_test_results.json" ] && echo "  🔥 stress_test_results.json - 压力测试结果"
        [ -f "stress_test_report.md" ] && echo "  🔥 stress_test_report.md - 压力测试报告"
    else
        print_error "报告生成失败"
        exit 1
    fi
}

# 清理测试结果文件
clean_results() {
    print_info "清理测试结果文件..."
    
    files_to_clean=(
        "quick_benchmark_results.json"
        "benchmark_results.json"
        "stress_test_results.json"
        "benchmark_report.md"
        "benchmark_results.csv"
        "stress_test_report.md"
    )
    
    cleaned_count=0
    for file in "${files_to_clean[@]}"; do
        if [ -f "$file" ]; then
            rm "$file"
            print_info "已删除: $file"
            ((cleaned_count++))
        fi
    done
    
    if [ $cleaned_count -eq 0 ]; then
        print_info "没有找到需要清理的文件"
    else
        print_success "已清理 $cleaned_count 个文件"
    fi
}

# 显示系统信息
show_system_info() {
    print_info "系统信息:"
    echo "  操作系统: $(uname -s) $(uname -r)"
    echo "  Python版本: $(python3 --version 2>/dev/null || echo '未安装')"
    echo "  当前目录: $(pwd)"
    echo "  虚拟环境: $([ -d venv ] && echo '已创建' || echo '未创建')"
    echo ""
}

# 主函数
main() {
    # 显示标题
    echo "🚀 MCP Web Search Server 基准测试工具"
    echo "================================================"
    echo ""
    
    # 显示系统信息
    show_system_info
    
    # 检查虚拟环境
    check_venv
    
    # 检查依赖
    check_dependencies
    
    # 解析命令行参数
    case "${1:-quick}" in
        -q|--quick|quick)
            run_quick_benchmark
            ;;
        -f|--full|full)
            run_full_benchmark
            ;;
        -s|--stress|stress)
            run_stress_test
            ;;
        -r|--report|report)
            generate_report
            ;;
        -c|--clean|clean)
            clean_results
            ;;
        -h|--help|help)
            show_help
            ;;
        *)
            print_error "未知选项: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"