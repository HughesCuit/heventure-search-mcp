#!/bin/bash

# MCP Web Search Server 启动脚本

echo "=================================="
echo "MCP Web Search Server 启动脚本"
echo "=================================="

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: Python3 未安装"
    exit 1
fi

# 检查pip是否安装
if ! command -v pip3 &> /dev/null; then
    echo "错误: pip3 未安装"
    exit 1
fi

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "当前工作目录: $SCRIPT_DIR"

# 检查requirements.txt是否存在
if [ ! -f "requirements.txt" ]; then
    echo "错误: requirements.txt 文件不存在"
    exit 1
fi

# 检查server.py是否存在
if [ ! -f "server.py" ]; then
    echo "错误: server.py 文件不存在"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "错误: 虚拟环境创建失败"
        exit 1
    fi
fi

# 激活虚拟环境并安装依赖
echo "激活虚拟环境并安装依赖..."
source venv/bin/activate
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "错误: 依赖安装失败"
    exit 1
fi

echo "依赖安装完成"

# 询问用户是否要运行测试
read -p "是否要先运行测试? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "正在运行测试..."
    source venv/bin/activate
    python test_server.py
    echo "测试完成"
    echo
fi

# 询问用户启动方式
echo "请选择启动方式:"
echo "1. 直接启动服务器 (stdio模式)"
echo "2. 显示配置信息"
echo "3. 退出"
read -p "请输入选择 (1-3): " -n 1 -r
echo

case $REPLY in
    1)
        echo "正在启动 MCP Web Search Server..."
        echo "使用 Ctrl+C 停止服务器"
        echo "=================================="
        source venv/bin/activate
        python server.py
        ;;
    2)
        echo "MCP 配置信息:"
        echo "=================================="
        echo "服务器名称: web-search-server"
        echo "服务器版本: 1.0.0"
        echo "服务器路径: $SCRIPT_DIR/server.py"
        echo
        echo "MCP 客户端配置示例:"
        cat config.json
        echo
        echo "可用工具:"
        echo "1. web_search - 网页搜索"
        echo "2. get_webpage_content - 获取网页内容"
        ;;
    3)
        echo "退出"
        exit 0
        ;;
    *)
        echo "无效选择"
        exit 1
        ;;
esac