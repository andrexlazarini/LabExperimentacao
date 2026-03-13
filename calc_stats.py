"""Calcula medianas e contagens do CSV sem pandas (apenas stdlib)."""
import csv
import statistics
from datetime import datetime, timezone
from collections import Counter

CSV_PATH = "top_1000_repos_github.csv"

with open(CSV_PATH, encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

now = datetime.now(timezone.utc)
idades = []
dias_atualizacao = []
merged_prs = []
releases = []
languages = []
issues_ratio = []
issues_ratio_com_issues = []

for r in rows:
    created = datetime.fromisoformat(r["createdAt"].replace("Z", "+00:00"))
    updated = datetime.fromisoformat(r["updatedAt"].replace("Z", "+00:00"))
    idades.append((now - created).days / 365.25)
    dias_atualizacao.append((now - updated).days)
    merged_prs.append(int(r["mergedPRs"]))
    releases.append(int(r["releases"]))
    lang = r["language"].strip() if r["language"].strip() else "Sem linguagem"
    languages.append(lang)
    ratio = float(r["issues_closed_ratio"])
    issues_ratio.append(ratio)
    if int(r["issues_total"]) > 0:
        issues_ratio_com_issues.append(ratio)

print("MEDIANAS:")
print("  Idade (anos):", round(statistics.median(idades), 2))
print("  PRs aceitas:", round(statistics.median(merged_prs), 0))
print("  Releases:", round(statistics.median(releases), 0))
print("  Dias desde atualização:", round(statistics.median(dias_atualizacao), 1))
print("  Razão issues fechadas (todos):", round(statistics.median(issues_ratio), 3))
print("  Razão issues fechadas (com issues):", round(statistics.median(issues_ratio_com_issues), 3))

print("\nCONTAGEM POR LINGUAGEM (top 15):")
for lang, count in Counter(languages).most_common(15):
    print(f"  {lang}: {count}")

# RQ07: top 5 linguagens vs outras
top5 = set(lang for lang, _ in Counter(languages).most_common(5))
pr_pop, pr_out = [], []
rel_pop, rel_out = [], []
dias_pop, dias_out = [], []
for i, r in enumerate(rows):
    pr = int(r["mergedPRs"])
    rel = int(r["releases"])
    created = datetime.fromisoformat(r["createdAt"].replace("Z", "+00:00"))
    updated = datetime.fromisoformat(r["updatedAt"].replace("Z", "+00:00"))
    dias = (now - updated).days
    lang = r["language"].strip() if r["language"].strip() else "Sem linguagem"
    if lang in top5:
        pr_pop.append(pr); rel_pop.append(rel); dias_pop.append(dias)
    else:
        pr_out.append(pr); rel_out.append(rel); dias_out.append(dias)

print("\nRQ07 - Linguagens populares (top 5):", sorted(top5))
print("  Mediana PRs - Populares:", round(statistics.median(pr_pop), 0), "| Outras:", round(statistics.median(pr_out), 0))
print("  Mediana Releases - Populares:", round(statistics.median(rel_pop), 0), "| Outras:", round(statistics.median(rel_out), 0))
print("  Mediana dias atual. - Populares:", round(statistics.median(dias_pop), 1), "| Outras:", round(statistics.median(dias_out), 1))
