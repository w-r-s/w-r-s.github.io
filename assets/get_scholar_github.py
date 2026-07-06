import json
from datetime import datetime
import os
import requests
import signal
from pathlib import Path

# =====================================================
#  全局超时控制（用于限制整个 scholarly 流程最多 60 秒）
# =====================================================
class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException()


def write_json_atomic(path, data):
    """Replace badge data only after the new JSON has been fully written."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    with tmp_path.open('w') as f:
        json.dump(data, f, ensure_ascii=False)
    tmp_path.replace(output_path)


# =====================================================
#  Google Scholar citation 抓取（无代理 + 超时自动跳过）
# =====================================================
def get_scholar():
    from scholarly import scholarly

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

    write_json_atomic('./assets/gs_data_shieldsio.json', shieldio_data)

    print("Google Scholar 数据已更新：", author['citedby'])


# =====================================================
#  GitHub stars 统计
# =====================================================
def get_repo_stars(repo_full_name):
    """返回 repo star 数"""
    url = f"https://api.github.com/repos/{repo_full_name}"
    headers = {}
    github_token = os.environ.get("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    try:
        resp = requests.get(url, headers=headers, timeout=12)
    except requests.RequestException as e:
        print(f"获取失败：{repo_full_name}，请求异常：{e}")
        return None

    if resp.status_code != 200:
        print(f"获取失败：{repo_full_name}，状态码：{resp.status_code}")
        return None

    data = resp.json()
    return data.get("stargazers_count", 0)


def get_github(repo_list):
    total = 0
    for repo in repo_list:
        stars = get_repo_stars(repo)
        if stars is None:
            print("GitHub stars 更新失败，保留旧 badge 数据")
            return
        total += stars

    shieldio_data = {
        "schemaVersion": 1,
        "label": "stars",
        "message": f"{total}",
    }

    write_json_atomic('./assets/stars_data_shieldsio.json', shieldio_data)

    print("GitHub stars 数据已更新，总 stars =", total)


def badge_filename(repo_full_name):
    return repo_full_name.replace("/", "__") + ".json"


def get_project_stars(project_list):
    projects = []
    badge_data = []

    for project in project_list:
        stars = get_repo_stars(project["repo"])
        if stars is None:
            print("Projects stars 更新失败，保留旧项目 stars 数据")
            return

        projects.append({
            "name": project["name"],
            "repo": project["repo"],
            "html_url": f"https://github.com/{project['repo']}",
            "stargazers_count": stars,
        })
        badge_data.append((project["repo"], {
            "schemaVersion": 1,
            "label": "stars",
            "message": f"{stars}",
            "color": "yellow",
            "logo": "github",
            "style": "flat-square",
            "cacheSeconds": 3600,
        }))

    write_json_atomic('./assets/project_stars.json', {
        "updated": datetime.now().isoformat(),
        "projects": projects,
    })
    for repo, shieldio_data in badge_data:
        write_json_atomic(f'./assets/project_stars_badges/{badge_filename(repo)}', shieldio_data)

    print("Projects stars 数据已更新，项目数 =", len(projects))


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
    "FreedomIntelligence/OpenClaw-Medical-Skills",
    "FreedomIntelligence/Med-MAT",
    "FreedomIntelligence/TinyDeepSeek"
]

project_repos = [
    {"name": "RoboVerse", "repo": "RoboVerseOrg/RoboVerse"},
    {"name": "GameCraft-Bench", "repo": "FreedomIntelligence/gamecraft-bench"},
    {"name": "MicroVerse", "repo": "FreedomIntelligence/MicroVerse"},
    {"name": "MedGen", "repo": "FreedomIntelligence/MedGen"},
    {"name": "Med-MAT", "repo": "FreedomIntelligence/Med-MAT"},
    {"name": "ManipLLM", "repo": "clorislili/ManipLLM"},
    {"name": "awesome-LLM-resources", "repo": "WangRongsheng/awesome-LLM-resources"},
    {"name": "CareGPT", "repo": "WangRongsheng/CareGPT"},
    {"name": "XrayGLM", "repo": "WangRongsheng/XrayGLM"},
    {"name": "ChatPaper", "repo": "kaixindelele/ChatPaper"},
    {"name": "ChatGenTitle", "repo": "WangRongsheng/ChatGenTitle"},
    {"name": "Awesome-AI4Med", "repo": "FreedomIntelligence/Awesome-AI4Med"},
    {"name": "TinyDeepSeek", "repo": "FreedomIntelligence/TinyDeepSeek"},
    {"name": "MiniGPT-4", "repo": "Vision-CAIR/MiniGPT-4"},
    {"name": "OpenClaw-Medical-Skills", "repo": "FreedomIntelligence/OpenClaw-Medical-Skills"},
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
    get_project_stars(project_repos)
