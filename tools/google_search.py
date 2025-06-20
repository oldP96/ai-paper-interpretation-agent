from googlesearch import search
from tools.bing_search import bing_search

def google_search(query: str, num_results: int = 5):
    try:
        results = []
        for url in search(query, num_results=num_results, lang='zh-CN'):
            results.append(url)
        if results:
            return results
        else:
            # google无结果时也兜底bing
            return bing_search(query, num_results)
    except Exception:
        # google报错时兜底bing
        return bing_search(query, num_results)