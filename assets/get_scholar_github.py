import argparse
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
#  Google Scholar citation update (SerpApi preferred, direct access fallback)
# =====================================================
def get_scholar():
    serpapi_key = os.environ.get("SERPAPI_KEY")
    if serpapi_key:
        response = requests.get(
            "https://serpapi.com/search.json",
            params={
                "engine": "google_scholar_author",
                "author_id": "SSaBaioAAAAJ",
                "api_key": serpapi_key,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        table = data.get("cited_by", {}).get("table", [])
        citations = table[0].get("citations", {}).get("all") if table else None
        try:
            citations = int(citations)
        except (TypeError, ValueError) as exc:
            raise RuntimeError("SerpApi response did not contain a citation count")
        write_scholar_badge(citations)
        print("Google Scholar data updated through SerpApi:", citations)
        return

    print("SERPAPI_KEY is not configured; falling back to direct Google Scholar access")
    from scholarly import scholarly

    # 设置整个 get_scholar 的超时时间（单位：秒）
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(60)

    try:
        scholarly.set_timeout(10)
        scholarly.set_retries(1)
        author = scholarly.search_author_id("SSaBaioAAAAJ")
        scholarly.fill(author, sections=['basics', 'indices', 'counts'])
    except TimeoutException as exc:
        raise RuntimeError("Google Scholar request exceeded 60 seconds") from exc
    finally:
        signal.alarm(0)

    write_scholar_badge(author['citedby'])
    print("Google Scholar data updated directly:", author['citedby'])


def write_scholar_badge(citations):
    if not isinstance(citations, int) or citations < 0:
        raise ValueError(f"Invalid Google Scholar citation count: {citations!r}")

    shieldio_data = {
        "schemaVersion": 1,
        "label": "citations",
        "message": str(citations),
    }

    write_json_atomic('./assets/gs_data_shieldsio.json', shieldio_data)


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
        raise RuntimeError(f"GitHub request failed for {repo_full_name}: {e}") from e

    if resp.status_code != 200:
        raise RuntimeError(
            f"GitHub request failed for {repo_full_name}: HTTP {resp.status_code}"
        )

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

    write_json_atomic('./assets/stars_data_shieldsio.json', shieldio_data)

    print("GitHub stars 数据已更新，总 stars =", total)


def badge_filename(repo_full_name):
    return repo_full_name.replace("/", "__") + ".json"


def get_project_stars(project_list):
    projects = []
    badge_data = []

    for project in project_list:
        stars = get_repo_stars(project["repo"])
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
    {"name": "GameCraft-Bench", "repo": "FreedomIntelligence/gamecraft-bench"},
    {"name": "MicroVerse", "repo": "FreedomIntelligence/MicroVerse"},
    {"name": "MedGen", "repo": "FreedomIntelligence/MedGen"},
    {"name": "Med-MAT", "repo": "FreedomIntelligence/Med-MAT"},
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
#  Main entry point
# =====================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update homepage citation and star data")
    parser.add_argument(
        "target",
        nargs="?",
        choices=("all", "scholar", "github"),
        default="all",
        help="data source to update (default: all)",
    )
    args = parser.parse_args()

    scholar_error = None
    if args.target in ("all", "scholar"):
        try:
            get_scholar()
        except Exception as exc:
            if args.target == "scholar":
                raise
            scholar_error = exc
            print("Google Scholar update failed; continuing with GitHub data:", exc)

    if args.target in ("all", "github"):
        get_github(repos)
        get_project_stars(project_repos)

    if scholar_error:
        raise RuntimeError("Google Scholar update failed") from scholar_error
