import os
import json
import requests
from openai import OpenAI

MODEL_NAME = "qwen-max"
DASHSCOPE_API_KEY = "your_api_key"
MCP_SERVER_URL = "http://localhost:8000/mcp"  # 替换为实际的MCP服务器地址

client = OpenAI(
    api_key=DASHSCOPE_API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

tools = [
    {
        "type": "function",
        "function": {
            "name": "google_search",
            "description": "用 Google 搜索获得网页链接。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "要搜索的内容"},
                    "num_results": {"type": "integer", "description": "返回结果数", "default": 5}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "bing_search",
            "description": "用 Bing 搜索获得网页链接。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "要搜索的内容"},
                    "num_results": {"type": "integer", "description": "返回结果数", "default": 5}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_webpage_content",
            "description": "抓取指定网页的正文内容和图片。",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "要抓取的网页 URL"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "download_pdf",
            "description": "下载 PDF 文件到服务器本地。",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "PDF 文件的下载地址"},
                    "save_path": {"type": "string", "description": "保存到本地的路径"}
                },
                "required": ["url", "save_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "parse_pdf",
            "description": "解析 PDF 文件，返回主要文本内容。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "本地 PDF 文件路径"}
                },
                "required": ["file_path"]
            }
        }
    }
]

def call_mcp(method, params):
    """
    调用 MCP 服务器，执行 LLM 生成的指令。
    """
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(MCP_SERVER_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        resp_json = response.json()
        if isinstance(resp_json, dict) and ("result" in resp_json or "error" in resp_json):
            return resp_json
        else:
            return {"jsonrpc": "2.0", "id": 1, "result": resp_json}
    except Exception as e:
        return {"jsonrpc": "2.0", "id": 1, "error": {"code": -32000, "message": f"工具调用失败: {e}"}}


def interact_with_model(user_input):
    """
    与模型进行交互，处理用户输入并返回响应。
    """
    messages = [
        {
            "role": "system",
            "content": (
                "你是一个高效、结构化的智能助手。"
                "每次调用工具前，先分步说明该步的目的和计划。"
                "你必须严格执行以下步骤，且每步都必须调用指定工具，不可跳过任何环节：\
                1. 用 google_search 或 bing_search 搜索 DeepSeek R1 论文的下载链接。\
                2. 用 download_pdf 下载论文到本地。\
                3. 用 parse_pdf 解析已下载的PDF文件。\
                每步都要等到上一步有结果后再执行下一步，严格分开。"
                "工具调用后，整理工具调用参数和结果。"
                "全部完成后，请按如下结构化格式输出全部过程及最终评价：\n\n"
                "### 步骤 1: xxx\n- **目的**: ...\n- **工具**: ...\n- **参数**: ...\n- **结果**: ...\n"
                "### 步骤 2: ...\n...\n"
                "### 论文简要评价（最后一步）\n- **概述**: ...\n- **优点**: ...\n- **改进空间**: ...\n"
                "必须严格遵循上述格式，不要遗漏任何步骤。"
            )
        },
        {
            "role": "user", 
            "content": user_input
        }
    ]
    step_contexts = []  # 用于保存每一步结构化内容
    while True:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            stream=False
        )
        message = completion.choices[0].message

        # 如果有工具调用
        if getattr(message, "tool_calls", None):
            # 结构化保存本次assistant的分步说明
            step_desc = message.content or ""
            messages.append({
                "role": "assistant",
                "content": step_desc,
                "tool_calls": [tc.model_dump() if hasattr(tc, "model_dump") else {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    }
                } for tc in message.tool_calls]
            })
            for tool_call in message.tool_calls:
                name = tool_call.function.name
                try:
                    args = json.loads(tool_call.function.arguments)
                except Exception as e:
                    print(f"[系统] 工具参数解析失败: {e}")
                    args = {}
                print(f"[系统] 调用工具: {name} 参数: {args}")
                result = call_mcp(name, args)
                print(f"[系统] 工具返回: {result}\n")
                # 保存本步结构化上下文
                step_contexts.append({
                    "step_desc": step_desc,
                    "tool": name,
                    "params": args,
                    "result": result
                })
                # 追加tool消息
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result)
                })
            continue  # 继续循环
        else:
            # 最后组织结构化总结prompt
            # （把各步内容拼成上下文，要求模型总结）
            steps_text = ""
            for idx, step in enumerate(step_contexts, 1):
                steps_text += f"### 步骤 {idx}: \n"
                steps_text += f"- **目的**: {step['step_desc']}\n"
                steps_text += f"- **工具**: {step['tool']}\n"
                steps_text += f"- **参数**: {json.dumps(step['params'], ensure_ascii=False)}\n"
                steps_text += f"- **结果**: {json.dumps(step['result'], ensure_ascii=False)}\n\n"
            summary_prompt = (
                f"请根据以下步骤过程，严格按照【步骤-目的-工具-参数-结果】结构输出，并对论文进行简要评价：\n\n{steps_text}"
                "最后请补充一段论文简要概述和评价（优点/改进空间）。"
            )
            messages.append({"role": "user", "content": summary_prompt})
            final = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                stream=True
            )
            print("\n[AI]: ", end="", flush=True)
            for chunk in final:
                delta = getattr(chunk.choices[0].delta, "content", None)
                if delta:
                    print(delta, end="", flush=True)
            print()
            break

    
if __name__ == "__main__":
    print(">>> MCP寻找论文下载解读工具增强AI助手 <<<")
    while True:
        try:
            user_input = input("\n你: ").strip()
            if user_input.lower() in ("exit", "quit"):
                print("已退出。")
                break
            interact_with_model(user_input)
        except KeyboardInterrupt:
            print("\n退出。")
            break
