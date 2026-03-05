import os
import json
import csv
import time
import urllib.request
import urllib.error


def load_dotenv():
    """Carrega variáveis do arquivo .env para os.environ."""
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ[key.strip()] = value.strip().strip('"').strip("'")


load_dotenv()
TOKEN = os.getenv("GITHUB_TOKEN")

if not TOKEN:
    raise SystemExit("Defina o token: set GITHUB_TOKEN=SEU_TOKEN")

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "User-Agent": "lab-github",
    "Accept": "application/vnd.github+json"
}

GRAPHQL_URL = "https://api.github.com/graphql"


def fetch_top_repos_rest(n=100):
    print("Buscando TOP repos via REST (ranking por estrelas)...")

    repos = []
    page = 1

    while len(repos) < n:
        url = f"https://api.github.com/search/repositories?q=stars:>1&sort=stars&order=desc&per_page=100&page={page}"

        req = urllib.request.Request(url, headers=HEADERS)

        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())

        repos.extend(data["items"])
        page += 1

    return repos[:n]


GRAPHQL_QUERY = """
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    name
    nameWithOwner
    url
    stargazerCount
    createdAt
    updatedAt
    pushedAt

    primaryLanguage { name }

    releases { totalCount }

    pullRequests(states: MERGED) { totalCount }

    issues { totalCount }

    closedIssues: issues(states: CLOSED) { totalCount }
  }
}
"""


def graphql_repo(owner, name):
    payload = json.dumps({
        "query": GRAPHQL_QUERY,
        "variables": {"owner": owner, "name": name}
    }).encode()

    req = urllib.request.Request(
        GRAPHQL_URL,
        data=payload,
        headers={
            **HEADERS,
            "Content-Type": "application/json"
        }
    )

    for attempt in range(5):
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode())
                return data["data"]["repository"]

        except Exception:
            wait = 2 ** attempt
            print(f"Retry GraphQL {owner}/{name} ({wait}s)")
            time.sleep(wait)

    print(f"Falhou: {owner}/{name}")
    return None
    
def save_csv(rows, filename="top_1000_repos_github.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "name",
            "nameWithOwner",
            "url",
            "stars",
            "createdAt",
            "updatedAt",
            "language",
            "releases",
            "mergedPRs",
            "issues_total",
            "issues_closed",
            "issues_closed_ratio"
        ])

        for r in rows:
            total = r["issues"]["totalCount"]
            closed = r["closedIssues"]["totalCount"]
            ratio = closed / total if total else 0

            writer.writerow([
                r["name"],
                r["nameWithOwner"],
                r["url"],
                r["stargazerCount"],
                r["createdAt"],
                r["updatedAt"],
                r["primaryLanguage"]["name"] if r["primaryLanguage"] else "",
                r["releases"]["totalCount"],
                r["pullRequests"]["totalCount"],
                total,
                closed,
                ratio
            ])


def main():
    N_REPOS = 1000
    top = fetch_top_repos_rest(N_REPOS)

    print(f"Coletando métricas GraphQL para {len(top)} repositórios...")

    rows = []
    for i, repo in enumerate(top, 1):
        owner = repo["owner"]["login"]
        name = repo["name"]

        data = graphql_repo(owner, name)
        if data:
            rows.append(data)

        if i % 100 == 0:
            print(f"  Progresso: {i}/{len(top)}")
        time.sleep(0.3)

    csv_file = "top_1000_repos_github.csv"
    save_csv(rows, csv_file)

    print(f"\nOK! {len(rows)} repositórios salvos em: {csv_file}")


if __name__ == "__main__":
    main()
