# 配置文档目录

本目录包含项目复现所需的所有配置文件和文档。

## 📁 文件说明

| 文件名 | 说明 | 必需 |
|--------|------|------|
| `movie_db.sql` | MySQL 数据库结构和初始数据（~8000条电影数据） | ✅ 必需 |
| `requirements.txt` | Python 依赖列表（FastAPI + Flask） | ✅ 必需 |
| `.env.example` | 环境变量配置模板 | ✅ 必需 |
| `CONFIG.md` | **详细配置文档**（推荐先阅读） | ✅ 必需 |
| `docker-compose.yml` | Docker Compose 一键部署配置 | ⭕ 可选 |
| `start_all.bat` | Windows 一键启动脚本 | ⭕ 可选 |
| `start_all.sh` | macOS 一键启动脚本 | ⭕ 可选 |

## 🚀 快速开始

### 方式一：手动部署（推荐新手）

1. 阅读 [CONFIG.md](./CONFIG.md) 了解详细配置步骤
2. 导入数据库：`mysql -u root -p < movie_db.sql`
3. 安装依赖：`pip install -r requirements.txt`
4. 配置环境变量：复制 `.env.example` 到 `../fastapi/.env` 并填写实际配置
5. 启动服务（需要三个终端窗口）

### 方式二：Docker 部署（推荐有经验者）

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 2. 一键启动
docker-compose up -d

# 3. 访问服务
# http://localhost:3000/demo.html
```

### 方式三：一键启动脚本

**Windows:**
```bash
双击 start_all.bat
```

**macOS:**
```bash
chmod +x start_all.sh
./start_all.sh
```

## 📖 详细文档

请阅读 [CONFIG.md](./CONFIG.md) 获取完整的配置说明，包括：

- 环境要求
- 数据库配置
- Python/Node.js 环境配置
- 环境变量配置
- Docker 配置
- 机器学习模型准备
- 启动服务
- 常见问题解答

## 🔗 相关链接

- [项目 README](../README.md)
- [更新日志](../更新日志/)
- [API 文档](http://localhost:8000/docs) - 启动 FastAPI 后访问

## ⚠️ 注意事项

1. **数据库**: 必须先导入 `movie_db.sql` 才能启动服务
2. **API Key**: 必须在 `.env` 文件中配置 `API_KEY`（DeepSeek 或 OpenAI）
3. **端口**: 确保端口 3000/5000/8000/3306 未被占用
4. **Python 版本**: 需要 Python 3.10+
5. **Node.js 版本**: 需要 Node.js 16+

## 🆘 遇到问题？

1. 查看 [CONFIG.md](./CONFIG.md) 中的"常见问题"章节
2. 检查环境变量配置是否正确
3. 确认所有依赖已正确安装
4. 查看服务日志排查错误

---

**祝您使用愉快！如有问题，请参考详细配置文档 [CONFIG.md](./CONFIG.md)**
