# 常见问题

本文档汇总了项目部署和使用过程中可能遇到的问题及解决方案。

## 目录

- [数据库问题](#数据库问题)
- [LLM API 问题](#llm-api-问题)
- [Docker 问题](#docker-问题)
- [模型加载问题](#模型加载问题)
- [端口占用问题](#端口占用问题)
- [前端连接问题](#前端连接问题)
- [依赖安装问题](#依赖安装问题)

---

## 数据库问题

### Q1: 数据库连接失败

**错误信息:**
```
pymysql.err.OperationalError: (1045, "Access denied for user 'root'@'localhost'")
```

**解决方案:**
1. 检查 `.env` 文件中的 `DB_USER` 和 `DB_PASS` 是否正确
2. 确认 MySQL 服务已启动
3. 尝试在命令行手动连接: `mysql -u root -p`

### Q2: 数据库表不存在

**错误信息:**
```
pymysql.err.ProgrammingError: (1146, "Table 'movie_db.users' doesn't exist")
```

**解决方案:**
```bash
# 重新导入数据库
mysql -u root -p < movie_db.sql
```

---

## LLM API 问题

### Q3: LLM API 调用失败

**错误信息:**
```
openai.AuthenticationError: Incorrect API key provided
```

**解决方案:**
1. 检查 `.env` 文件中的 `API_KEY` 是否正确
2. 确认 API Key 有效且有余额
3. 检查 `API_BASE` 地址是否正确

### Q4: API 请求超时

**错误信息:**
```
openai.APITimeoutError: Request timed out
```

**解决方案:**
1. 检查网络连接
2. 确认 API 服务可用
3. 检查防火墙设置

---

## Docker 问题

### Q5: Docker 容器启动失败

**错误信息:**
```
docker.errors.ImageNotFound: pyecharts-sandbox
```

**解决方案:**
```bash
# 重新构建镜像
cd fastapi
docker build -t pyecharts-sandbox .
```

### Q6: Docker 服务未启动

**错误信息:**
```
docker.errors.DockerException: Error while fetching server API version
```

**解决方案:**
1. 确认 Docker Desktop 已启动
2. 检查 Docker 服务状态
3. 重启 Docker Desktop

---

## 模型加载问题

### Q7: 模型加载失败

**错误信息:**
```
FileNotFoundError: random_forest_model.pkl
```

**解决方案:**
1. 确认模型文件存在于 `Flask/` 目录
2. 检查文件名是否正确
3. 如果文件丢失，需要重新训练模型

---

## 端口占用问题

### Q8: 端口被占用

**错误信息:**
```
OSError: [Errno 98] Address already in use: ('0.0.0.0', 3000)
```

**解决方案 - Windows:**
```bash
# 查找占用端口的进程
netstat -ano | findstr :3000
# 结束进程（PID 为上面查到的进程ID）
taskkill /PID <PID> /F
```

**解决方案 - macOS/Linux:**
```bash
# 查找并结束进程
lsof -i :3000
kill -9 <PID>
```

---

## 前端连接问题

### Q9: 前端页面无法访问后端 API

**错误信息:**
```
CORS policy: No 'Access-Control-Allow-Origin' header
```

**解决方案:**
1. 确认三个服务都已启动
2. 检查服务端口是否正确（3000/5000/8000）
3. 清除浏览器缓存后重试

---

## 依赖安装问题

### Q10: Python 依赖安装失败

**错误信息:**
```
error: Microsoft Visual C++ 14.0 is required
```

**解决方案:**
1. 安装 [Microsoft Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
2. 或使用预编译的 wheel 文件:
   ```bash
   pip install --only-binary :all: <package_name>
   ```

### Q11: Node.js 依赖安装失败

**错误信息:**
```
npm ERR! code ENOENT
npm ERR! syscall open
```

**解决方案:**
```bash
# 清除缓存后重新安装
npm cache clean --force
rm -rf node_modules
npm install
```

---

## 其他问题

### Q12: agent-browser 命令未找到

**错误信息:**
```
'agent-browser' 不是内部或外部命令
```

**解决方案:**
```bash
# 全局安装
npm install -g agent-browser

# 验证安装
agent-browser --version
```

### Q13: 中文显示乱码

**解决方案:**
1. 确保数据库使用 UTF-8 编码
2. 检查前端页面 charset 设置
3. 确认 MySQL 连接字符集为 utf8mb4

---

## 获取帮助

如果以上解决方案无法解决您的问题，请：

1. 查看 [项目 README](../README.md)
2. 查看 [更新日志](../更新日志/)
3. 检查 FastAPI API 文档：http://localhost:8000/docs
4. 查看服务日志输出
