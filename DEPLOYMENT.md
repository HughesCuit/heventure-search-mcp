# MCP Web Search Server 部署指南

本指南将帮助你在不同环境中部署和配置MCP Web Search Server。

## 系统要求

### 最低要求
- Python 3.8+
- 2GB RAM
- 1GB 可用磁盘空间
- 稳定的网络连接

### 推荐配置
- Python 3.10+
- 4GB RAM
- 2GB 可用磁盘空间
- 高速网络连接

## 快速部署

### 1. 克隆或下载项目

```bash
# 如果使用git
git clone <repository-url>
cd mcp_dev

# 或者直接下载并解压到目录
```

### 2. 运行自动部署脚本

```bash
./start_server.sh
```

脚本会自动：
- 检查Python环境
- 创建虚拟环境
- 安装依赖
- 运行测试（可选）
- 启动服务器

## 手动部署

### 1. 创建虚拟环境

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.12-venv

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 测试安装

```bash
python test_server.py
```

### 4. 启动服务器

```bash
python server.py
```

## 不同环境部署

### Ubuntu/Debian

```bash
# 安装系统依赖
sudo apt update
sudo apt install python3 python3-pip python3-venv

# 部署服务
cd /path/to/mcp_dev
./start_server.sh
```

### CentOS/RHEL

```bash
# 安装系统依赖
sudo yum update
sudo yum install python3 python3-pip

# 手动创建虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 启动服务
python server.py
```

### macOS

```bash
# 使用Homebrew安装Python
brew install python3

# 部署服务
cd /path/to/mcp_dev
./start_server.sh
```

### Windows

```powershell
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
python server.py
```

## Docker 部署

### 1. 创建Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 暴露端口（如果需要）
# EXPOSE 8000

# 启动命令
CMD ["python", "server.py"]
```

### 2. 构建和运行

```bash
# 构建镜像
docker build -t mcp-web-search .

# 运行容器
docker run -it mcp-web-search
```

### 3. 使用docker-compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  mcp-web-search:
    build: .
    container_name: mcp-web-search
    restart: unless-stopped
    stdin_open: true
    tty: true
```

```bash
# 启动服务
docker-compose up -d
```

## 生产环境部署

### 1. 使用systemd服务

创建服务文件 `/etc/systemd/system/mcp-web-search.service`：

```ini
[Unit]
Description=MCP Web Search Server
After=network.target

[Service]
Type=simple
User=mcp
WorkingDirectory=/opt/mcp_dev
Environment=PATH=/opt/mcp_dev/venv/bin
ExecStart=/opt/mcp_dev/venv/bin/python server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用和启动服务：

```bash
# 创建用户
sudo useradd -r -s /bin/false mcp

# 部署代码
sudo cp -r /path/to/mcp_dev /opt/
sudo chown -R mcp:mcp /opt/mcp_dev

# 启用服务
sudo systemctl daemon-reload
sudo systemctl enable mcp-web-search
sudo systemctl start mcp-web-search

# 检查状态
sudo systemctl status mcp-web-search
```

### 2. 使用进程管理器

#### PM2 (Node.js环境)

```bash
# 安装PM2
npm install -g pm2

# 创建配置文件 ecosystem.config.js
module.exports = {
  apps: [{
    name: 'mcp-web-search',
    script: 'server.py',
    interpreter: '/opt/mcp_dev/venv/bin/python',
    cwd: '/opt/mcp_dev',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G'
  }]
};

# 启动服务
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

#### Supervisor

```ini
# /etc/supervisor/conf.d/mcp-web-search.conf
[program:mcp-web-search]
command=/opt/mcp_dev/venv/bin/python server.py
directory=/opt/mcp_dev
user=mcp
autostart=true
autorestart=true
stderr_logfile=/var/log/mcp-web-search.err.log
stdout_logfile=/var/log/mcp-web-search.out.log
```

```bash
# 重新加载配置
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start mcp-web-search
```

## MCP客户端配置

### Claude Desktop

编辑配置文件 `~/.config/claude-desktop/claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "web-search": {
      "command": "/opt/mcp_dev/venv/bin/python",
      "args": ["/opt/mcp_dev/server.py"],
      "env": {
        "PYTHONPATH": "/opt/mcp_dev"
      }
    }
  }
}
```

### 其他MCP客户端

大多数MCP客户端使用类似的配置格式：

```json
{
  "servers": {
    "web-search": {
      "command": "python",
      "args": ["/path/to/server.py"],
      "cwd": "/path/to/mcp_dev"
    }
  }
}
```

## 性能优化

### 1. 系统级优化

```bash
# 增加文件描述符限制
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# 优化网络参数
echo "net.core.somaxconn = 65536" >> /etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog = 65536" >> /etc/sysctl.conf
sysctl -p
```

### 2. Python优化

```bash
# 使用更快的JSON库
pip install orjson

# 使用更快的HTTP客户端
pip install httpx[http2]
```

### 3. 缓存配置

可以添加Redis缓存来提高性能：

```python
# 在server.py中添加缓存
import redis
import json
from datetime import timedelta

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_cached_result(query):
    cached = redis_client.get(f"search:{query}")
    if cached:
        return json.loads(cached)
    return None

def cache_result(query, result):
    redis_client.setex(
        f"search:{query}", 
        timedelta(hours=1), 
        json.dumps(result)
    )
```

## 监控和日志

### 1. 日志配置

```python
# 在server.py中配置详细日志
import logging
from logging.handlers import RotatingFileHandler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('mcp-web-search.log', maxBytes=10485760, backupCount=5),
        logging.StreamHandler()
    ]
)
```

### 2. 健康检查

```python
# 添加健康检查端点
from aiohttp import web

async def health_check(request):
    return web.json_response({"status": "healthy", "timestamp": time.time()})

# 在main函数中添加HTTP服务器（可选）
app = web.Application()
app.router.add_get('/health', health_check)
web.run_app(app, host='0.0.0.0', port=8080)
```

### 3. 监控脚本

```bash
#!/bin/bash
# monitor.sh

while true; do
    if ! pgrep -f "python.*server.py" > /dev/null; then
        echo "$(date): MCP服务器已停止，正在重启..."
        cd /opt/mcp_dev
        source venv/bin/activate
        nohup python server.py > /dev/null 2>&1 &
    fi
    sleep 30
done
```

## 故障排除

### 常见问题

1. **端口占用**
   ```bash
   # 查找占用端口的进程
   lsof -i :8080
   # 杀死进程
   kill -9 <PID>
   ```

2. **权限问题**
   ```bash
   # 修复文件权限
   chmod +x start_server.sh
   chown -R user:group /path/to/mcp_dev
   ```

3. **依赖冲突**
   ```bash
   # 重新创建虚拟环境
   rm -rf venv
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **网络问题**
   ```bash
   # 测试网络连接
   curl -I https://duckduckgo.com
   # 检查DNS
   nslookup duckduckgo.com
   ```

### 调试模式

```bash
# 启用调试模式
export PYTHONPATH=/path/to/mcp_dev
export MCP_DEBUG=1
python server.py
```

## 安全考虑

### 1. 网络安全

- 使用防火墙限制访问
- 配置SSL/TLS（如果需要网络访问）
- 定期更新依赖包

### 2. 系统安全

```bash
# 创建专用用户
sudo useradd -r -s /bin/false mcp

# 限制文件权限
chmod 750 /opt/mcp_dev
chown -R mcp:mcp /opt/mcp_dev
```

### 3. 应用安全

- 限制搜索频率
- 过滤恶意查询
- 监控异常活动

## 备份和恢复

### 备份脚本

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/mcp_dev"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/mcp_dev_$DATE.tar.gz /opt/mcp_dev

# 保留最近7天的备份
find $BACKUP_DIR -name "mcp_dev_*.tar.gz" -mtime +7 -delete
```

### 恢复步骤

```bash
# 停止服务
sudo systemctl stop mcp-web-search

# 恢复文件
tar -xzf /backup/mcp_dev/mcp_dev_YYYYMMDD_HHMMSS.tar.gz -C /

# 重启服务
sudo systemctl start mcp-web-search
```

这个部署指南涵盖了从开发环境到生产环境的各种部署场景，帮助你在任何环境中成功部署MCP Web Search Server。