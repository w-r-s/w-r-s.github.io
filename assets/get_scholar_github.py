from scholarly import scholarly, ProxyGenerator
import json
from datetime import datetime
import os
import requests

# =======================
#  初始化 Google Scholar 代理
# =======================
def setup_scholar_proxy():
    """使用 ScraperAPI 配置代理（最稳定方式：SingleProxy 自定义 URL）"""
    api_key = os.environ.get("SCRAPER_API_KEY")
    if not api_key:
        print("SCRAPER_API_KEY 未设置，跳过 Google Scholar 抓取")
        return False

    pg = ProxyGenerator()

    # ScraperAPI 官方代理格式
    proxy_url = f"http://scraperapi:{api_key}@proxy-server.scraperapi.com:8001"

    # 使用 SingleProxy，而不是 scholarly 内置 ScraperAPI 函数
    pg.SingleProxy(http=proxy_url, https=proxy_url)

    scholarly.use_proxy(pg)

    # 设置请求超时和重试次数，避免网络不通时拖太久
    try:
        scholarly.set_timeout(10)   # 单次请求最多等 10s
        scholarly.set_retries(1)    # 最多重试 1 次
    except Exception as e:
        print("设置 timeout/retries 失败，但不影响主流程：", e)

    return True


# =======================
#  Google Scholar Citation 抓取
# =======================
def get_scholar():
    # 启动代理
    if not setup_scholar_proxy():
        return  # 不配置代理就直接跳过

    try:
        author = scholarly.search_author_id("SSaBaioAAAAJ")
        scholarly.fill(author, sections=['basics', 'indices', 'counts', 'publications'])
    except Exception as e:
        print("Google Scholar 请求失败，已跳过：", e)
        return

    # 数据整理
    author['updated'] = str(datetime.now())
    author['publications'] = {v['author_pub_id']: v for v in author['publications']}

    # 输出 badge 用的数据
    shieldio_data = {
        "schemaVersion": 1,
        "label": "citations",
        "message": f"{author['citedby']}",
    }

    with open('./assets/gs_data_shieldsio.json', 'w') as outfile:
        json.dump(shieldio_data, outfile, ensure_ascii=False)

    print("Google Scholar 数据已更新")


# =======================
#  GitHub Stars 统计
# =======================
def get_repo_stars(repo_full_name):
    """返回 repo star 数"""
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

    print("GitHub stars 数据已更新，总 stars =", total)


# =======================
#  要统计的仓库列表
# =======================
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


# =======================
#  主入口
# =======================
if __name__ == "__main__":
    # Scholar 错误不会影响 GitHub stars 更新
    try:
        get_scholar()
    except Exception as e:
        print("get_scholar() 出现未捕获异常，已忽略：", e)

    get_github(repos)
