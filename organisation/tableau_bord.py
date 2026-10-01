#!/usr/bin/env python3
"""TABLEAU DE BORD QUOTIDIEN (propriétaire 01/10) — machine seule, depuis les reçus : par produit, étapes réglées, réussite du 1er coup,
minutes et jetons par étape réglée, comparaison noyau / IA seule (OMBRE.jsonl), quotas. Écrit ~/Obsidian/Factory/TABLEAU_DE_BORD.md."""
import glob, json, os, re, subprocess, time, collections
B = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(os.path.dirname(B)); jour = time.strftime("%Y-%m-%d")
tok = lambda f: sum(int(x) for l in open(f, errors="ignore") for x in re.findall(r'"(?:input|output|reasoning)":(\d+)', l)) if os.path.exists(f) else 0
L = [f"# Tableau de bord — {time.strftime('%d/%m/%Y %H:%M')} (machine, depuis les reçus)", "",
     "| Produit | Étapes réglées (total) | dont aujourd'hui | Constructions | Réussite 1er essai | Minutes / étape réglée | Jetons / étape réglée |", "|---|---|---|---|---|---|---|"]
for mf in sorted(glob.glob(f"{B}/*/mf_etat/file.json")):
    P = mf.split("/")[-3]
    if os.path.exists(f"{B}/{P}/ARRET"): continue
    F = json.load(open(mf)); acc = [k for k, v in F.items() if v.get("etat") == "accepte"]
    runs = [os.path.dirname(f) for f in glob.glob(f"{B}/{P}/copie/.factory_v3/runs/*/RECEIPT.json") if os.path.exists(os.path.dirname(f) + "/CONSIGNE.md")]
    rec = [(r, json.load(open(r + "/RECEIPT.json"))) for r in runs]; vert = [(r, x) for r, x in rec if x.get("verdict") == "VERT"]
    par = collections.defaultdict(list)
    for r, x in sorted(rec, key=lambda t: t[1].get("started_at") or ""): par[x.get("milestone")].append(x.get("verdict"))
    premier = sum(1 for v in par.values() if v and v[0] == "VERT"); auj = sum(1 for r, x in vert if (x.get("finished_at") or "").startswith(jour))
    m = sum((x.get("t_wall_total") or 0) for _, x in rec) / 60 / max(len(vert), 1); t = sum(tok(r + "/engine.log") for r, _ in rec) / max(len(vert), 1)
    L.append(f"| {P} | {len(acc)} | {auj} | {len(rec)} | {premier}/{len(par)} | {m:.0f} | {t:,.0f} |".replace(",", " "))
O = [json.loads(l) for l in open(f"{B}/OMBRE.jsonl")] if os.path.exists(f"{B}/OMBRE.jsonl") else []
MS = {json.loads(l)["id"]: json.loads(l)["msa"] for l in open(f"{B}/OMBRE_MSA.jsonl")} if os.path.exists(f"{B}/OMBRE_MSA.jsonl") else {}
L += ["", f"## Noyau contre IA seule ({len(O)} étapes comparées, même juge, même isolement)", "", "| Étape | Noyau (verdicts, min, jetons) | IA seule (réussis/total, min, jetons) | mini-swe-agent (réussis/total, min) |", "|---|---|---|---|"]
L += [f"| {o['produit']}/{o['id']} | {','.join(map(str, o['noyau']['verdicts']))}, {o['noyau']['minutes']}, {o['noyau']['tokens']} | {o['seul']['reussis']}/{o['seul']['total']}, {o['seul']['minutes']}, {o['seul']['tokens']} | {(lambda m: f"{m['reussis']}/{m['total']}, {m['minutes']}" if m else '—')(MS.get(o['id']))} |" for o in O]
q = subprocess.run(["python3", f"{R}/factory_v2/quota_live.py"], capture_output=True, text=True).stdout
L += ["", "Quotas : " + " ; ".join(f"{e} {p} %" for e, p in re.findall(r"^  (\w+).*?\n(?:.*\n)*?\s+(?:seven_day|weekly)\s+utilisé\s+([\d.]+)", q, re.M))]
open(os.path.expanduser("~/Obsidian/Factory/TABLEAU_DE_BORD.md"), "w").write("\n".join(L) + "\n"); print("\n".join(L))
