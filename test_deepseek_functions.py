import os
from openai import OpenAI

api_key = "sk-c19847906874408e86a65a8fa6f5dc3c"
client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

# Test 1: Check if response_format is supported
print("=== Test 1: response_format (JSON mode) ===")
try:
    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": "Return a JSON with keys: name, age"}],
        response_format={"type": "json_object"},
        max_tokens=100,
    )
    print("✅ response_format supported!")
    print(f"Response: {resp.choices[0].message.content[:200]}")
except Exception as e:
    print(f"❌ response_format not supported: {e}")

# Test 2: Check if function calling is supported
print("\n=== Test 2: Function Calling ===")
try:
    functions = [{
        "name": "create_blog_post",
        "description": "Create a structured blog post",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "summary": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["title", "summary"]
        }
    }]
    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": "Write a blog about AI"}],
        functions=functions,
        max_tokens=100,
    )
    print("✅ Function calling supported!")
    print(f"Response: {resp}")
except Exception as e:
    print(f"❌ Function calling not supported: {e}")

print("\n=== Test 3: Tools (newer API) ===")
try:
    tools = [{
        "type": "function",
        "function": {
            "name": "create_blog_post",
            "description": "Create a structured blog post",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "summary": {"type": "string"},
                },
                "required": ["title"]
            }
        }
    }]
    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": "Write a blog about AI"}],
        tools=tools,
        max_tokens=100,
    )
    print("✅ Tools API supported!")
    print(f"Response: {resp}")
except Exception as e:
    print(f"❌ Tools API not supported: {e}")
