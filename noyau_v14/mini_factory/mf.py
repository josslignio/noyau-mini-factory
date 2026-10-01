"""Mini-factory séquentielle minimale (arbitrage CTO D4 ; STRATEGIE_NOYAU_MINI_FACTORY §4). Une file persistante, UN travail actif, un appel au noyau
par pas, démarrage compté sur disque AVANT l'appel, aucune relance d'une issue inconnue, aide exploitable. Pas une plateforme : ni service, ni concurrence.
Usage : mf.py ajouter ID --projet P --jalon M [--moteur glm] [--essais 2] | mf.py suivant
      | mf.py regler ID pret|bloque --raison T | mf.py statut — ajouter/suivant exigent MF_NOYAU (… run.py)"""
import argparse, contextlib, fcntl, hashlib, json, os, re, shlex, subprocess, sys, time, types
from pathlib import Path

ETAT = Path(os.environ.get("MF_ETAT", Path.home() / ".mini_factory")); FILE = ETAT / "file.json"
NOYAU = shlex.split(os.environ.get("MF_NOYAU", ""))  # C:A13 : aucun défaut (ajouter/suivant : refus rc 3)
FICHIERS = ("run.py", "support.py", "juge_isole.py", "bornage.sb", "ENGINES.lock", "CONSIGNE.md.tmpl")  # + moteurs/
MF_SHA = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()  # R3 : le programme qui accepte les reçus
DELAI_S = 6 * 5400  # v9 : > moteur + 4 passes de suite (5 × BUDGET_MAX 5400 de run.py) + 5400 de marge (git, arrêts)
RELIES = set(filter(None, os.environ.get("MF_MOTEURS_RELIES", "").split(",")))   # D3 : moteurs dont compte mesuré = compte débité est ÉTABLI
VERDICTS = {"VERT": "accepte", "ROUGE": "a_corriger", "REFUS": "bloque"}         # tout le reste (ABORT, RUNNING, absent, illisible) = inconnu
TRANS = {"inconnu": ("pret", "bloque"), "bloque": ("pret", "bloque"), "pret": ("bloque",)}  # v10 : sortir un "pret" jamais lancé ; "en_cours" toujours hors de portée

def lire():
    return json.loads(FILE.read_text()) if FILE.exists() else {}

def ecrire(F):
    ETAT.mkdir(parents=True, exist_ok=True)
    tmp = FILE.with_suffix(".tmp")
    with open(tmp, "w") as f:
        f.write(json.dumps(F, indent=1, ensure_ascii=False)); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, FILE)

def sha_noyau():
    """B:9/R2 : empreinte des SEULS fichiers exécutés ou consommés par le noyau (ni README, ni sauvegarde)."""
    d, h = Path(NOYAU[-1]).resolve().parent, hashlib.sha256()
    for f in [d / n for n in FICHIERS] + sorted((d / "moteurs").glob("*.json")):
        h.update(f"{f.relative_to(d).as_posix()}\0{hashlib.sha256(f.read_bytes()).hexdigest()}\n".encode())
    return h.hexdigest()

def hash_contrat(t):
    """Empreinte du contrat calculée par le noyau lui-même (--hash-contrat) ; None si illisible ou hors délai."""
    argv = NOYAU + ["--hash-contrat", "--project", t["projet"], "--milestone", t["jalon"]]
    with contextlib.suppress(subprocess.TimeoutExpired):
        p = subprocess.run(argv, capture_output=True, text=True, timeout=120)
        return p.stdout.strip() if p.returncode == 0 and re.fullmatch(r"[0-9a-f]{64}", p.stdout.strip()) else None

def aide(t, blocage, choix):
    print(f"AIDE travail={t['id']} jalon={t['jalon']} moteur={t['moteur']} état={t['etat']} démarrages={len(t['demarrages'])}/{t['essais']} "
          f"dernier={t.get('dernier')} coût=inconnu s'il n'est pas dans le reçu\n  blocage : {blocage}\n  choix demandé : {choix}")
    return 2

def recevable(R, t, recu, rc):
    """Schéma, types, jalon, rc, dossier = run_uuid, contrat épinglé ; jamais test-only ; VERT = rc 0 ET commit."""
    ok = isinstance(R, dict) and R.get("schema") == "factory-v3-receipt/3" and R.get("milestone") == t["jalon"]
    ok = ok and isinstance(R.get("verdict"), str) and isinstance(R.get("run_uuid"), str)  # R3 : types
    ok = ok and all(isinstance(R.get(k) or {}, dict) for k in ("noyau", "commit", "engine"))
    ok = ok and R.get("rc") == rc and bool(R.get("run_uuid")) and Path(recu).parent.name == R["run_uuid"]
    ok = ok and R.get("hash_contrat") == t.get("hash_contrat")
    ok = ok and "test_only" not in ((R.get("noyau") or {}).get("flags") or [])
    return ok and (R.get("verdict") != "VERT" or (rc == 0 and bool((R.get("commit") or {}).get("sha"))))

def lancer(t, F, h):
    t["demarrages"].append({"t": time.strftime("%F %T"), "noyau": h, "mf": MF_SHA, "moteur": t["moteur"]})
    t["etat"] = "en_cours"
    ecrire(F)  # compté AVANT l'appel
    argv = NOYAU + ["--project", t["projet"], "--milestone", t["jalon"], "--engine", t["moteur"]]
    try:  # R3 : appel borné ; au délai, subprocess.run ne tue que son enfant direct
        p = subprocess.run(argv, capture_output=True, text=True, timeout=DELAI_S)
    except subprocess.TimeoutExpired:
        p = types.SimpleNamespace(returncode=None, stdout="")
    recu = ([mo.group(1) for mo in re.finditer(r"(?m)^\[v3\] reçu (\S+)$", p.stdout)] or [None])[-1]  # B:1
    R = None
    with contextlib.suppress(OSError, ValueError, TypeError, AttributeError, KeyError):  # R2/R3 : illisible, mal typé
        lu = json.loads(Path(recu).read_text())
        R = lu if recevable(lu, t, recu, p.returncode) and sha_noyau() == h else None  # noyau changé pendant l'appel
    v = R and R.get("verdict")
    cout = R and (R.get("engine") or {}).get("cost_usd")
    t["dernier"] = {"rc": p.returncode, "verdict": v, "recu": recu, "cout_usd": cout}
    t["etat"] = VERDICTS.get(v, "inconnu")
    if v == "ABORT" and R.get("motif_echec") == "panne_moteur":  # CORR_7 : panne ≠ échec du travail
        t["demarrages"][-1]["technique"] = True
        t["etat"] = "pret" if sum(1 for d in t["demarrages"] if d.get("technique")) < 3 else "bloque"  # CORR_8 : la 3e bloque
    if t["etat"] == "accepte":
        t["preuve"] = {"recu": recu, "run_uuid": R["run_uuid"], "noyau": h, "mf": MF_SHA, "base_sha": R.get("base_sha"),
                       "commit": R["commit"]["sha"], "repo": R.get("repo")}
    if t["etat"] == "a_corriger":
        t["etat"] = "pret" if sum(1 for d in t["demarrages"] if not d.get("technique")) < t["essais"] else "bloque"
    ecrire(F)
    print(f"{t['id']} {t['jalon']} → {v} ({t['etat']}) reçu={t['dernier']['recu']}")
    blocage = f"issue {v or 'sans reçu valide'}"
    blocage += f" (noyau hors délai : {DELAI_S} s)" if p.returncode is None else ""
    return 0 if t["etat"] in ("accepte", "pret") else aide(t, blocage, "examiner le reçu puis `mf.py regler`")

def suivant(F):
    if not Path(NOYAU[-1]).is_file():
        return print(f"REFUS : noyau introuvable ({NOYAU[-1]}) — aucun démarrage") or 3
    for t in F.values():
        if t["etat"] == "en_cours":                            # verrou tenu ici : un « en_cours » est orphelin (pilote mort pendant un appel)
            t["etat"] = "inconnu"; ecrire(F)
        if t["etat"] in ("en_cours", "inconnu"):
            return aide(t, f"travail {t['etat']} : un seul travail actif ; issue à réconcilier avant toute suite", "examiner puis `mf.py regler`")
    h = sha_noyau()  # une fois par appel
    for t in F.values():
        if t["etat"] != "pret":
            continue
        if t.get("apres"):  # v9 Q1(1) : --apres retiré ; toute file existante non vide est REFUSÉE, jamais ignorée
            return aide(t, f"champ 'apres'={t['apres']!r} non vide (retiré, v9)", "migrer la file (retirer 'apres')")
        t["moteur"] = os.environ.get("MF_MOTEUR_FORCE") or t["moteur"]   # repli propriétaire 28/09 « quand GLM est mort, switch sur Claude » : moteur écrit au travail, tracé au démarrage
        if t["moteur"] not in RELIES:
            return aide(t, f"compte mesuré non relié au compte débité pour le moteur {t['moteur']} (D3)", "établir le lien puis l'ajouter à MF_MOTEURS_RELIES")
        if sum(1 for d in t["demarrages"] if not d.get("technique")) >= t["essais"]:
            t["etat"] = "bloque"; ecrire(F); return aide(t, "plafond de tentatives atteint", "décider : arrêt ou nouveau contrat")
        if hash_contrat(t) != t.get("hash_contrat"):  # B:9 : contrat épinglé à l'ajout ; changé/illisible = refus
            return aide(t, f"contrat changé depuis l'ajout ({t.get('hash_contrat')})", "nouveau travail")
        return lancer(t, F, h)
    return aide({"id": "-", "jalon": "-", "moteur": "-", "etat": "rien", "demarrages": [], "essais": 0}, "aucun travail prêt", "ajouter ou régler un travail")

def main(argv=None):
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("ajouter"); a.add_argument("id")
    for o, k in (("--projet", {"required": True}), ("--jalon", {"required": True}), ("--moteur", {"default": "glm"}),
                 ("--essais", {"type": int, "default": 2})):
        a.add_argument(o, **k)
    r = sub.add_parser("regler"); r.add_argument("id"); r.add_argument("vers", choices=("pret", "bloque")); r.add_argument("--raison", required=True)
    sub.add_parser("suivant"); sub.add_parser("statut")
    x = ap.parse_args(argv)
    if x.cmd in ("ajouter", "suivant") and not NOYAU:
        return print("REFUS : MF_NOYAU obligatoire (commande du noyau, chemin de run.py en dernier)") or 3
    ETAT.mkdir(parents=True, exist_ok=True)
    with open(ETAT / "verrou", "w") as v:
        try:
            fcntl.flock(v, fcntl.LOCK_EX | fcntl.LOCK_NB)      # un seul écrivain ; libéré par le système si le processus meurt
        except OSError:
            return print("REFUS : une autre mini-factory tourne sur cet état") or 3
        F = lire()
        if x.cmd == "ajouter":
            if x.id in F:
                return print("REFUS : identifiant déjà présent") or 3
            F[x.id] = {"id": x.id, "projet": x.projet, "jalon": x.jalon, "moteur": x.moteur, "essais": x.essais,
                       "etat": "pret", "demarrages": [], "reglages": []}
            if not (hc := hash_contrat(F[x.id])):
                return print("REFUS : empreinte du contrat illisible (--hash-contrat du noyau)") or 3
            F[x.id]["hash_contrat"] = hc
            return ecrire(F) or 0
        if x.cmd == "regler":
            if x.id not in F:
                return print(f"REFUS : travail inconnu : {x.id}") or 3
            t = F[x.id]
            if x.vers not in TRANS.get(t["etat"], ()):
                return print(f"REFUS : {x.id} est {t['etat']}, transition vers {x.vers} interdite") or 3
            t["reglages"].append({"t": time.strftime("%F %T"), "de": t["etat"], "vers": x.vers, "raison": x.raison}); t["etat"] = x.vers
            return ecrire(F) or 0                                # les démarrages déjà comptés ne sont JAMAIS remis à zéro
        if x.cmd == "statut":
            return print(json.dumps(F, indent=1, ensure_ascii=False)) or 0
        return suivant(F)

if __name__ == "__main__":
    sys.exit(main())
