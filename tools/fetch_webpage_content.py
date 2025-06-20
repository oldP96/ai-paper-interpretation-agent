from newspaper import Article
def fetch_webpage_content(url: str, max_total_length: int = 4500):
    try:
        article = Article(url, language='zh')
        article.download()
        article.parse()
    except Exception as e:
        return f"请求失败，错误信息：{e}"

    # 提取主体文本并截断
    text_content = article.text.strip()
    if len(text_content) > max_total_length:
        text_content = text_content[:max_total_length] + '...'

    # 提取图片链接（主体图片+其他图片）
    images = list(article.images)

    # 主图优先
    if article.top_image:
        images = [article.top_image] + [img for img in images if img != article.top_image]

    images_content = "\n".join(f"[IMAGE:{img}]" for img in images[:5])  # 限制前5张

    final_content = f"[TEXT:{text_content}]\n\n{images_content}" if images else f"[TEXT:{text_content}]"

    return final_content if final_content else "未能提取到有效内容。"
