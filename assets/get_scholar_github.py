from scholarly import scholarly
import jsonpickle
import json
from datetime import datetime
import os
import requests

def get_scholar():
    author: dict = scholarly.search_author_id("SSaBaioAAAAJ")
    scholarly.fill(author, sections=['basics', 'indices', 'counts', 'publications'])
    name = author['name']
    author['updated'] = str(datetime.now())
    author['publications'] = {v['author_pub_id']:v for v in author['publications']}

    shieldio_data = {
    "schemaVersion": 1,
    "label": "citations",
    "message": f"{author['citedby']}",
    }
    with open(f'./assets/gs_data_shieldsio.json', 'w') as outfile:
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
    with open(f'./assets/stars_data_shieldsio.json', 'w') as outfile:
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

get_scholar()
get_github(repos)
