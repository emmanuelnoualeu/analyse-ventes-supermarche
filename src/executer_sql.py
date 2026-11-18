"""Exécute les scripts SQL du dossier sql/ avec DuckDB et enregistre chaque résultat en CSV.

    python src/executer_sql.py
"""
import re
from pathlib import Path
import duckdb

RACINE = Path(__file__).resolve().parents[1]


def requetes(fichier):
    """Découpe un script en (titre, requête) ; le titre est le dernier commentaire '-- ' rencontré."""
    titre, morceaux = None, []
    for bloc in fichier.read_text(encoding="utf-8").split(";"):
        lignes = [l for l in bloc.strip().splitlines()]
        coms = [l[2:].strip() for l in lignes if l.strip().startswith("--") and not set(l.strip()) <= {"-", "="}]
        sql = "\n".join(l for l in lignes if not l.strip().startswith("--")).strip()
        if coms:
            titre = coms[-1]
        if sql:
            morceaux.append((titre, sql))
    return morceaux


def main():
    con = duckdb.connect()
    sortie = RACINE / "resultats"
    sortie.mkdir(exist_ok=True)
    import os
    os.chdir(RACINE)
    n = 0
    for f in sorted((RACINE / "sql").glob("*.sql")):
        for titre, sql in requetes(f):
            res = con.execute(sql)
            if res.description is None or sql.upper().startswith("CREATE"):
                continue
            df = res.df()
            n += 1
            code = re.match(r"(Q\d+|Contrôle \d+)", titre or "").group(1) if titre and re.match(r"(Q\d+|Contrôle \d+)", titre) else f"R{n}"
            nom = code.lower().replace("ô", "o").replace(" ", "_")
            df.to_csv(sortie / f"{nom}.csv", index=False)
            print(f"\n=== {titre}\n{df.to_string(index=False)}")
    return con


if __name__ == "__main__":
    main()
