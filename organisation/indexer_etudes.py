#!/usr/bin/env python3
"""Banque d'études (propriétaire 30/09) : range par produit toutes les études (liens) et écrit INDEX.md — machine seule, aucune IA."""
import pathlib, re, time
X = pathlib.Path(__file__).resolve().parents[1]; B = X / "BANQUE_ETUDES"
PRODUITS = {"noyau_mini_factory": ["ETUDE_STACK", "ETAT_ART_PI", "ETAT_ART_LECUN_JEV", "ETAT_ART_POCOCK", "ETAT_ART_HERMES", "HARNAIS_MARCHE_20260927",
                                   "RADAR/ETAT_ART_BRIQUES", "RADAR/ETAT_ART_OUTILS", "VIDEOS_YT"],
            "pepita_video": ["TIKTOK/ETAT_ART", "TIKTOK/BENCHMARK_OUTILS", "TIKTOK/RECHERCHE_V2", "ETAT_ART_HIGGSFIELD"],
            "pepita_seo": ["SEO/ETAT_ART", "SEO/ETAT_ART/V2", "SEO/DIFFUSION"],
            "mailbox_cleaner": ["INBOX_CLEAN", "INBOX_CLEAN/ETAT_ART"],
            "savespace_drive": ["DISK_CLEAN", "DISK_CLEAN/ETAT_ART"]}
L = [f"# Banque d'études — index régénéré par machine le {time.strftime('%d/%m/%Y %H:%M')}", "",
     "Chaque dossier est un lien vers l'étude d'origine. Les verdicts « À PRENDRE » ne sont appliqués qu'après relecture Codex groupée.", ""]
for p, dirs in PRODUITS.items():
    (B / p).mkdir(parents=True, exist_ok=True); L += [f"## {p}", ""]
    for d in dirs:
        s = X / d
        if not s.is_dir(): continue
        lien = B / p / d.replace("/", "__")
        if not lien.exists(): lien.symlink_to(s)
        for f in sorted(s.glob("*.md")):
            t = f.read_text(errors="ignore"); prendre = len(re.findall(r"(?i)\bà prendre\b|\bPRENDRE\b", t))
            L.append(f"- `{d}/{f.name}` — {t.count(chr(10))} l., modifié {time.strftime('%d/%m %H:%M', time.localtime(f.stat().st_mtime))}, mentions PRENDRE : {prendre}")
    L.append("")
(B / "INDEX.md").write_text("\n".join(L) + "\n"); print(B / "INDEX.md", len(L), "lignes")
