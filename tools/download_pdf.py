import requests

def download_pdf(url, save_path):
    """
    下载PDF文件到指定路径。
    """
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(save_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    return save_path
