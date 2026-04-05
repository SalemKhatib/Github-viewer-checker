import urllib.request
import urllib.error
import json
import os

# ── Config ──────────────────────────────────────────────────────────────────
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "YOUR_TOKEN_HERE")
# ────────────────────────────────────────────────────────────────────────────

BASE_URL = "https://api.github.com"

def gh_get(path):
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def get_username():
    return gh_get("/user")["login"]


def get_owned_repos(username):
    repos, page = [], 1
    while True:
        batch = gh_get(f"/user/repos?per_page=100&page={page}&type=owner")
        if not batch:
            break
        repos.extend(batch)
        page += 1
    # Extra safety: only repos where we are the owner
    return [r for r in repos if r["owner"]["login"] == username]


def get_traffic(owner, repo):
    try:
        return gh_get(f"/repos/{owner}/{repo}/traffic/views")
    except urllib.error.HTTPError as e:
        if e.code == 403:
            return None   # no push access → no traffic data
        raise


def display(repos_traffic):
    col_w = max(len(r) for r, _ in repos_traffic) + 2
    header = f"{'Repository':<{col_w}} {'Unique viewers (14d)':>20}  {'Total views (14d)':>18}"
    print("\n" + header)
    print("─" * len(header))
    for repo, data in repos_traffic:
        if data is None:
            unique = total = "no access"
            print(f"{repo:<{col_w}} {'no access':>20}  {'no access':>18}")
        else:
            unique = data.get("uniques", 0)
            total  = data.get("count",   0)
            print(f"{repo:<{col_w}} {unique:>20,}  {total:>18,}")
    print()


def main():
    if GITHUB_TOKEN == "YOUR_TOKEN_HERE":
        print("ERROR: Set your GitHub token via the GITHUB_TOKEN env variable.")
        print("  export GITHUB_TOKEN=ghp_xxxxxxxxxxxx")
        return

    print("Fetching your repositories…")
    username = get_username()
    repos    = get_owned_repos(username)

    if not repos:
        print("No owned repositories found.")
        return

    print(f"Found {len(repos)} owned repo(s) for @{username}. Fetching traffic…\n")

    results = []
    for repo in repos:
        name    = repo["name"]
        traffic = get_traffic(username, name)
        results.append((name, traffic))

    display(results)


if __name__ == "__main__":
    main()
