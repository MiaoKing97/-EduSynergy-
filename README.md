# 杏坛智析・人机协同学情共创平台 - 项目完整部署文档
## 1. 项目架构概述
本项目是一个前后端分离的全栈式"AI+教育"智能教研系统：
- 前端：基于 Vue 3 + Vite + Vue Router 构建，使用 ECharts、Mermaid 等进行数据可视化，TailwindCSS 搭配原生 CSS 排版，Pinia-like 全局状态管理。
- 后端：基于 Python FastAPI 异步高性能框架，SQLite 持久化用户认证，ChromaDB 本地向量检索（RAG），接入火山豆包、DeepSeek 等大模型接口，飞书多维表格（Bitable）API 深度集成，Playwright 无头浏览器截图。

## 2. 运行环境依赖
- Node.js：v16.18.0 或以上版本（推荐 v18+）
- Python：3.9 或以上版本（推荐 3.10+）
- 包管理工具：npm 以及 pip

## 3. 一键部署方案（推荐）
该项目底层目录下有 `start_mac.sh`、`start_windows.bat` 两个一键部署工具，安装 Python 后即可使用对应系统的脚本完成一键安装与启动。

## 4. 后端部署指南 (Backend)
### 4.1 安装依赖
在 backend 目录下执行：
```bash
pip install -r requirements.txt
playwright install chromium
```

### 4.2 环境配置 (环境变量，可选)
在 `backend` 根目录新建 `.env` 文件：
```env
FEISHU_APP_ID=你的飞书应用ID
FEISHU_APP_SECRET=你的飞书应用密钥
OPENAI_API_KEY=你的大模型SK
CHROMA_PERSIST_DIRECTORY=./chroma_data
JWT_SECRET_KEY=你的JWT密钥（生产环境必须修改）
```

### 4.3 启动后端服务
默认地址：`http://localhost:8000`
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 5. 前端部署指南 (Frontend)
### 5.1 安装依赖
```bash
cd frontend
npm install
```

### 5.2 启动开发服务器
```bash
npm run dev
```
默认：`http://localhost:5173`（Vite 自动代理 `/api` 到后端 8000 端口）

### 5.3 生产打包
```bash
npm run build
```

## 6. 系统初始化
1. **登录系统** — 默认管理员：账号 `admin`，密码 `123`（首次启动后端会自动在 SQLite 中创建默认账号）。
2. **配置飞书凭证** — 右侧展开【开发者参数底盘】，填入飞书 App ID、App Secret（需开通多维表格读写权限）。
3. **配置大模型凭证** — 填写 API Key，下拉选择模型（deepseek-chat / doubao）。
4. **一键初始化数据表** — 进入【老师模板设置】，点击「一键生成全新表格」。

## 7. 优化说明 (v2 更新)
- 后端全面异步化（httpx 替代 requests，Playwright 持久化浏览器复用）
- SQLite 持久化用户认证（JWT token），替换纯前端存储
- CORS 限制为 localhost:5173
- 代码去重：Feishu table list 查询提取为共享函数
- 前端使用 Vue Router，配置面板保存按钮真实调用后端
