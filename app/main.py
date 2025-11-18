import os
import uuid
import shutil
import markdown
from pathlib import Path
from typing import List
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Request, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader

from . import analyzer

BASE_DIR = Path(__file__).resolve().parents[1]
UPLOAD_DIR = BASE_DIR / "uploads"
SITE_DIR = BASE_DIR / "site"
# templates are located next to this module: app/templates
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(SITE_DIR, exist_ok=True)
# don't create templates dir at runtime; templates are part of the source tree

app = FastAPI(title="MPNN Blog Scaffold")
env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))

app.mount("/site", StaticFiles(directory=str(SITE_DIR)), name="site")


def save_upload_file(upload_file: UploadFile, dest: Path) -> Path:
    with open(dest, "wb") as f:
        shutil.copyfileobj(upload_file.file, f)
    return dest


def parse_file(path: Path) -> str:
    name = path.name.lower()
    if name.endswith(".pdf"):
        try:
            import pdfplumber
            text_pages = []
            with pdfplumber.open(path) as pdf:
                for p in pdf.pages:
                    txt = p.extract_text()
                    if txt:
                        text_pages.append(txt)
            return "\n\n".join(text_pages)
        except Exception:
            return ""
    elif name.endswith(".docx"):
        try:
            import docx
            doc = docx.Document(path)
            return "\n\n".join(p.text for p in doc.paragraphs if p.text)
        except Exception:
            return ""
    elif name.endswith(".pptx"):
        try:
            from pptx import Presentation
            prs = Presentation(path)
            texts = []
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text:
                        texts.append(shape.text)
            return "\n\n".join(texts)
        except Exception:
            return ""
    else:
        try:
            return path.read_text(encoding="utf-8")
        except Exception:
            return ""


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    # List generated posts with metadata (category, date, title, summary, tags)
    posts = []
    categories_data = {}  # {category: [posts]}
    for f in sorted(SITE_DIR.glob("*.json"), reverse=True):
        try:
            import json
            with open(f, "r", encoding="utf-8") as mf:
                data = json.load(mf)
            cat = data.get("category", "未分类")
            post_info = {
                "name": f.stem,
                "title": data.get("title", f.stem),
                "path": f"/site/{f.stem}.html",
                "category": cat,
                "date": data.get("date", ""),
                "tags": data.get("tags", []),
                "summary": data.get("summary", "")
            }
            posts.append(post_info)
            if cat not in categories_data:
                categories_data[cat] = []
            categories_data[cat].append(post_info)
        except Exception:
            # Fallback if JSON missing
            html_file = SITE_DIR / f"{f.stem}.html"
            if html_file.exists():
                posts.append({"name": f.stem, "title": f.stem, "path": f"/site/{f.stem}.html", "category": "未分类", "date": "", "tags": [], "summary": ""})
    tpl = env.get_template("index.html")
    return tpl.render(posts=posts, categories_data=categories_data)


@app.post("/upload")
async def upload(files: List[UploadFile] = File(...), category: str = Form("未分类")):
    """Upload multiple files (folder upload). Parse all and generate a single structured blog post."""
    combined_texts = []
    file_ids = []
    
    for file in files:
        ext = Path(file.filename).suffix
        file_id = uuid.uuid4().hex
        dest = UPLOAD_DIR / f"{file_id}{ext}"
        save_upload_file(file, dest)
        file_ids.append(file_id)
        
        # parse each file
        text = parse_file(dest)
        if text:
            combined_texts.append(f"### 文件: {file.filename}\n{text}")
    
    # combine all texts
    combined = "\n\n---\n\n".join(combined_texts) if combined_texts else "无内容"
    
    # analyze with DeepSeek (expects structured Chinese blog)
    analysis = analyzer.call_deepseek_blog(combined, category=category)
    
    # render to HTML - convert markdown to HTML
    slug = analysis.get("slug") or file_ids[0] if file_ids else uuid.uuid4().hex[:10]
    date = datetime.now().strftime("%Y-%m-%d")
    
    content_md = analysis.get("content", "")
    print(f"[DEBUG] Content MD length: {len(content_md)}, first 100 chars: {content_md[:100]}")
    content_html = markdown.markdown(
        content_md,
        extensions=['fenced_code', 'tables', 'nl2br']
    )
    print(f"[DEBUG] Content HTML length: {len(content_html)}, first 200 chars: {content_html[:200]}")
    
    tpl = env.get_template("post.html")
    html = tpl.render(
        title=analysis.get("title", "未命名"),
        summary=analysis.get("summary", ""),
        tags=analysis.get("tags", []),
        content=content_html,
        category=analysis.get("category", category),
        date=date
    )
    out_path = SITE_DIR / f"{slug}.html"
    out_path.write_text(html, encoding="utf-8")
    
    # save JSON metadata
    try:
        import json
        meta_path = SITE_DIR / f"{slug}.json"
        with open(meta_path, "w", encoding="utf-8") as mf:
            json.dump({
                "title": analysis.get("title", "未命名"),
                "summary": analysis.get("summary", ""),
                "tags": analysis.get("tags", []),
                "content": analysis.get("content", ""),
                "category": analysis.get("category", category),
                "date": date,
                "slug": slug,
            }, mf, ensure_ascii=False, indent=2)
    except Exception:
        pass
    
    return JSONResponse({"ids": file_ids, "url": f"/site/{slug}.html", "slug": slug})


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/admin", response_class=HTMLResponse)
async def admin(request: Request):
    posts = []
    for f in sorted(SITE_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            import json
            with open(f, "r", encoding="utf-8") as mf:
                data = json.load(mf)
            posts.append({
                "name": data.get("title") or f.stem,
                "title": data.get("title") or f.stem,
                "slug": data.get("slug") or f.stem,
                "category": data.get("category", "未分类"),
                "date": data.get("date", "未知")
            })
        except Exception:
            posts.append({
                "name": f.stem,
                "title": f.stem,
                "slug": f.stem,
                "category": "未分类",
                "date": "未知"
            })
    tpl = env.get_template("admin.html")
    openwebui = os.getenv("OPENWEBUI_URL", "http://localhost:3000")
    return tpl.render(posts=posts, openwebui=openwebui)


@app.get("/post/{slug}")
async def get_post(slug: str):
    meta_path = SITE_DIR / f"{slug}.json"
    if not meta_path.exists():
        return JSONResponse({"error": "not found"}, status_code=404)
    import json
    with open(meta_path, "r", encoding="utf-8") as mf:
        data = json.load(mf)
    return JSONResponse(data)


@app.post("/review/{slug}")
async def review_post(slug: str, request: Request):
    meta_path = SITE_DIR / f"{slug}.json"
    if not meta_path.exists():
        return JSONResponse({"error": "not found"}, status_code=404)
    payload = await request.json()
    title = payload.get("title")
    summary = payload.get("summary")
    content = payload.get("content")
    tags = payload.get("tags") or []
    # update meta json
    try:
        import json
        # Read existing metadata to preserve date and category
        with open(meta_path, "r", encoding="utf-8") as mf:
            old_data = json.load(mf)
        
        # Update with new values
        with open(meta_path, "w", encoding="utf-8") as mf:
            json.dump({
                "title": title,
                "summary": summary,
                "tags": tags,
                "content": content,
                "slug": slug,
                "date": old_data.get("date", datetime.now().strftime("%Y-%m-%d")),
                "category": old_data.get("category", "未分类")
            }, mf, ensure_ascii=False, indent=2)
        
        # re-render html with markdown conversion
        content_html = markdown.markdown(
            content,
            extensions=['fenced_code', 'tables', 'nl2br']
        )
        tpl = env.get_template("post.html")
        html = tpl.render(
            title=title,
            summary=summary,
            tags=tags,
            content=content_html,
            date=old_data.get("date", datetime.now().strftime("%Y-%m-%d")),
            category=old_data.get("category", "未分类")
        )
        out_path = SITE_DIR / f"{slug}.html"
        out_path.write_text(html, encoding="utf-8")
        return JSONResponse({"ok": True, "url": f"/site/{slug}.html"})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/import")
async def import_file(request: Request):
    """Import a file already present on the server under the `uploads/` directory.
    POST JSON {"filename": "your.pdf"}
    This helps avoid HTTP upload size limits imposed by some proxies.
    """
    payload = await request.json()
    filename = payload.get("filename")
    if not filename:
        return JSONResponse({"error": "filename required"}, status_code=400)

    # Sanitize path: only allow files inside UPLOAD_DIR
    candidate = UPLOAD_DIR / Path(filename).name
    if not candidate.exists():
        return JSONResponse({"error": "file not found on server"}, status_code=404)

    # parse
    text = parse_file(candidate)
    analysis = analyzer.call_deepseek(text)

    slug = analysis.get("slug") or Path(filename).stem
    
    # Convert markdown to HTML
    content_html = markdown.markdown(
        analysis.get("content", ""),
        extensions=['fenced_code', 'tables', 'nl2br']
    )
    
    tpl = env.get_template("post.html")
    html = tpl.render(
        title=analysis.get("title", filename),
        summary=analysis.get("summary", ""),
        tags=analysis.get("tags", []),
        content=content_html
    )
    out_path = SITE_DIR / f"{slug}.html"
    out_path.write_text(html, encoding="utf-8")

    try:
        import json
        meta_path = SITE_DIR / f"{slug}.json"
        with open(meta_path, "w", encoding="utf-8") as mf:
            json.dump({"title": analysis.get("title", filename), "summary": analysis.get("summary",""), "tags": analysis.get("tags",[]), "content": analysis.get("content",""), "slug": slug}, mf, ensure_ascii=False, indent=2)
    except Exception:
        pass

    return JSONResponse({"ok": True, "url": f"/site/{slug}.html", "slug": slug})


@app.delete("/post/{slug}")
async def delete_post(slug: str):
    """Delete a post (both HTML and JSON files)."""
    html_path = SITE_DIR / f"{slug}.html"
    json_path = SITE_DIR / f"{slug}.json"
    
    deleted = []
    if html_path.exists():
        html_path.unlink()
        deleted.append("html")
    if json_path.exists():
        json_path.unlink()
        deleted.append("json")
    
    if deleted:
        return JSONResponse({"ok": True, "deleted": deleted})
    else:
        return JSONResponse({"error": "not found"}, status_code=404)


@app.post("/api/ai-rewrite")
async def ai_rewrite(request: Request):
    """Use AI to improve/rewrite existing blog content."""
    payload = await request.json()
    title = payload.get("title", "")
    summary = payload.get("summary", "")
    content = payload.get("content", "")
    tags = payload.get("tags", "")
    
    # Combine current content and ask AI to improve it
    combined = f"标题: {title}\n\n摘要: {summary}\n\n正文:\n{content}\n\n标签: {tags}"
    
    try:
        # Use the blog generator with rewrite instruction
        result = analyzer.call_deepseek_blog(combined, category="优化版")
        return JSONResponse({
            "title": result.get("title") or title,
            "summary": result.get("summary") or summary,
            "content": result.get("content") or content,
            "tags": result.get("tags") or []
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


    return JSONResponse({"ok": True, "url": f"/site/{slug}.html"})
