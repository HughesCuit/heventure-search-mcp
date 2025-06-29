# PyPI 发布指南

本文档详细说明如何将 `heventure-search-mcp` 项目发布到 PyPI。

## 前置要求

### 1. 安装构建工具

```bash
pip install build twine
```

### 2. 配置 PyPI 账户

#### 注册账户
- 正式 PyPI: https://pypi.org/account/register/
- 测试 PyPI: https://test.pypi.org/account/register/

#### 生成 API Token
1. 登录 PyPI 账户
2. 进入 Account Settings → API tokens
3. 创建新的 API token
4. 复制生成的 token

#### 配置 ~/.pypirc

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-your-api-token-here

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-your-test-api-token-here
```

## 发布流程

### 方式一：使用自动化脚本（推荐）

项目包含了自动化发布脚本 `publish.py`：

```bash
# 发布到测试 PyPI
python publish.py test

# 发布到正式 PyPI
python publish.py prod

# 仅构建包（不上传）
python publish.py build

# 清理构建文件
python publish.py clean
```

### 方式二：手动发布

#### 1. 清理旧的构建文件

```bash
rm -rf build/ dist/ *.egg-info/
```

#### 2. 构建包

```bash
python -m build
```

#### 3. 检查包

```bash
python -m twine check dist/*
```

#### 4. 上传到测试 PyPI

```bash
python -m twine upload --repository testpypi dist/*
```

#### 5. 测试安装

```bash
# 从测试 PyPI 安装
pip install --index-url https://test.pypi.org/simple/ heventure-search-mcp

# 测试运行
heventure-search-mcp
```

#### 6. 上传到正式 PyPI

```bash
python -m twine upload dist/*
```

## 发布前检查清单

- [ ] 更新版本号（在 `pyproject.toml` 中）
- [ ] 更新 `CHANGELOG.md`
- [ ] 确保所有测试通过
- [ ] 检查 README.md 格式正确
- [ ] 验证依赖项版本
- [ ] 确保 `pyproject.toml` 配置正确
- [ ] 测试本地安装：`pip install -e .`
- [ ] 运行基准测试：`python benchmark.py`

## 版本管理

项目遵循 [语义化版本](https://semver.org/lang/zh-CN/) 规范：

- **主版本号**：不兼容的 API 修改
- **次版本号**：向下兼容的功能性新增
- **修订号**：向下兼容的问题修正

### 版本号更新位置

1. `pyproject.toml` 中的 `version` 字段
2. `__init__.py` 中的 `__version__` 变量

## 发布后验证

### 1. 检查 PyPI 页面

访问 https://pypi.org/project/heventure-search-mcp/ 确认：
- 项目描述正确显示
- README 格式正确
- 依赖项列表正确
- 分类标签正确

### 2. 测试安装

```bash
# 创建新的虚拟环境
python -m venv test_env
source test_env/bin/activate  # Linux/macOS
# 或 test_env\Scripts\activate  # Windows

# 从 PyPI 安装
pip install heventure-search-mcp

# 测试运行
heventure-search-mcp

# 测试 uvx
uvx heventure-search-mcp
```

### 3. 更新文档

发布成功后，确保以下文档是最新的：
- README.md 中的安装说明
- 项目主页的链接
- 示例代码和用法说明

## 常见问题

### 1. 构建失败

**问题**：`python -m build` 失败

**解决方案**：
- 检查 `pyproject.toml` 语法
- 确保所有依赖项都已安装
- 检查文件路径和权限

### 2. 上传失败

**问题**：`twine upload` 失败

**解决方案**：
- 检查 API token 是否正确
- 确认包名没有冲突
- 检查网络连接

### 3. 版本冲突

**问题**：版本号已存在

**解决方案**：
- 更新版本号
- 不能覆盖已发布的版本

### 4. 依赖问题

**问题**：安装时依赖解析失败

**解决方案**：
- 检查依赖版本约束
- 测试在干净环境中的安装
- 更新依赖版本范围

## 回滚策略

如果发布的版本有问题：

1. **不能删除已发布的版本**
2. **发布修复版本**：增加修订号
3. **标记为 yanked**：在 PyPI 页面标记问题版本
4. **更新文档**：说明问题和解决方案

## 自动化发布

考虑使用 GitHub Actions 进行自动化发布：

```yaml
# .github/workflows/publish.yml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.x'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine
    - name: Build package
      run: python -m build
    - name: Publish to PyPI
      uses: pypa/gh-action-pypi-publish@release/v1
      with:
        password: ${{ secrets.PYPI_API_TOKEN }}
```

## 联系方式

如有发布相关问题，请：

1. 查看 [PyPI 官方文档](https://packaging.python.org/)
2. 在项目 GitHub 仓库提交 Issue
3. 联系项目维护者