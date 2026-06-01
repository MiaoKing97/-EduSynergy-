杏坛智析・人机协同学情共创平台 - 项目完整部署文档
1. 项目架构概述
本项目是一个前后端分离的全栈式“AI+教育”智能教研系统：
• 前端：基于 Vue 3 + Vite 构建，使用 ECharts、Mermaid 等进行数据可视化，TailwindCSS (可选) 搭配原生 CSS 进行排版，结合 Vue Router 和 Pinia 状态管理。
• 后端：基于 Python FastAPI 框架构建异步高性能接口，集成 ChromaDB 进行本地向量检索（RAG），接入火山豆包、DeepSeek 等大模型接口，并打通了飞书多维表格（Bitable）API。
2. 运行环境依赖
• Node.js：v16.18.0 或以上版本（推荐 v18+）
• Python：3.9 或以上版本（推荐 3.10+）
• 包管理工具：npm (或 yarn/pnpm) 以及 pip
3.一键部署方案（推荐）
该项目底层目录下有start_mac.sh、start_windows.bat，两个一键部署工具，设备安装python后即可使用对应的一键部署工具进行安装。
4. 后端部署指南 (Backend)
3.1 创建虚拟环境
在后端目录下执行以下命令创建并激活虚拟环境：
cd backend
python -m venv venv
# Windows激活:
venv\Scripts\activate
# macOS/Linux激活:
source venv/bin/activate
3.2 安装依赖
请确保虚拟环境已激活，然后安装 requirements.txt 中的依赖：
pip install -r requirements.txt
3.3 环境配置 (环境变量)
系统运行可能需要配置环境变量。可以在 backend 根目录下创建 `.env` 文件，配置如下参数（如系统支持在前端直接传入可忽略此步，通常建议配在后端以做全局备用）：
FEISHU_APP_ID=你的飞书应用ID
FEISHU_APP_SECRET=你的飞书应用密钥
OPENAI_API_KEY=你的大模型SK
CHROMA_PERSIST_DIRECTORY=./chroma_data
3.4 启动后端服务
执行以下命令启动 FastAPI 服务，默认将运行在 http://localhost:8000
uvicorn main:app --reload --host 0.0.0.0 --port 8000
5. 前端部署指南 (Frontend)
4.1 安装依赖包
新开一个终端窗口，进入 frontend 目录并安装依赖：
cd frontend
npm install
4.2 配置接口地址
如果您的后端未运行在 localhost:8000，请修改前端项目中（如 axios.post、store.js、或者 vite.config.js 的 proxy 中）对应的 `API_BASE_URL`。
4.3 启动开发服务器
npm run dev
命令执行后，在浏览器访问控制台输出的本地地址（如 http://localhost:5173）即可进入系统。
4.4 生产环境打包 (可选)
部署到服务器时，需进行静态文件构建：
npm run build
打包生成的 dist 目录下的文件可通过 Nginx 或其它 Web 服务器进行托管。
5. 系统初始化准备工作
项目前后端均启动成功后，即可进入系统：
1.登录：使用任意角色（如教师）登录。
默认管理员账号密码：账号：admin，密码：123
2. 飞书凭证设置：在系统右侧展开【开发者参数底盘】，填入您在“飞书开放平台”创建的自建应用的 App ID 和 App Secret。请务必确保您的飞书应用已开通【多维表格读写权限】。
3. 大模型凭证：在面板中填入大语言模型的 API Key，并在下拉框选择对应的模型名称（如 deepseek-chat 或 doubao 模型）。
4. 智能建表：在【老师模板设置】界面，点击“一键生成全新表格”，系统将自动在您的飞书账号下创建标准批改数据底座，即可开始闭环流程。
