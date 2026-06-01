# 杏坛智析・人机协同学情共创平台 - 项目完整部署文档
## 1. 项目架构概述
本项目是一个前后端分离的全栈式“AI+教育”智能教研系统：
- 前端：基于 Vue 3 + Vite 构建，使用 ECharts、Mermaid 等进行数据可视化，TailwindCSS (可选) 搭配原生 CSS 进行排版，结合 Vue Router 和 Pinia 状态管理。
- 后端：基于 Python FastAPI 框架构建异步高性能接口，集成 ChromaDB 进行本地向量检索（RAG），接入火山豆包、DeepSeek 等大模型接口，并打通了飞书多维表格（Bitable）API。

## 2. 运行环境依赖
- Node.js：v16.18.0 或以上版本（推荐 v18+）
- Python：3.9 或以上版本（推荐 3.10+）
- 包管理工具：npm (或 yarn/pnpm) 以及 pip

## 3. 一键部署方案（推荐）
该项目底层目录下有 `start_mac.sh`、`start_windows.bat` 两个一键部署工具，设备安装Python后即可使用对应系统的脚本完成一键安装与启动。

## 4. 后端部署指南 (Backend)
### 4.1 创建虚拟环境
在后端目录下执行以下命令创建并激活虚拟环境：
```powershell
cd backend
python -m venv venv
```
Windows 激活虚拟环境：
```powershell
venv\Scripts\activate
```
macOS / Linux 激活虚拟环境：
```bash
source venv/bin/activate
```

### 4.2 安装依赖
确保虚拟环境已激活，执行命令安装 `requirements.txt` 内全部依赖：
```powershell
pip install -r requirements.txt
```

### 4.3 环境配置 (环境变量)
系统运行需配置核心环境变量，在 `backend` 根目录新建 `.env` 文件，写入如下配置：
```env
FEISHU_APP_ID=你的飞书应用ID
FEISHU_APP_SECRET=你的飞书应用密钥
OPENAI_API_KEY=你的大模型SK
CHROMA_PERSIST_DIRECTORY=./chroma_data
```
> 说明：若系统支持前端直接传入凭证可忽略此配置，建议后端配置作为全局备用方案。

### 4.4 启动后端服务
执行命令启动 FastAPI 开发服务，服务默认地址：`http://localhost:8000`
```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 5. 前端部署指南 (Frontend)
### 5.1 安装依赖包
新开终端窗口，进入 frontend 目录安装项目依赖：
```powershell
cd frontend
npm install
```

### 5.2 配置接口地址
若后端服务未运行在 `localhost:8000`，需要修改前端项目内接口基础地址：
修改位置可选：axios 请求封装文件、store 状态文件、`vite.config.js` 代理配置中的 `API_BASE_URL`。

### 5.3 启动开发服务器
```powershell
npm run dev
```
执行成功后，复制控制台输出本地地址（示例：`http://localhost:5173`）在浏览器打开，进入系统。

### 5.4 生产环境打包 (可选)
服务器线上部署时执行打包命令，生成静态资源：
```powershell
npm run build
```
打包完成后根目录生成 `dist` 文件夹，内部静态文件可通过 Nginx、Apache 等 Web 服务器托管。

## 6. 系统初始化准备工作
前后端服务全部启动成功后，执行以下初始化步骤：
1. **登录系统**
支持教师、管理员等多角色登录；
默认管理员账号密码：账号 `admin`，密码 `123`。

2. **配置飞书凭证**
系统右侧展开【开发者参数底盘】，填入飞书开放平台自建应用的 App ID、App Secret；
前置要求：飞书应用已开通**多维表格读写权限**。

3. **配置大模型凭证**
在开发者参数面板填写大语言模型 API Key，下拉框选择对应模型（deepseek-chat / doubao 火山豆包）。

4. **一键初始化数据表**
进入【老师模板设置】页面，点击「一键生成全新表格」，系统会自动在你的飞书账号下创建标准化批改数据底座，完成后即可启动完整教研业务流程。