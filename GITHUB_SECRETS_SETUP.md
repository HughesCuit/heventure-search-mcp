# GitHub Secrets 设置指南

为了让自动发布到 PyPI 的 GitHub Actions 工作流正常运行，您需要在 GitHub 仓库中设置以下 Secrets。

## 必需的 Secrets

### 1. PYPI_API_TOKEN

这是发布到 PyPI 所需的 API 令牌。

**设置步骤：**

1. 访问您的 GitHub 仓库页面
2. 点击 **Settings** 选项卡
3. 在左侧菜单中选择 **Secrets and variables** → **Actions**
4. 点击 **New repository secret**
5. 设置以下信息：
   - **Name**: `PYPI_API_TOKEN`
   - **Secret**: `YOUR_PYPI_API_TOKEN`
6. 点击 **Add secret**

### 2. TEST_PYPI_API_TOKEN (可选)

如果您想要先在 Test PyPI 上测试发布，可以设置此令牌。

**获取 Test PyPI API Token：**

1. 访问 [Test PyPI](https://test.pypi.org/)
2. 登录您的账户
3. 进入 Account settings → API tokens
4. 创建新的 API token
5. 按照上述步骤将其添加为 `TEST_PYPI_API_TOKEN`

## 工作流触发条件

自动发布工作流会在以下情况下触发：

### 自动触发
- 当推送到 `main` 分支时
- 且修改了以下文件之一：
  - `server.py`
  - `pyproject.toml`
  - `setup.py`
  - `__init__.py`
  - 任何 `.py` 文件

### 手动触发
- 在 GitHub Actions 页面手动运行工作流
- 可以选择版本更新类型：`patch`、`minor`、`major`

## 版本管理

工作流会自动处理版本管理：

1. **检查当前版本**：读取 `pyproject.toml` 中的版本号
2. **检查 PyPI 版本**：获取 PyPI 上已发布的最新版本
3. **版本比较**：
   - 如果本地版本 ≤ PyPI 版本，自动递增版本号
   - 如果本地版本 > PyPI 版本，直接发布当前版本
   - 如果是首次发布，直接发布当前版本

## 发布流程

1. **版本检查和更新**
   - 自动检测是否需要更新版本
   - 更新 `pyproject.toml` 和 `__init__.py` 中的版本号
   - 提交版本更新到 Git

2. **包构建**
   - 使用 `python -m build` 构建包
   - 检查包的完整性

3. **发布到 PyPI**
   - 使用 `twine` 上传到 PyPI
   - 创建 Git 标签
   - 创建 GitHub Release
   - 更新 CHANGELOG.md

## 安全注意事项

- ✅ **已正确设置**：API Token 存储在 GitHub Secrets 中，不会暴露在代码中
- ✅ **权限控制**：只有仓库管理员可以查看和修改 Secrets
- ✅ **令牌范围**：PyPI API Token 只能用于指定的包

## 故障排除

### 常见问题

1. **工作流失败："Invalid credentials"**
   - 检查 `PYPI_API_TOKEN` 是否正确设置
   - 确认 API Token 没有过期

2. **工作流失败："Package already exists"**
   - 版本号可能已经存在于 PyPI
   - 工作流会自动处理版本递增

3. **工作流不触发**
   - 检查推送的分支是否为 `main`
   - 确认修改的文件在触发路径中

### 查看工作流状态

1. 访问仓库的 **Actions** 选项卡
2. 查看最近的工作流运行
3. 点击具体的运行查看详细日志

## 手动发布

如果需要手动控制发布过程：

1. 访问 **Actions** 选项卡
2. 选择 "Auto Publish to PyPI" 工作流
3. 点击 **Run workflow**
4. 选择版本更新类型（patch/minor/major）
5. 点击 **Run workflow** 确认

## 验证发布

发布成功后，您可以：

1. 访问 [PyPI 项目页面](https://pypi.org/project/heventure-search-mcp/)
2. 检查 GitHub Releases 页面
3. 测试安装：`pip install heventure-search-mcp`

---

**注意**：首次设置完成后，所有后续的发布都将自动进行，无需手动干预。