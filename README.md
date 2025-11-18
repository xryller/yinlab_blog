# hzau-MPNN_fr

这是一个最小示例仓库，演示如何把 Word/PDF 上传、用 AI（示例 mock DeepSeek）分析，并把内容生成静态博客页面。

快速开始（本地虚拟环境）

1. 创建并激活虚拟环境
```bash
python -m venv .venv
source .venv/bin/activate
```
2. 安装依赖并启动
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
3. 在浏览器打开 `http://localhost:8000/`，上传一个 `.pdf` 或 `.docx` 文件，服务会解析并在 `site/` 目录生成 HTML 页面。

使用 Docker
```bash
docker compose up --build
```

说明
- 解析：使用 `pdfplumber` 读取 PDF、`python-docx` 读取 docx。
- AI 分析：当前使用 `app/analyzer.py` 中的本地 mock `call_deepseek`，当你提供 DeepSeek API 时，我可以帮你替换为真正的 API 调用并安全管理密钥。

DeepSeek / 实际 AI 集成
- 为了安全不要把密钥写入代码或提交到仓库。两种常用方式：
	1. 在当前 shell 中导出环境变量（本地测试）：
```bash
export DEEPSEEK_API_KEY="<你的_api_key>"
export DEEPSEEK_API_URL="https://api.deepseek.com"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
	2. 使用 Docker：复制 `.env.example` 为 `.env`，把 `DEEPSEEK_API_KEY` 与 `DEEPSEEK_API_URL` 填入 `.env`（不要提交 `.env`），然后运行：
```bash
cp .env.example .env
# 编辑 .env 并填入你的密钥和 URL
docker compose up --build
```

在这份骨架中，`app/analyzer.py` 会在检测到 `DEEPSEEK_API_KEY` 与 `DEEPSEEK_API_URL` 时调用远程服务。返回字段会被正规化为 `title`, `summary`, `tags`, `content`, `slug`。如果没有设置这些环境变量或远程调用失败，代码会回退到本地 mock 分析器以保证功能可用。

示例：使用 OpenAI SDK 调用 DeepSeek（与你的环境变量配合）：
```python
import os
from openai import OpenAI

client = OpenAI(api_key=os.environ.get('DEEPSEEK_API_KEY'), base_url=os.environ.get('DEEPSEEK_API_URL','https://api.deepseek.com'))

response = client.chat.completions.create(
	model="deepseek-chat",
	messages=[
		{"role": "system", "content": "You are a helpful assistant"},
		{"role": "user", "content": "Summarize the following document: <your text>"},
	],
	stream=False
)

print(response.choices[0].message.content)
```

管理界面（OpenWebUI 集成）
- 访问 `http://localhost:8000/admin` 可以看到生成的帖子列表并打开一个内置编辑器。
- 管理页中每条记录有：`Edit`（内置文本编辑器）、`View`（打开生成页面）和 `Open in OpenWebUI`（在页面内打开 OpenWebUI 的 iframe 并尝试预填内容）。
- 管理页面实现了 iframe + postMessage 的预填与回写骨架：当点击 `Open in OpenWebUI` 时，页面会把当前文章（JSON）通过 `postMessage({type:'prefill', payload: <post JSON>})` 发送到 OpenWebUI 页面；若你的 OpenWebUI 前端能处理该消息并在编辑完成后通过 `postMessage({type:'export', payload: <post JSON>})` 将修改结果发回，则本服务会自动接收并保存（调用 `/review/{slug}`），并重新渲染页面。
- 如果你的 OpenWebUI 不支持 postMessage，管理页仍可使用内置编辑器手动修改并保存；或者你可以把 OpenWebUI 在新标签页打开，然后手工复制/粘贴内容回管理页保存。

便捷一键设置（推荐小白用户）
- 运行 `./setup.sh`：该脚本会引导你填写 `DEEPSEEK_API_KEY` / `DEEPSEEK_API_URL` / `OPENWEBUI_URL`，并在本地生成 `.env`（不会提交到仓库）。脚本会询问是否立即用 Docker 启动服务。

下一步建议
- 集成真实 DeepSeek API（需 API 文档/凭证）。
- 添加用户界面用于 OpenWebUI 集成和人工复核。
