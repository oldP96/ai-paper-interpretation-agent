# src/server/mcp_server.py
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..')) # 添加上级目录到路径中，以便导入工具模块
from aiohttp import web
from tools.google_search import google_search
from tools.bing_search import bing_search
from tools.fetch_webpage_content import fetch_webpage_content
from tools.parse_pdf import parse_pdf
from tools.download_pdf import download_pdf

async def handle(request):
    req = await request.json()
    method = req.get("method")
    params = req.get("params", {})
    id_ = req.get("id")
    try:
        if method == "google_search":
            result = google_search(params.get("query", ""), params.get("num_results", 5))
        elif method == "bing_search":
            result = bing_search(params.get("query", ""), params.get("num_results", 5))
        elif method == "fetch_webpage_content":
            result = fetch_webpage_content(params.get("url", ""))
        elif method == "parse_pdf":
            result = parse_pdf(params.get("file_path", ""))
        elif method == "download_pdf":
            result = download_pdf(params.get("url", ""), params.get("save_path", ""))
        else:
            return web.json_response({"jsonrpc": "2.0", "id": id_, "error": {"code": -32601, "message": "Method not found"}})
        return web.json_response({"jsonrpc": "2.0", "id": id_, "result": result})
    except Exception as e:
        return web.json_response({"jsonrpc": "2.0", "id": id_, "error": {"code": -32000, "message": str(e)}})

app = web.Application()
app.router.add_post("/mcp", handle)

if __name__ == "__main__":
    web.run_app(app, port=8000)
