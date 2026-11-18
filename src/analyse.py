"""
Analyse des ventes : tests statistiques, figures du README et données du tableau de bord.

    python src/executer_sql.py   # requêtes SQL -> resultats/*.csv
    python src/analyse.py        # tests + figures + dashboard/donnees.js
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

RACINE = Path(__file__).resolve().parents[1]
RAYONS = {"Health and beauty": "Santé et beauté", "Home and lifestyle": "Maison",
          "Fashion accessories": "Mode", "Electronic accessories": "Électronique",
          "Sports and travel": "Sport et voyage", "Food and beverages": "Alimentation"}
JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
PAIEMENT = {"Cash": "Espèces", "Credit card": "Carte bancaire", "Ewallet": "Portefeuille mobile"}
BLEU, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, GRILLE = "#0b0b0b", "#52514e", "#e6e5e1"
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "font.size": 10,
                     "axes.edgecolor": INK2, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.titleweight": "bold", "axes.titlelocation": "left",
                     "axes.titlesize": 11})


def charger():
    d = pd.read_csv(RACINE / "data/ventes_supermarche.csv")
    d["date"] = pd.to_datetime(d["Date"], format="%m/%d/%Y")
    d["heure"] = d["Time"].str[:2].astype(int)
    d["jour"] = d["date"].dt.dayofweek
    d["rayon"] = d["Product line"].map(RAYONS)
    d["paiement"] = d["Payment"].map(PAIEMENT)
    d["magasin"] = d["Branch"] + " – " + d["City"]
    return d


def tests(d):
    """Les écarts observés sont-ils plus grands que le hasard ?"""
    out = []
    g = [x.Total.values for _, x in d.groupby("Branch")]
    out.append(("Panier moyen différent selon le magasin", "Kruskal-Wallis", stats.kruskal(*g).pvalue))
    g = [x.Total.values for _, x in d.groupby("rayon")]
    out.append(("Panier moyen différent selon le rayon", "Kruskal-Wallis", stats.kruskal(*g).pvalue))
    m = d[d["Customer type"] == "Member"].Total
    n = d[d["Customer type"] == "Normal"].Total
    out.append(("Les membres dépensent plus que les non-membres", "Mann-Whitney (unilatéral)",
                stats.mannwhitneyu(m, n, alternative="greater").pvalue))
    tab = pd.crosstab(d.Branch, d.Payment)
    out.append(("Mode de paiement lié au magasin", "Khi-deux d'indépendance", stats.chi2_contingency(tab)[1]))
    jour = d.groupby("date").Total.sum()
    out.append(("CA journalier différent selon le jour de la semaine", "Kruskal-Wallis",
                stats.kruskal(*[v.values for _, v in jour.groupby(jour.index.dayofweek)]).pvalue))
    out.append(("Février plus faible (CA journalier)", "Mann-Whitney",
                stats.mannwhitneyu(jour[jour.index.month == 2], jour[jour.index.month != 2]).pvalue))
    out.append(("Le samedi fait plus de CA que les autres jours", "Mann-Whitney (unilatéral)",
                stats.mannwhitneyu(jour[jour.index.dayofweek == 5], jour[jour.index.dayofweek != 5],
                                   alternative="greater").pvalue))
    out.append(("Mix des rayons différent selon le magasin", "Khi-deux d'indépendance",
                stats.chi2_contingency(pd.crosstab(d.rayon, d.Branch))[1]))
    out.append(("Affluence non uniforme selon l'heure", "Khi-deux d'adéquation",
                stats.chisquare(d.heure.value_counts().sort_index()).pvalue))
    t = pd.DataFrame(out, columns=["Question", "Test", "p-valeur"])
    t["Conclusion (seuil 5 %)"] = np.where(t["p-valeur"] < 0.05, "Écart significatif", "Pas d'écart démontré")
    return t


def fig_rayon_magasin(d, chemin):
    piv = d.pivot_table(index="rayon", columns="Branch", values="Total", aggfunc="sum") / 1000
    piv = piv.loc[piv.sum(axis=1).sort_values().index]
    fig, ax = plt.subplots(figsize=(8.5, 4.4))
    y = np.arange(len(piv))
    h = 0.26
    for i, (b, c) in enumerate(zip(["A", "B", "C"], [BLEU, ORANGE, AQUA])):
        ax.barh(y + (i - 1) * h, piv[b], height=h - 0.03, color=c, label={"A": "A – Yangon", "B": "B – Mandalay", "C": "C – Naypyitaw"}[b])
    ax.set_yticks(y, piv.index)
    ax.set_xlabel("Chiffre d'affaires (milliers)")
    ax.xaxis.grid(True, color=GRILLE); ax.set_axisbelow(True)
    ax.set_title("Le rayon n° 1 change d'un magasin à l'autre… mais l'écart reste dans le bruit (p = 0,32)")
    ax.legend(frameon=False, fontsize=8.5, loc="lower right")
    fig.tight_layout(); fig.savefig(chemin, dpi=170); plt.close(fig)


def fig_jour_heure(d, chemin):
    piv = d.pivot_table(index="jour", columns="heure", values="Total", aggfunc="count").reindex(range(7)).fillna(0)
    fig, ax = plt.subplots(figsize=(9, 3.9))
    im = ax.imshow(piv.values, cmap="Blues", aspect="auto")
    ax.set_yticks(range(7), JOURS); ax.set_xticks(range(piv.shape[1]), [f"{h}h" for h in piv.columns])
    for s in ax.spines.values():
        s.set_visible(False)
    for i in range(7):
        for j in range(piv.shape[1]):
            v = int(piv.values[i, j])
            if v >= np.percentile(piv.values, 92):
                ax.text(j, i, v, ha="center", va="center", fontsize=8, color="white")
    ax.set_title("Tickets par jour et par heure : le samedi ressort (p = 0,03), le pic de 19 h reste à confirmer")
    fig.colorbar(im, ax=ax, shrink=0.8, label="Tickets")
    fig.tight_layout(); fig.savefig(chemin, dpi=170); plt.close(fig)


def fig_tendance(d, chemin):
    j = d.groupby("date").Total.sum()
    mm = j.rolling(7, center=True).mean()
    fig, ax = plt.subplots(figsize=(9, 3.8))
    ax.plot(j.index, j / 1000, color="#b7d3f6", lw=1, label="CA journalier")
    ax.plot(mm.index, mm / 1000, color=BLEU, lw=2.2, label="Moyenne mobile 7 jours")
    moy = d.groupby(d.date.dt.month).apply(lambda x: x.Total.sum() / x.date.nunique()) / 1000
    for mois, debut, fin in [(1, "2019-01-01", "2019-01-31"), (2, "2019-02-01", "2019-02-28"), (3, "2019-03-01", "2019-03-30")]:
        ax.hlines(moy[mois], pd.Timestamp(debut), pd.Timestamp(fin), color=ORANGE, lw=1.6, ls="--")
        ax.text(pd.Timestamp(debut) + pd.Timedelta(days=1), moy[mois] + 0.3, f"moyenne {moy[mois]*1000:,.0f} / jour".replace(",", " "),
                color=INK, fontsize=8, bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85))
    ax.set_ylabel("CA (milliers)")
    import matplotlib.dates as mdates
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
    ax.yaxis.grid(True, color=GRILLE); ax.set_axisbelow(True)
    ax.set_title("Février paraît plus faible (−7 % par jour), mais l'écart n'est pas significatif (p = 0,42)")
    ax.legend(frameon=False, fontsize=8.5, loc="upper right", ncol=2)
    fig.tight_layout(); fig.savefig(chemin, dpi=170); plt.close(fig)


def donnees_dashboard(d, chemin):
    """Données ligne à ligne (1 000 tickets) pour un tableau de bord filtrable côté navigateur."""
    lignes = [[r.Branch, r.date.strftime("%Y-%m-%d"), int(r.heure), int(r.jour), r.rayon, r.paiement,
               r["Customer type"] == "Member", round(float(r.Total), 2), int(r.Quantity), float(r.Rating if "Rating" in r else r["Customer stratification rating"])]
              for _, r in d.iterrows()]
    chemin.write_text("window.VENTES = " + json.dumps(lignes, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")


def main():
    d = charger()
    t = tests(d)
    t.to_csv(RACINE / "resultats/tests_statistiques.csv", index=False)
    print(t.to_string(index=False, formatters={"p-valeur": "{:.3f}".format}))
    fig_rayon_magasin(d, RACINE / "figures/01_ca_rayon_magasin.png")
    fig_jour_heure(d, RACINE / "figures/02_affluence_jour_heure.png")
    fig_tendance(d, RACINE / "figures/03_tendance_journaliere.png")
    donnees_dashboard(d, RACINE / "dashboard/donnees.js")
    print("Figures et données du tableau de bord générées.")


if __name__ == "__main__":
    main()
