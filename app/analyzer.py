import hashlib
import json
import os
import re
from typing import Dict


def _simple_tags(text, max_tags=6):
    words = re.findall(r"\w+", text.lower())
    stop = {"the", "and", "of", "in", "to", "a", "is", "for", "that"}
    freqs = {}
    for w in words:
        if len(w) < 3 or w in stop:
            continue
        freqs[w] = freqs.get(w, 0) + 1
    items = sorted(freqs.items(), key=lambda x: x[1], reverse=True)
    return [w for w, _ in items[:max_tags]]


def _mock_analysis(text: str) -> Dict:
    trimmed = (text or "").strip()
    title = trimmed.splitlines()[0][:80] if trimmed else "Untitled"
    summary = trimmed[:400] + ("..." if len(trimmed) > 400 else "")
    tags = _simple_tags(trimmed)
    slug = hashlib.sha1(trimmed.encode("utf-8") if trimmed else b"").hexdigest()[:10]
    return {"title": title, "summary": summary, "tags": tags, "content": trimmed, "slug": slug}


def call_deepseek(text: str) -> Dict:
    """
    Use DeepSeek via OpenAI-compatible SDK when `DEEPSEEK_API_KEY` is set.
    Falls back to `_mock_analysis` if SDK not available or call fails.

    The function will try to parse a JSON object returned by the model; if the model returns plain text,
    that text is used as `summary`/`content` and other fields are filled conservatively.
    """
    api_key = os.getenv("DEEPSEEK_API_KEY")
    api_url = os.getenv("DEEPSEEK_API_URL") or "https://api.deepseek.com"

    if api_key:
        try:
            # Use OpenAI-compatible client if available
            from openai import OpenAI

            client = OpenAI(api_key=api_key, base_url=api_url)

            # Ask the model to respond with a JSON object when possible to simplify parsing
            system_msg = {
                "role": "system",
                "content": (
                    "You are a document analysis assistant. Given the user's document text, "
                    "return a JSON object with keys: title, summary, tags (list), content, slug. "
                    "If you cannot produce JSON, return a plain useful summary."
                ),
            }
            user_msg = {"role": "user", "content": text or ""}

            resp = client.chat.completions.create(
                model="deepseek-chat",
                messages=[system_msg, user_msg],
                stream=False,
            )

            # Extract text
            raw = None
            try:
                raw = resp.choices[0].message.content
            except Exception:
                # fallback to top-level string representation
                raw = str(resp)

            # Try parse JSON from model output
            try:
                data = json.loads(raw)
                title = data.get("title") or (text or "").splitlines()[0][:80]
                summary = data.get("summary") or (text or "")[:400]
                tags = data.get("tags") or []
                content = data.get("content") or text or ""
                slug = data.get("slug") or hashlib.sha1((content or "").encode("utf-8")).hexdigest()[:10]
                return {"title": title, "summary": summary, "tags": tags, "content": content, "slug": slug}
            except Exception:
                # If not JSON, use the returned text as summary/content
                summary = raw or (text or "")[:400]
                content = text or ""
                slug = hashlib.sha1((content or "").encode("utf-8")).hexdigest()[:10]
                tags = _simple_tags(content)
                title = (content.splitlines()[0][:80]) if content else "Untitled"
                return {"title": title, "summary": summary, "tags": tags, "content": content, "slug": slug}

        except Exception:
            # If any error (import, network, parsing), fall back to local mock
            return _mock_analysis(text)

    # No API key provided — use local mock
    return _mock_analysis(text)


def call_deepseek_blog(combined_text: str, category: str = "未分类") -> Dict:
    """
    Generate a structured Chinese blog post from multiple files (PDF, PPT, Word).
    Returns: {title, summary, tags, content (formatted markdown/HTML), category, slug}
    """
    api_key = os.getenv("DEEPSEEK_API_KEY")
    api_url = os.getenv("DEEPSEEK_API_URL") or "https://api.deepseek.com"

    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url=api_url)

            system_msg = {
                "role": "system",
                "content": (
                    "你是一名专业的技术博客编辑，擅长撰写类似微信公众号的高质量文章。"
                    "给定多个文档（PDF原文、讲解PPT、讨论纪要），请将其整合为一篇结构化、美观、易读的中文技术博文。\n\n"
                    "**严格要求：**\n"
                    "1. ⚠️ 必须只返回纯 JSON 对象，不要任何解释、代码块标记（```）或其他文本！\n"
                    "2. JSON 格式：{\"title\": \"\", \"summary\": \"\", \"tags\": [], \"content\": \"\", \"category\": \"\"}\n"
                    "3. title：吸引人的标题（10-25字），体现核心价值\n"
                    "4. summary：精炼摘要（50-120字），概括核心观点和亮点\n"
                    "5. tags：3-6个精准关键词（中文）\n"
                    "6. content：Markdown 格式的正文（2000-4000字），必须包含：\n"
                    "   - **引言**（1-2段，引出话题，说明重要性，吸引读者）\n"
                    "   - **核心内容**（2-4个## 二级标题，每部分3-5段，包含要点、代码示例、公式、图表说明）\n"
                    "   - **实践应用**（真实案例、最佳实践、避坑指南）\n"
                    "   - **总结与展望**（归纳要点、未来方向、行动建议）\n"
                    "   - 适当使用：> 引用块（重点提示）、**加粗**（关键术语）、`代码`、- 列表、数字序号\n"
                    "7. 语言风格：专业但通俗易懂，避免过于学术化，像对话般讲解，适合技术人员快速理解\n"
                    "8. 排版：段落间留空行，每段2-5行，保持视觉舒适，重要内容用引用块突出\n"
                    "9. category：使用提供的分类或从内容推断合适的技术分类\n\n"
                    "⚠️ 再次强调：直接输出 JSON 对象，不要包裹在代码块中！"
                ),
            }
            user_msg = {
                "role": "user",
                "content": f"分类：{category}\n\n{combined_text}"
            }

            resp = client.chat.completions.create(
                model="deepseek-chat",
                messages=[system_msg, user_msg],
                response_format={"type": "json_object"},  # 强制返回 JSON 格式
                temperature=0.7,
                max_tokens=4096,
                stream=False,
            )

            raw = resp.choices[0].message.content
            print(f"[DEBUG] DeepSeek raw response:\n{raw[:1200]}\n...")

            # 清理常见的 Markdown 代码块包裹（```json ... ``` 或 ``` ... ```）
            clean = raw.strip()
            # 移除开头的代码块标记
            if clean.startswith("```json"):
                clean = clean[7:]
            elif clean.startswith("```"):
                clean = clean[3:]
            # 移除结尾的代码块标记
            if clean.endswith("```"):
                clean = clean[:-3]
            clean = clean.strip()

            # 尝试直接解析
            data = None
            try:
                data = json.loads(clean)
            except Exception:
                # 如果失败，尝试从第一个 { 到最后一个 } 提取
                start_idx = clean.find("{")
                end_idx = clean.rfind("}")
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    candidate = clean[start_idx:end_idx+1]
                    try:
                        data = json.loads(candidate)
                    except Exception:
                        data = None

            # 如果解析成功，取字段；否则降级为将合并文本作为 content
            if data:
                title = data.get("title") or data.get("标题") or "未命名博文"
                summary = data.get("summary") or data.get("摘要") or ""
                tags = data.get("tags") or data.get("标签") or []
                content = data.get("content") or data.get("正文") or combined_text
                cat = data.get("category") or category
                slug = hashlib.sha1(content.encode("utf-8")).hexdigest()[:10]
                return {"title": title, "summary": summary, "tags": tags, "content": content, "category": cat, "slug": slug}
            else:
                # 自动重试：发送严格 JSON-only prompt
                print("[RETRY] First parse failed, sending strict JSON-only request...")
                retry_system = {
                    "role": "system",
                    "content": (
                        "你必须只返回有效的 JSON 对象，不要任何解释、代码块或其他文本。"
                        "格式：{\"title\":\"标题\",\"summary\":\"摘要\",\"tags\":[\"标签1\",\"标签2\"],\"content\":\"Markdown内容\",\"category\":\"分类\"}。"
                        "如果无法生成，返回：{\"error\":\"原因\"}。"
                    )
                }
                retry_user = {
                    "role": "user",
                    "content": f"基于以下内容生成技术博文的 JSON：\n\n{combined_text[:3000]}"
                }
                try:
                    retry_resp = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[retry_system, retry_user],
                        response_format={"type": "json_object"},  # 强制 JSON
                        temperature=0.3,
                        max_tokens=4096,
                    )
                    retry_raw = retry_resp.choices[0].message.content
                    # 再次清理和提取
                    retry_clean = retry_raw.strip()
                    if retry_clean.startswith("```json"):
                        retry_clean = retry_clean[7:]
                    elif retry_clean.startswith("```"):
                        retry_clean = retry_clean[3:]
                    if retry_clean.endswith("```"):
                        retry_clean = retry_clean[:-3]
                    retry_clean = retry_clean.strip()
                    
                    retry_data = None
                    try:
                        retry_data = json.loads(retry_clean)
                    except:
                        retry_start = retry_clean.find("{")
                        retry_end = retry_clean.rfind("}")
                        if retry_start != -1 and retry_end != -1:
                            retry_candidate = retry_clean[retry_start:retry_end+1]
                            retry_data = json.loads(retry_candidate)
                    
                    if retry_data and "error" not in retry_data:
                            title = retry_data.get("title") or "未命名博文"
                            summary = retry_data.get("summary") or ""
                            tags = retry_data.get("tags") or []
                            content = retry_data.get("content") or combined_text
                            cat = retry_data.get("category") or category
                            slug = hashlib.sha1(content.encode("utf-8")).hexdigest()[:10]
                            print(f"[RETRY] Success! Title: {title[:50]}")
                            return {"title": title, "summary": summary, "tags": tags, "content": content, "category": cat, "slug": slug}
                except Exception as e:
                    print(f"[RETRY] Failed: {e}")
                
                # fallback: 模型没有返回可解析的 JSON，使用合并文本作为内容
                slug = hashlib.sha1((raw or combined_text).encode("utf-8")).hexdigest()[:10]
                return {
                    "title": "未命名博文",
                    "summary": (raw or combined_text)[:300],
                    "tags": _simple_tags(combined_text),
                    "content": raw or combined_text,
                    "category": category,
                    "slug": slug
                }
        except Exception:
            pass

    # Fallback: use local mock
    slug = hashlib.sha1((combined_text or "").encode("utf-8")).hexdigest()[:10]
    return {
        "title": "未命名博文",
        "summary": (combined_text or "")[:400],
        "tags": _simple_tags(combined_text),
        "content": combined_text,
        "category": category,
        "slug": slug
    }
