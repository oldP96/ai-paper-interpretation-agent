import requests
import re

def bing_search(query: str, num_results: int = 5):
    """
    通过爬取 Bing 搜索结果页面获取前几个结果链接，无需 API Key。
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    params = {"q": query, "count": num_results}
    url = "https://www.bing.com/search"
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        html = resp.text
        # 用正则提取搜索结果链接
        links = re.findall(r'<li class="b_algo".*?<a href="(http[s]?://[^"]+)"', html, re.S)
        return links[:num_results] if links else ["未找到相关结果"]
    except Exception as e:
        return [f"Bing 搜索失败: {e}"]
