from scholarly import scholarly
import json
from datetime import datetime
import os
import requests
import signal

# =====================================================
#  全局超时控制（用于限制整个 scholarly 流程最多 60 秒）
# =====================================================
class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException()


# =====================================================
#  Google Scholar citation 抓取（无代理 + 超时自动跳过）
# =====================================================
def get_scholar():

    # 设置整个 get_scholar 的超时时间（单位：秒）
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(60)

    try:
        # 限制单次请求超时时间 / 重试次数，进一步避免卡死
        scholarly.set_timeout(10)
        scholarly.set_retries(1)

        author = scholarly.search_author_id("SSaBaioAAAAJ")
        scholarly.fill(author, sections=['basics', 'indices', 'counts', 'publications'])

        # Scholar 请求成功，关闭超时 alarm
        signal.alarm(0)

    except TimeoutException:
        print("Google Scholar 请求超过 60 秒，已跳过")
        return

    except Exception as e:
        print("Google Scholar 请求失败，已跳过：", e)
        return

    # === 生成 shields.io JSON ===
    author['updated'] = str(datetime.now())
    author['publications'] = {v['author_pub_id']: v for v in author['publications']}

    shieldio_data = {
        "schemaVersion": 1,
        "label": "citations",
        "message": f"{author['citedby']}",
    }

    with open('./assets/gs_data_shieldsio.json', 'w') as f:
        json.dump(shieldio_data, f, ensure_ascii=False)

    print("Google Scholar 数据已更新：", author['citedby'])


# =====================================================
#  GitHub stars 统计
# =====================================================
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

    with open('./assets/stars_data_shieldsio.json', 'w') as f:
        json.dump(shieldio_data, f, ensure_ascii=False)

    print("GitHub stars 数据已更新，总 stars =", total)


# =====================================================
#  要统计的仓库列表
# =====================================================
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


# =====================================================
#  主入口（Scholar 失败不会影响 Stars）
# =====================================================
if __name__ == "__main__":
    try:
        get_scholar()
    except Exception as e:
        print("get_scholar() 出现未捕获异常，已忽略：", e)

    get_github(repos)
