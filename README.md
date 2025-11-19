# yinlab_blog

AI 驱动的学术博客生成系统，支持批量上传文档（PDF、Word、PPT），通过 DeepSeek AI 自动分析并生成结构化的博客文章，包含图片提取、多文件分类整合等高级特性。

## ✨ 核心特性

- 🚀 **异步后台处理**：大文件处理不阻塞，实时轮询任务状态
- 📚 **多文件智能分类**：自动识别论文、PPT、讨论纪要并分别处理
- 🖼️ **富媒体支持**：自动提取 PDF 图片、将 PPT 转换为高清截图
- 🎨 **精美的前端界面**：参考 laiyz.cn 设计风格，响应式布局
- 🔄 **FTP 批量导入**：支持通过 FTP 上传到时间戳文件夹
- ✏️ **强大的管理后台**：在线编辑、AI 优化、OpenWebUI 集成
- 🐳 **Docker 一键部署**：包含完整的容器化配置

## 🚀 快速开始

### 方式一：Docker（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/xryller/yinlab_blog.git
cd yinlab_blog

# 2. 配置环境变量（可选）
cp .env.example .env
# 编辑 .env 填入 DeepSeek API 密钥

# 3. 启动服务
docker compose up -d --build

# 4. 访问服务
# 首页: http://localhost:8000
# 管理后台: http://localhost:8000/admin
```

### 方式二：本地虚拟环境

```bash
# 1. 创建并激活虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 安装系统依赖（Ubuntu/Debian）
sudo apt-get update
sudo apt-get install -y poppler-utils libreoffice

# 4. 配置环境变量
export DEEPSEEK_API_KEY="your_api_key"
export DEEPSEEK_API_URL="https://api.deepseek.com"

# 5. 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📖 使用指南

### 1. 上传文件

访问 `http://localhost:8000/admin`，使用批量上传功能：

- 选择分类（如：蛋白质设计、机器学习等）
- 支持多文件选择（PDF、DOCX、PPTX）
- 自动创建时间戳文件夹（格式：`20251119_143000`）
- 支持大文件（自动分批上传，绕过 Nginx 限制）

### 2. 生成博文

在"已上传文件夹"区域：

1. 点击"生成博文"按钮
2. 任务在后台异步处理（不会超时）
3. 页面自动轮询显示实时状态：
   - ⏳ **待处理**：文件已上传，等待生成
   - ⚙️ **生成中**：AI 正在分析处理
   - ✅ **已完成**：点击"查看博文"按钮预览
   - ❌ **失败**：显示错误信息，可重新生成

### 3. 智能内容识别

系统会自动识别并分类处理：

- **📄 文献原文**：PDF/DOCX 论文，生成纯文字概述
- **🎯 PPT 分享**：PPTX 文件，转换每页为高清图片并配 AI 解析
- **💬 讨论纪要**：包含"讨论"或"纪要"的文档，保留图片和格式

### 4. FTP 批量导入

支持通过 FTP 直接上传文件到服务器：

```bash
# 连接到服务器后，上传到指定格式的文件夹
# 文件夹格式：YYYYMMDD_HHMMSS（如：20251119_143000）
/app/uploads/20251119_143000/
  ├── paper.pdf
  ├── slides.pptx
  └── discussion_notes.docx
```

管理页面会自动扫描并显示这些文件夹，无需 Web 界面上传。

### 5. 编辑与优化

在管理后台可以：

- ✏️ **在线编辑**：修改标题、摘要、正文（支持 Markdown）
- ✨ **AI 优化**：一键让 AI 改进文章质量
- 🚀 **OpenWebUI 集成**：在 iframe 中使用 OpenWebUI 编辑器
- 🗑️ **删除文章**：不需要的文章可直接删除

## 🔧 配置说明

### 环境变量

创建 `.env` 文件或设置以下环境变量：

```bash
# DeepSeek API 配置（必需）
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_API_URL=https://api.deepseek.com

# OpenWebUI 集成（可选）
OPENWEBUI_URL=http://localhost:3000
```

**安全提示**：`.env` 文件已在 `.gitignore` 中，不会被提交到代码库。

### 一键配置脚本

运行 `./setup.sh` 进行交互式配置：

```bash
chmod +x setup.sh
./setup.sh
```

脚本会引导您：
1. 填写 DeepSeek API 密钥和 URL
2. 配置 OpenWebUI 地址（可选）
3. 自动生成 `.env` 文件
4. 询问是否立即启动 Docker 服务

## 🏗️ 技术架构

### 后端技术栈

- **FastAPI**：高性能异步 Web 框架
- **BackgroundTasks**：异步任务处理，防止请求超时
- **Jinja2**：模板引擎，渲染 HTML 页面
- **Markdown**：支持 Markdown 格式内容
- **Python-Multipart**：处理文件上传
- **OpenAI SDK**：调用 DeepSeek API

### 文档处理

- **pdfplumber**：PDF 文本提取
- **python-docx**：Word 文档解析
- **python-pptx**：PPT 文本提取
- **poppler-utils** (`pdftoppm`)：PDF 转图片
- **LibreOffice** (`soffice`)：PPT 转高清截图

### 前端技术

- **Vanilla JavaScript**：原生 JS，无依赖
- **XHR + Polling**：实时状态更新
- **Responsive Design**：自适应布局
- **PostMessage API**：OpenWebUI 集成

### 部署方式

- **Docker Compose**：容器化部署
- **Nginx**（可选）：反向代理，处理静态文件
- **Volume Mounts**：数据持久化

## 📁 项目结构

```
yinlab_blog/
├── app/
│   ├── main.py              # FastAPI 主应用（异步架构）
│   ├── analyzer.py          # DeepSeek AI 分析器
│   └── templates/           # Jinja2 模板
│       ├── index.html       # 首页（博客列表）
│       ├── admin.html       # 管理后台（支持轮询）
│       └── post.html        # 文章页面模板
├── uploads/                 # 上传文件存储（按时间戳分类）
│   └── 20251119_143000/
│       ├── _metadata.json   # 文件夹元数据（含任务状态）
│       └── *.pdf/*.pptx     # 上传的文件
├── site/                    # 生成的静态博客
│   ├── *.html               # 文章页面
│   ├── *.json               # 文章元数据
│   └── images/              # 提取的图片
├── docker-compose.yml       # Docker 编排配置
├── Dockerfile               # 容器镜像定义
├── requirements.txt         # Python 依赖
└── README.md               # 本文档
```

## 🔄 工作流程

### 异步生成流程

```
用户点击"生成博文"
    ↓
后端立即返回 202 Accepted（任务已接收）
    ↓
任务加入后台队列，状态标记为 "running"
    ↓
前端每 3 秒轮询 /api/generation-status/{timestamp}
    ↓
后台处理：
  1. 解析所有文件（PDF/DOCX/PPTX）
  2. 提取图片（PDF）或截图（PPT）
  3. 调用 DeepSeek AI 分析
  4. 生成结构化 HTML
    ↓
处理完成后，更新状态为 "completed" 或 "failed"
    ↓
前端检测到完成，显示"查看博文"链接
```

### 文件分类逻辑

系统根据文件名和扩展名自动分类：

| 文件类型 | 识别规则 | 处理方式 |
|---------|---------|---------|
| 📄 论文 | `.pdf`、`.docx`（不含 "slide"/"ppt"） | 纯文字概述，无图片 |
| 🎯 PPT | `.pptx` 或文件名含 "ppt"/"slide" | 每页转高清图片 + AI 解析 |
| 💬 讨论纪要 | 文件名含"讨论"/"纪要"/"note" | 保留图片，Markdown 渲染 |

## 🛠️ API 文档

### 上传文件

```http
POST /upload
Content-Type: multipart/form-data

files: File[]           # 多个文件
category: string        # 分类（可选）
timestamp: string       # 指定文件夹（可选）
```

### 生成博文（异步）

```http
POST /api/generate-blog/{timestamp}?category=分类名

返回: 202 Accepted
{
  "message": "博文生成任务已在后台开始",
  "timestamp": "20251119_143000"
}
```

### 查询任务状态

```http
GET /api/generation-status/{timestamp}

返回:
{
  "timestamp": "20251119_143000",
  "status": "running" | "completed" | "failed" | "pending",
  "error": "错误信息（如果失败）",
  "blog_slug": "abc123def456",
  "url": "/site/abc123def456.html"
}
```

### 获取上传文件夹列表

```http
GET /api/upload-folders

返回:
{
  "folders": [
    {
      "timestamp": "20251119_143000",
      "category": "蛋白质设计",
      "files_count": 3,
      "total_size_mb": 15.6,
      "upload_time": "2025-11-19T14:30:00",
      "processed": "completed",
      "blog_slug": "abc123def456"
    }
  ]
}
```

## 🐛 故障排查

### 问题：上传失败 "413 Request Entity Too Large"

**原因**：Nginx 限制了请求体大小。

**解决方案**：
1. 前端已实现分批上传（每批 4MB）
2. 如果仍然失败，在 Nginx 配置中增加：
   ```nginx
   client_max_body_size 50M;
   ```

### 问题：生成超时 "Failed to fetch"

**原因**：旧版本使用同步处理，大文件耗时过长。

**解决方案**：
- ✅ 已在最新版本中修复（使用异步后台任务）
- 确保使用最新代码并重新构建容器

### 问题：PPT 转图片失败

**原因**：缺少 LibreOffice 或 poppler-utils。

**解决方案**：
```bash
# Ubuntu/Debian
sudo apt-get install -y libreoffice poppler-utils

# Docker 已包含这些依赖
docker compose up -d --build
```

### 问题：AI 返回 Mock 数据

**原因**：未配置 DeepSeek API 密钥。

**解决方案**：
1. 确保 `.env` 文件包含 `DEEPSEEK_API_KEY`
2. Docker 需要重启以加载新环境变量：
   ```bash
   docker compose down
   docker compose up -d
   ```

## 🚧 开发计划

- [ ] 支持更多文件格式（Markdown、TXT、HTML）
- [ ] 添加用户认证和权限管理
- [ ] 实现全文搜索功能
- [ ] 支持自定义模板主题
- [ ] 添加文章版本历史
- [ ] WebSocket 实时推送任务状态

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

- GitHub: [@xryller](https://github.com/xryller)
- 仓库: [yinlab_blog](https://github.com/xryller/yinlab_blog)
