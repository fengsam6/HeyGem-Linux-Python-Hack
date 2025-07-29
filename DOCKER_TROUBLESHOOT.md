# Docker 故障排除指南

## 问题描述

当启动Docker容器时遇到以下错误：
```
[notice] A new release of pip is available: 23.0.1 -> 25.0.1
heygem-gen-video  | [notice] To update, run: /usr/local/python3/bin/python3.8 -m pip install --upgrade pip
heygem-gen-video  | bash: gunicorn: command not found
heygem-gen-video exited with code 127
```

## 解决方案

我们已经创建了一个健壮的Docker启动脚本来处理这些问题。

### 🔧 修复内容

1. **新增 `docker_start.sh`** - 专门的Docker容器启动脚本
2. **更新所有Docker Compose文件** - 使用新的启动脚本
3. **改进 `app_production.py`** - 智能检测gunicorn命令

### 📋 故障排除步骤

#### 步骤1：重新构建和启动

```bash
# 停止现有容器
docker-compose -f deploy/docker-compose-lite.yml down

# 重新启动
docker-compose -f deploy/docker-compose-lite.yml up -d

# 查看启动日志
docker logs heygem-gen-video -f
```

#### 步骤2：检查容器内部状态

```bash
# 进入容器
docker exec -it heygem-gen-video bash

# 手动检查Python和pip
python --version
pip --version

# 手动安装gunicorn
pip install gunicorn>=21.2.0

# 检查gunicorn
python -c "import gunicorn; print(gunicorn.__version__)"

# 尝试启动
python /code/app_production.py
```

#### 步骤3：查看详细启动日志

新的启动脚本会提供详细的诊断信息：

```
==========================================
HeyGem AI Docker Container Starting...
==========================================
🐍 Python版本：
📦 当前pip版本：
⬆️ 升级pip...
✅ pip升级完成
📥 安装Gunicorn...
✅ Gunicorn安装完成
🔍 验证Gunicorn安装...
✅ Gunicorn导入成功
✅ 找到Gunicorn命令: /usr/local/bin/gunicorn
🧪 测试Gunicorn命令...
✅ gunicorn命令可用
🔧 检查服务配置...
✅ 应用文件检查通过
🚀 启动生产服务器...
```

### 🚨 常见问题和解决方案

#### 问题1：pip版本过旧
**症状**：看到pip升级提示
**解决**：脚本会自动升级pip

#### 问题2：gunicorn命令未找到
**症状**：`bash: gunicorn: command not found`
**解决方案**：
1. 脚本会自动安装gunicorn
2. 如果命令仍未找到，会使用 `python -m gunicorn`
3. 最终回退到Flask服务器

#### 问题3：权限问题
**症状**：Permission denied
**解决**：
```bash
# 确保脚本有执行权限
chmod +x docker_start.sh
```

#### 问题4：路径问题
**症状**：模块找不到
**解决**：脚本会自动设置工作目录为 `/code`

### 📊 启动模式检测

新的系统会按以下顺序尝试：

1. **优先**：直接使用 `gunicorn` 命令
2. **备选**：使用 `python -m gunicorn`
3. **回退**：使用Flask开发服务器

### 🔍 调试命令

如果仍有问题，可以使用以下调试命令：

```bash
# 查看容器进程
docker ps -a

# 查看容器详细信息
docker inspect heygem-gen-video

# 查看容器资源使用
docker stats heygem-gen-video

# 查看容器网络
docker network ls
docker network inspect ai_network

# 重新构建镜像（如果需要）
docker-compose -f deploy/docker-compose-lite.yml build
```

### 🆘 紧急回退方案

如果新的启动方式仍有问题，可以临时回退：

1. **临时修改Docker Compose**：
```yaml
command: python /code/app_server.py
```

2. **或使用原始启动命令**：
```yaml
command: bash -c "python /code/app_local.py"
```

### 📝 日志分析

#### 成功启动的标志：
```
HeyGem AI Server is ready. Listening on 0.0.0.0:8383
```

#### 需要关注的错误：
- `ModuleNotFoundError`: 依赖缺失
- `Permission denied`: 权限问题
- `Address already in use`: 端口占用
- `No such file or directory`: 文件路径问题

### 🔧 高级故障排除

#### 检查Docker环境

```bash
# 检查Docker版本
docker --version
docker-compose --version

# 检查系统资源
docker system df
docker system prune  # 清理不用的资源
```

#### 重置容器

```bash
# 完全重置
docker-compose -f deploy/docker-compose-lite.yml down -v
docker system prune -a
docker-compose -f deploy/docker-compose-lite.yml up -d
```

## 总结

通过这些改进，Docker容器启动应该更加可靠：

- ✅ 自动升级pip
- ✅ 智能安装和检测gunicorn
- ✅ 多种启动方式回退
- ✅ 详细的启动日志
- ✅ 健壮的错误处理

如果问题仍然存在，请查看容器日志获取更多诊断信息。 