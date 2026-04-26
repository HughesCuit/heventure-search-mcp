# 贡献指南

欢迎贡献 heventure-search-mcp！

## 开发环境设置

```bash
# 克隆项目
git clone https://github.com/HughesCuit/heventure-search-mcp.git
cd heventure-search-mcp

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -e ".[dev]"
# 或
pip install -r requirements.txt
pip install pytest pytest-asyncio ruff
```

## 代码规范

- 使用 **ruff** 进行代码检查和格式化
- 运行 `ruff check .` 检查代码
- 运行 `ruff format .` 格式化代码

```bash
# 检查代码
ruff check .

# 自动修复
ruff check . --fix

# 格式化
ruff format .
```

## 测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行单元测试（跳过集成测试）
python -m pytest tests/ -v -m "not integration"

# 运行集成测试
python -m pytest tests/ -v -m integration
```

## 提交 PR

1. Fork 项目
2. 创建特性分支：`git checkout -b feature/your-feature`
3. 编写代码并确保通过测试
4. 运行 `ruff check .` 确保无警告
5. 提交更改：`git commit -m "Add feature: ..."`
6. Push 到你的仓库：`git push origin feature/your-feature`
7. 创建 Pull Request

## 项目结构

```
heventure-search-mcp/
├── server.py          # 主服务器
├── tests/             # 测试用例
│   └── test_server.py
├── pyproject.toml     # 项目配置
├── requirements.txt   # 依赖
├── publish.py         # 发布脚本
└── README.md         # 项目文档
```

## 发布新版本

```bash
# 更新版本号（在 pyproject.toml）
# 更新 CHANGELOG.md

# 发布到 PyPI
python publish.py prod
```

## 许可证

MIT License
