from scholarly import scholarly, ProxyGenerator
import json
from datetime import datetime
import os
import requests

def setup_scholar_proxy():
    """使用 ScraperAPI 配置 scholarly 代理"""
    api_key = os.environ.get("SCRAPER_API_KEY")
    if not api_key:
        print("环境变量 SCRAPER_API_KEY 未配置，跳过 Google Scholar 抓取")
        return False

    pg = ProxyGenerator()
    # ScraperAPI 的官方用法就是这样：pg.ScraperAPI(API_KEY) :contentReference[oaicite:3]{index=3}
    success = pg.ScraperAPI(api_key)
    if not success:
        print("ScraperAPI 代理初始化失败，跳过 Google Scholar 抓取")
        return False

    scholarly.use_proxy(pg)

    # 可选：降低每次请求的 timeout & 重试次数，避免死撑太久
    try:
        scholarly.set_timeout(10)   # 单次请求最多等 10 秒
        scholarly.set_retries(1)    # 最多重试 1 次
    except Exception as e:
        print("设置 timeout / retries 失败，不影响主流程：", e)

    return True

def get_scholar():
    # 先尝试配置代理
    if not setup_scholar_proxy():
        return

    try:
        author = scholarly.search_author_id("SSaBaioAAAAJ")
        scholarly.fill(author, sections=['basics', 'indices', 'counts', 'publications'])
    except Exception as e:
        print("Google Scholar 请求失败，已跳过:", e)
        return  # 失败就直接跳过

    author['updated'] = str(datetime.now())
    author['publications'] = {v['author_pub_id']: v for v in author['publications']}

    shieldio_data = {
        "schemaVersion": 1,
        "label": "citations",
        "message": f"{author['citedby']}",
    }

    # 注意：因为我们在 workflow 里是 `python3 ./assets/get_scholar_github.py`
    # 当前工作目录是仓库根目录，这里路径写成 ./assets/xxx.json
    with open('./assets/gs_data_shieldsio.json', 'w') as outfile:
        json.dump(shieldio_data, outfile, ensure_ascii=False)

def get_repo_stars(repo_full_name):
    """
    repo_full_name: 字符串，例如 'torvalds/linux'
    """
    url = f"https://api.github.com/repos/{repo_full_name}"
    resp = requests.get(url)

    if resp.status_code != 200:
        print(f"获取失败：{repo_full_name}，状态码：{resp.status_code}")
        return 0

    data = resp.json()
    return data.get("stargazers_count", 0)

def get_github(repo_list):
    total = 0
    for repo in repo_list:
        stars = get_repo_stars(repo)
        total += stars
    
    shieldio_data = {
        "schemaVersion": 1,
        "label": "stars",
        "message": f"{total}",
    }
    with open('./assets/stars_data_shieldsio.json', 'w') as outfile:
        json.dump(shieldio_data, outfile, ensure_ascii=False)

repos = [
    "WangRongsheng/awesome-LLM-resources",
    "WangRongsheng/XrayGLM",
    "WangRongsheng/CareGPT",
    "WangRongsheng/ChatGenTitle",
    "WangRongsheng/MedQA-ChatGLM",
    "WangRongsheng/Aurora",
    "WangRongsheng/BestYOLO",
    "WangRongsheng/SAM-fine-tune",
    "WangRongsheng/Use-LLMs-in-Colab",
    "WangRongsheng/DS_Yanweimin",
    "WangRongsheng/Awesome-LLM-with-RAG",
    "WangRongsheng/KDAT",
    "kaixindelele/ChatPaper",
    "FreedomIntelligence/Awesome-AI4Med",
]

if __name__ == "__main__":
    # 双保险：Scholar 挂了也不影响 GitHub stars 更新
    try:
        get_scholar()
    except Exception as e:
        print("get_scholar() 出现未捕获异常，已忽略：", e)

    get_github(repos)
