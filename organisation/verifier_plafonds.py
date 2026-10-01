"""PLAFONDS À CLIQUET (propriétaire 28/09 : « encadrer et limiter le code pour ne pas se faire surprendre »).
Chaque pièce a un plafond de lignes = sa taille au jour de la pose. Plus grand → rc 3 (la chaîne refuse de démarrer). Plus petit → le plafond
DESCEND tout seul (jamais il ne remonte : le relever est une décision propriétaire écrite dans PLAFONDS.json, champ "releve"). Aucune dépendance."""
import json, sys
from pathlib import Path
B = Path(__file__).resolve().parent; P = B / "PLAFONDS.json"; d = json.loads(P.read_text()); trop, baisse = [], ["pose des lignes longues"] if "longues_160" not in d else []; lg = d.setdefault("longues_160", {})
for rel, cap in d["pieces"].items():   # 28/09 : lignes > 160 car. comptées à part (la recherche l'avait dit : un plafond de lignes pousse à tasser)
    L = open(B.parent / rel, "rb").read().splitlines(); n, k = len(L), sum(len(x.decode("utf-8", "replace")) > 160 for x in L); lg.setdefault(rel, k)
    if n > cap or k > lg[rel]: trop.append(f"{rel} {n} > {cap}" if n > cap else f"{rel} lignes longues {k} > {lg[rel]}")
    elif n < cap or k < lg[rel]: baisse.append(f"{rel} {cap}/{lg[rel]} → {n}/{k}"); d["pieces"][rel], lg[rel] = n, k
tot = sum(d["pieces"].values())
if tot > d["total"]: trop.append(f"TOTAL {tot} > {d['total']}")
elif tot < d["total"] and not trop: baisse.append(f"TOTAL {d['total']} → {tot}"); d["total"] = tot
if baisse and not trop: P.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n")
print(("PLAFOND DÉPASSÉ : " + " ; ".join(trop)) if trop else f"plafonds OK (total {tot}/{d['total']})" + (f" — cliquet : {' ; '.join(baisse)}" if baisse else ""))
sys.exit(3 if trop else 0)
