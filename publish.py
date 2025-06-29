#!/usr/bin/env python3
"""
发布脚本 - 自动化PyPI发布流程
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, check=True):
    """运行命令并打印输出"""
    print(f"运行命令: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    if check and result.returncode != 0:
        print(f"命令执行失败，退出码: {result.returncode}")
        sys.exit(1)
    
    return result

def clean_build():
    """清理构建文件"""
    print("清理构建文件...")
    dirs_to_clean = ['build', 'dist', '*.egg-info']
    for pattern in dirs_to_clean:
        for path in Path('.').glob(pattern):
            if path.is_dir():
                shutil.rmtree(path)
                print(f"删除目录: {path}")
            else:
                path.unlink()
                print(f"删除文件: {path}")

def check_requirements():
    """检查发布要求"""
    print("检查发布要求...")
    
    # 检查必要文件
    required_files = ['README.md', 'pyproject.toml', 'server.py']
    for file in required_files:
        if not Path(file).exists():
            print(f"错误: 缺少必要文件 {file}")
            sys.exit(1)
    
    # 检查是否安装了构建工具
    try:
        import build
        import twine
    except ImportError as e:
        print(f"错误: 缺少必要的构建工具: {e}")
        print("请运行: pip install build twine")
        sys.exit(1)
    
    print("✓ 所有要求检查通过")

def build_package():
    """构建包"""
    print("构建包...")
    run_command("python -m build")
    print("✓ 包构建完成")

def check_package():
    """检查包"""
    print("检查包...")
    run_command("python -m twine check dist/*")
    print("✓ 包检查通过")

def upload_to_testpypi():
    """上传到TestPyPI"""
    print("上传到TestPyPI...")
    print("请确保已配置TestPyPI的API token")
    run_command("python -m twine upload --repository testpypi dist/*")
    print("✓ 已上传到TestPyPI")

def upload_to_pypi():
    """上传到PyPI"""
    print("上传到PyPI...")
    print("请确保已配置PyPI的API token")
    
    confirm = input("确认要发布到正式PyPI吗? (y/N): ")
    if confirm.lower() != 'y':
        print("取消发布")
        return
    
    run_command("python -m twine upload dist/*")
    print("✓ 已发布到PyPI")

def main():
    """主函数"""
    print("=== MCP Web Search Server 发布脚本 ===")
    
    if len(sys.argv) > 1:
        action = sys.argv[1]
    else:
        print("可用操作:")
        print("  test    - 构建并发布到TestPyPI")
        print("  prod    - 构建并发布到PyPI")
        print("  build   - 仅构建包")
        print("  clean   - 清理构建文件")
        action = input("请选择操作 (test/prod/build/clean): ").strip()
    
    if action == "clean":
        clean_build()
    elif action == "build":
        check_requirements()
        clean_build()
        build_package()
        check_package()
    elif action == "test":
        check_requirements()
        clean_build()
        build_package()
        check_package()
        upload_to_testpypi()
    elif action == "prod":
        check_requirements()
        clean_build()
        build_package()
        check_package()
        upload_to_pypi()
    else:
        print(f"未知操作: {action}")
        sys.exit(1)
    
    print("\n=== 发布完成 ===")

if __name__ == "__main__":
    main()