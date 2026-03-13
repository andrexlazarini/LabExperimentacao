"""
LAB01S03 - Análise e visualização dos dados dos 1000 repositórios mais estrelados.
Gera estatísticas (medianas) para as RQs e figuras para o relatório.
Funciona sem pandas; matplotlib é opcional (apenas para gerar os PDFs).
"""
import csv
import os
import statistics
from collections import Counter
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "top_1000_repos_github.csv")
FIG_DIR = os.path.join(BASE_DIR, "docs", "figuras")


def load_and_prepare():
    """Carrega o CSV e retorna lista de dicts com colunas derivadas."""
    now = datetime.now(timezone.utc)
    rows = []
    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            created = datetime.fromisoformat(r["createdAt"].replace("Z", "+00:00"))
            updated = datetime.fromisoformat(r["updatedAt"].replace("Z", "+00:00"))
            r["idade_anos"] = (now - created).days / 365.25
            r["dias_desde_atualizacao"] = (now - updated).days
            r["language"] = r["language"].strip() if r["language"].strip() else "Sem linguagem"
            r["mergedPRs"] = int(r["mergedPRs"])
            r["releases"] = int(r["releases"])
            r["issues_total"] = int(r["issues_total"])
            r["issues_closed_ratio"] = float(r["issues_closed_ratio"])
            rows.append(r)
    return rows


def median_of(data, key):
    return statistics.median([r[key] for r in data])


def print_summary(data):
    """Imprime resumo das medianas para cada RQ."""
    print("=" * 60)
    print("RESUMO PARA O RELATÓRIO (medianas)")
    print("=" * 60)

    print(f"\nRQ01 - Idade do repositório (anos): mediana = {median_of(data, 'idade_anos'):.2f}")
    print(f"RQ02 - Total de PRs aceitas: mediana = {median_of(data, 'mergedPRs'):.0f}")
    print(f"RQ03 - Total de releases: mediana = {median_of(data, 'releases'):.0f}")
    print(f"RQ04 - Dias desde a última atualização: mediana = {median_of(data, 'dias_desde_atualizacao'):.1f}")

    print("\nRQ05 - Contagem por linguagem (top 15):")
    lang_counts = Counter(r["language"] for r in data)
    for lang, count in lang_counts.most_common(15):
        print(f"  {lang}: {count}")

    with_issues = [r for r in data if r["issues_total"] > 0]
    med_ratio = median_of(data, "issues_closed_ratio")
    med_ratio_ci = statistics.median([r["issues_closed_ratio"] for r in with_issues]) if with_issues else 0
    print(f"\nRQ06 - Razão issues fechadas/total: mediana (todos) = {med_ratio:.3f}")
    print(f"       mediana (repos com issues) = {med_ratio_ci:.3f}")

    print("\nRQ07 (Bônus) - Linguagens populares vs outras:")
    print_rq07_summary(data)
    print("\n" + "=" * 60)


def get_populares_vs_outras(data, top_n=5):
    """Separa em linguagens populares (top N) vs outras."""
    lang_counts = Counter(r["language"] for r in data)
    linguagens_populares = set(lang for lang, _ in lang_counts.most_common(top_n))
    pop = [r for r in data if r["language"] in linguagens_populares]
    outras = [r for r in data if r["language"] not in linguagens_populares]
    return pop, outras, linguagens_populares


def print_rq07_summary(data):
    top_n = 5
    pop, outras, linguagens_populares = get_populares_vs_outras(data, top_n)
    print(f"  Linguagens populares (top {top_n}): {sorted(linguagens_populares)}")
    print(f"  Repositórios em linguagens populares: {len(pop)}")
    print(f"  Repositórios em outras linguagens: {len(outras)}")
    print()
    print("  Mediana PRs aceitas:     Populares = {:.0f}  |  Outras = {:.0f}".format(
        median_of(pop, "mergedPRs"), median_of(outras, "mergedPRs")))
    print("  Mediana releases:        Populares = {:.0f}  |  Outras = {:.0f}".format(
        median_of(pop, "releases"), median_of(outras, "releases")))
    print("  Mediana dias sem atual.: Populares = {:.1f}  |  Outras = {:.1f}".format(
        median_of(pop, "dias_desde_atualizacao"), median_of(outras, "dias_desde_atualizacao")))
    print("  (Menor dias = mais atualizados)")


# ---- Gráficos (requerem apenas matplotlib, não pandas) ----

def _hist(ax, values, median_val, xlabel, title, med_label):
    import matplotlib.pyplot as plt
    ax.hist(values, bins=30, color="steelblue", edgecolor="white")
    ax.axvline(median_val, color="red", linestyle="--", label=med_label)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Frequência")
    ax.set_title(title)
    ax.legend()


def plot_rq01_age(data):
    import matplotlib.pyplot as plt
    vals = [r["idade_anos"] for r in data]
    fig, ax = plt.subplots(figsize=(7, 4))
    _hist(ax, vals, statistics.median(vals), "Idade (anos)", "RQ01 - Idade dos repositórios",
          f"Mediana = {statistics.median(vals):.1f} anos")
    plt.tight_layout()
    return fig


def plot_rq02_merged_prs(data):
    import matplotlib.pyplot as plt
    vals = [r["mergedPRs"] for r in data]
    fig, ax = plt.subplots(figsize=(7, 4))
    _hist(ax, vals, statistics.median(vals), "Pull requests aceitas", "RQ02 - Distribuição de PRs aceitas",
          f"Mediana = {statistics.median(vals):.0f}")
    plt.tight_layout()
    return fig


def plot_rq03_releases(data):
    import matplotlib.pyplot as plt
    vals = [r["releases"] for r in data]
    fig, ax = plt.subplots(figsize=(7, 4))
    _hist(ax, vals, statistics.median(vals), "Total de releases", "RQ03 - Distribuição de releases",
          f"Mediana = {statistics.median(vals):.0f}")
    plt.tight_layout()
    return fig


def plot_rq04_days_since_update(data):
    import matplotlib.pyplot as plt
    vals = [r["dias_desde_atualizacao"] for r in data]
    fig, ax = plt.subplots(figsize=(7, 4))
    _hist(ax, vals, statistics.median(vals), "Dias desde a última atualização",
          "RQ04 - Tempo desde a última atualização", f"Mediana = {statistics.median(vals):.0f} dias")
    plt.tight_layout()
    return fig


def plot_rq05_languages(data):
    import matplotlib.pyplot as plt
    lang_counts = Counter(r["language"] for r in data)
    top15 = lang_counts.most_common(15)
    langs = [t[0] for t in reversed(top15)]
    counts = [t[1] for t in reversed(top15)]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(langs, counts, color="steelblue", edgecolor="gray", linewidth=0.5)
    ax.set_xlabel("Quantidade de repositórios")
    ax.set_ylabel("Linguagem primária")
    ax.set_title("RQ05 - Distribuição por linguagem (top 15)")
    plt.tight_layout()
    return fig


def plot_rq06_ratio(data):
    import matplotlib.pyplot as plt
    with_issues = [r for r in data if r["issues_total"] > 0]
    if not with_issues:
        return None
    vals = [r["issues_closed_ratio"] for r in with_issues]
    fig, ax = plt.subplots(figsize=(7, 4))
    _hist(ax, vals, statistics.median(vals), "Razão (issues fechadas / total)",
          "RQ06 - Percentual de issues fechadas", f"Mediana = {statistics.median(vals):.2f}")
    plt.tight_layout()
    return fig


def plot_rq07_by_language(data):
    import matplotlib.pyplot as plt
    lang_counts = Counter(r["language"] for r in data)
    top_langs = [lang for lang, _ in lang_counts.most_common(8)]
    sub = [r for r in data if r["language"] in top_langs]

    def med_by_lang(key):
        by_lang = {}
        for lang in top_langs:
            vals = [r[key] for r in sub if r["language"] == lang]
            by_lang[lang] = statistics.median(vals) if vals else 0
        return [by_lang[lang] for lang in top_langs]

    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    x = range(len(top_langs))
    axes[0].bar(x, med_by_lang("mergedPRs"), color="steelblue", edgecolor="gray")
    axes[0].set_xticks(x); axes[0].set_xticklabels(top_langs, rotation=45, ha="right")
    axes[0].set_ylabel("PRs aceitas"); axes[0].set_title("Mediana de PRs aceitas")
    axes[1].bar(x, med_by_lang("releases"), color="seagreen", edgecolor="gray")
    axes[1].set_xticks(x); axes[1].set_xticklabels(top_langs, rotation=45, ha="right")
    axes[1].set_ylabel("Releases"); axes[1].set_title("Mediana de releases")
    axes[2].bar(x, med_by_lang("dias_desde_atualizacao"), color="coral", edgecolor="gray")
    axes[2].set_xticks(x); axes[2].set_xticklabels(top_langs, rotation=45, ha="right")
    axes[2].set_ylabel("Dias"); axes[2].set_title("Mediana de dias desde última atualização")
    fig.suptitle("RQ07 (Bônus) - Métricas por linguagem (top 8)", fontsize=12, y=1.02)
    plt.tight_layout()
    return fig


def plot_rq07_populares_vs_outras(data):
    import matplotlib.pyplot as plt
    pop, outras, _ = get_populares_vs_outras(data, 5)
    fig, axes = plt.subplots(1, 3, figsize=(11, 4))
    grupos = ["Linguagens\npopulares (top 5)", "Outras\nlinguagens"]
    cores = ["steelblue", "coral"]
    axes[0].bar(grupos, [median_of(pop, "mergedPRs"), median_of(outras, "mergedPRs")], color=cores, edgecolor="gray")
    axes[0].set_ylabel("Mediana de PRs aceitas"); axes[0].set_title("RQ02 por tipo de linguagem")
    axes[1].bar(grupos, [median_of(pop, "releases"), median_of(outras, "releases")], color=cores, edgecolor="gray")
    axes[1].set_ylabel("Mediana de releases"); axes[1].set_title("RQ03 por tipo de linguagem")
    axes[2].bar(grupos, [median_of(pop, "dias_desde_atualizacao"), median_of(outras, "dias_desde_atualizacao")],
                color=cores, edgecolor="gray")
    axes[2].set_ylabel("Mediana (dias)"); axes[2].set_title("RQ04 por tipo de linguagem\n(menor = mais atualizado)")
    fig.suptitle("RQ07 (Bônus) - Comparação: linguagens populares vs outras", fontsize=12, y=1.02)
    plt.tight_layout()
    return fig


def main():
    if not os.path.exists(CSV_PATH):
        print(f"Arquivo não encontrado: {CSV_PATH}")
        print("Execute primeiro lab01.py para gerar o CSV.")
        return

    os.makedirs(FIG_DIR, exist_ok=True)
    data = load_and_prepare()
    print_summary(data)

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        for name, plot_fn in [
            ("rq01_idade.pdf", plot_rq01_age),
            ("rq02_merged_prs.pdf", plot_rq02_merged_prs),
            ("rq03_releases.pdf", plot_rq03_releases),
            ("rq04_dias_atualizacao.pdf", plot_rq04_days_since_update),
            ("rq05_linguagens.pdf", plot_rq05_languages),
            ("rq06_issues_ratio.pdf", plot_rq06_ratio),
            ("rq07_por_linguagem.pdf", plot_rq07_by_language),
            ("rq07_populares_vs_outras.pdf", plot_rq07_populares_vs_outras),
        ]:
            fig = plot_fn(data)
            if fig is not None:
                fig.savefig(os.path.join(FIG_DIR, name), bbox_inches="tight")
                plt.close(fig)

        print(f"\nFiguras salvas em: {FIG_DIR}")
    except ImportError:
        print("\nPara gerar as figuras, instale apenas matplotlib: pip install matplotlib")


if __name__ == "__main__":
    main()
