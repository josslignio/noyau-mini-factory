"""Acceptation MÉCANIQUE d'un jalon préparé par GLM (Claude, 27/09 — autopilote, propriétaire absent).
Usage : python3 accepter_jalon.py <dossier projet> <dépôt copie> <dossier ID avec contrat.yaml> [dossier des patchs si différent]
Règles (toutes exigées, sinon REFUS — tout REFUS de la matrice précède toute écriture hors de la zone de travail dos/acceptation/) :
  base    : chaque a_faire_passer ROUGE, chaque a_garder_verts VERT ;
  honnête : tout VERT — un id sauté ou absent n'est PAS vert ;
  triches : chacune laisse au moins un id exigé ROUGE — absent, sauté ou collecte cassée ne comptent PAS comme détection ;
  patchs (honnête ET triches) : au moins un bloc reconnu et appliqué, chemins limités aux livrables du contrat, sinon REFUS ;
  livrables sans fichier de test ; tests à garder verts sans navigateur/socket/serveur (refus par mot-clé dans leur source).
Si accepté : juge déposé et commité dans la copie, contrat ajouté à ROADMAP.yaml + fichier de tâche, hash calculé par le noyau, validation
« claude_pilote_auto » (règles ci-dessus, juge rédigé par GLM : sans indépendance de famille), travail ajouté à la mini-factory. Aucun moteur lancé ici.
L'ancienne promesse d'aucune écriture après un refus était FAUSSE pour les refus noyau/mf finaux (juge, commit et roadmap déjà écrits à ce stade) :
RETIRÉE (retrait préféré à une duplication scratch du projet pour la rendre vraie) — ces refus-là disent « contrat écrit mais NON mis en file »."""
import json, os, re, shutil, subprocess, sys, xml.etree.ElementTree as ET
from pathlib import Path
import yaml
sys.excepthook = lambda t, v, tb: (print(f"REFUS : erreur interne de l'acceptation (à corriger dans le contrat ou le juge) : {t.__name__}: {v}"), sys.exit(3))  # 01/10 : un plantage devient un REFUS → correction auto

RADAR = Path(__file__).resolve().parent; RACINE = RADAR.parent.parent; K = RACINE / ".context/CLOTURE_20260927"
A = (RACINE / ".context/ACTIF").resolve(); NOYAU = A / "noyau/factory_v3/run.py"; MF = A / "mini_factory/mf.py"
projet, depot, dos = (Path(x).resolve() for x in sys.argv[1:4]); patchs = Path(sys.argv[4]).resolve() if len(sys.argv) > 4 else dos
c = yaml.safe_load((dos / "contrat.yaml").read_text()); ID = c["id"]
for k in ("a_faire_passer", "a_garder_verts"):          # nom de test seul → rattaché au fichier du juge (format GLM toléré)
    c[k] = [x if ".py" in x else f"{c['chemin_juge']}::{x}" for x in (c.get(k) or [])]
juge_src = next(p for p in list(dos.glob("test_*.py")) + list(patchs.glob("test_*.py")))
refus = lambda m: sys.exit(print(f"REFUS {ID} : {m}") or 3)  # noqa: E731

if any("test" in Path(x).name for x in c["livrables"]): refus("un livrable est un fichier de test")  # noqa: E701
CH = [*c["livrables"], c["chemin_juge"]]
if any(Path(x).is_absolute() or ".." in Path(x).parts for x in CH): refus("chemin hors copie")  # noqa: E701
for g in c["a_garder_verts"]:
    f = g.split("::")[0]; src = (juge_src if f == c["chemin_juge"] else depot / f).read_text(errors="replace")
    if re.search(r"playwright|socket\.|serve\(|urlopen|requests\.|httpx", src): refus(f"test à garder vert non hermétique : {g}")  # noqa: E701

def blocs(md):
    out = []
    for part in re.split(r"(?:^|\n)## Fichier \d+\s*[—:-]\s*", md.read_text())[1:]:  # P4 : un bloc en TOUT DÉBUT de fichier compte aussi (sinon patch honnête refusé)
        chemin = part.split("\n", 1)[0].strip().strip("`").split()[0].strip("`"); codes = re.findall(r"```[a-z]*\n(.*?)```", part, re.S)  # 30/09 diag GLM : ```sh était ignoré
        out += [(chemin, a, b) for a, b in zip(codes[0::2], codes[1::2])]
    return out

def jouer(nom, md):
    v = dos / "acceptation" / nom; shutil.rmtree(v, ignore_errors=True); v.mkdir(parents=True)
    a = subprocess.Popen(["git", "-C", str(depot), "archive", "HEAD"], stdout=subprocess.PIPE)
    subprocess.run(["tar", "-x", "-C", str(v)], stdin=a.stdout, check=True); a.stdout.close(); a.wait()
    bs = blocs(md) if md else []; hors = {ch for ch, _, _ in bs} - set(c["livrables"])  # 30/09 : chaque refus dit SA cause (la correction GLM doit savoir quoi réparer)
    if md is not None and (not bs or hors): return pq(f"chemin(s) hors livrables {sorted(hors)} (livrables : {c['livrables']})" if bs else "aucun bloc reconnu (« ## Fichier N — `chemin` » puis blocs ancien/nouveau)")
    for chemin, a, b in bs:
        p = v / chemin; t = p.read_text() if p.exists() else ""  # fichier NEUF : bloc « ancien » vide (29/09)
        if not p.resolve().is_relative_to(v.resolve()) or (a == "") == p.exists(): return pq(f"{chemin} : bloc « ancien » vide pour un fichier existant, ou fichier absent")  # noqa: E701
        p.parent.mkdir(parents=True, exist_ok=True)
        if t.count(a) != 1: return pq(f"{chemin} : bloc « ancien » trouvé {t.count(a)} fois (1 exigé) dans la version de RÉFÉRENCE {depot} (HEAD) — recopie-le à l'octet depuis CETTE version")
        p.write_text(t.replace(a, b))
    (v / c["chemin_juge"]).parent.mkdir(parents=True, exist_ok=True); shutil.copy(juge_src, v / c["chemin_juge"])
    fichiers = sorted({c["chemin_juge"], *(g.split("::")[0] for g in c["a_garder_verts"])})
    fd = os.open(v / "verdict_isole.json", os.O_WRONLY | os.O_CREAT, 0o600)  # 30/09 diag GLM : la matrice rejoue le juge dans LE MÊME isolement que le noyau
    subprocess.run([sys.executable, str(Path(NOYAU).parent / "juge_isole.py"), str(fd), ":".join(str(v / l) for l in c["livrables"]), "--", "-q", "-p", "no:cacheprovider",
                    "-p", "no:rerunfailures", "--junitxml", str(v / "j.xml"), *fichiers], cwd=v, capture_output=True, text=True, timeout=900, pass_fds=(fd,)); os.close(fd)
    if not (v / "j.xml").is_file(): return None  # Q5b : collecte cassée n'est pas une détection
    etat = {}
    for tc in ET.parse(v / "j.xml").iter("testcase"):
        cl = tc.get("classname", ""); f = tc.get("file") or cl.replace(".", "/") + ".py"
        if not (v / f).exists(): f = cl.rsplit(".", 1)[0].replace(".", "/") + ".py"   # classe de test : dernier élément = nom de classe
        etat[f"{f}::{tc.get('name')}"] = "rouge" if tc.find("failure") is not None or tc.find("error") is not None else ("saute" if tc.find("skipped") is not None else "vert")  # noqa: E501  Q5a : sauté ≠ vert
    return etat

_jouer = jouer
def pq(m):
    global POURQUOI; POURQUOI = m
def jouer(nom, md):   # 28/09 04:5x (pilote) : l'arbre extrait (622 Mo × 4 par jalon Twitter) est effacé après lecture ; seul j.xml (la preuve) reste
    try: return _jouer(nom, md)
    finally:
        for q in (dos / "acceptation" / nom).iterdir():
            if q.name != "j.xml": shutil.rmtree(q) if q.is_dir() and not q.is_symlink() else q.unlink()

def statut(etat, i):
    s = [v for k, v in etat.items() if k == i or k.startswith(i + "::") or (i.endswith(".py") and k.split("::")[0] == i)]
    return "absent" if not s else ("rouge" if "rouge" in s else "saute" if "saute" in s else "vert")  # Q5a : « saute » distinct de « vert »

base = jouer("base", None)
if base is None: refus("base inapplicable")  # noqa: E701
mauvais = [i for i in c["a_faire_passer"] if statut(base, i) != "rouge"] + [g for g in c["a_garder_verts"] if statut(base, g) != "vert"]
if mauvais: refus(f"base : attendus rouges/verts non conformes : {mauvais}")  # noqa: E701
hon = next(iter(sorted(patchs.glob("honnete*.patch.md"))), None) or next(iter(sorted(dos.glob("honnete*.patch.md"))), None)
TAILLE = sum(len(n.splitlines()) for _, _, n in blocs(hon)) if hon else 99  # lignes du correctif honnête
MOTEUR = "glm"  # propriétaire 29/09 23:4x : « économiser Claude à fond » (règle 1 suspendue, TAILLE mesurée)
h = jouer("honnete", hon) if hon else None
exig = c["a_faire_passer"] + c["a_garder_verts"]
if h is None: refus(f"patch honnête invalide : {globals().get('POURQUOI', 'absent')}")  # noqa: E701  Q5c
if any(statut(h, i) != "vert" for i in exig):
    refus(f"correction honnête non verte (sauté/absent ≠ vert) : {[i for i in exig if statut(h, i) != 'vert'][:6]}")
triches = sorted(dos.glob("triche*.patch.md"))
if len(triches) < 2: refus("moins de 2 triches")  # noqa: E701
for t in triches:
    e = jouer(t.stem, t)
    if e is None: refus(f"triche inapplicable (non jouée = non prouvée) : {t.name} : {globals().get('POURQUOI', '?')}")  # noqa: E701  (DURCI T2 28/09)
    if not any(statut(e, i) == "rouge" for i in exig): refus(f"triche non détectée par un ROUGE (absent/sauté/collecte ne comptent pas) : {t.name}")  # noqa: E701,E501  Q5b
print(f"MATRICE OK {ID} : base conforme, honnête verte, {len(triches)} triches refusées")

# --- dépôt du juge, contrat, hash, validation, mini-factory ---
shutil.copy(juge_src, depot / c["chemin_juge"])
env = {**os.environ, "GIT_AUTHOR_NAME": "Jocelyn Factory", "GIT_COMMITTER_NAME": "Jocelyn Factory",
       "GIT_AUTHOR_EMAIL": "jocelyn.grosjean@gmail.com", "GIT_COMMITTER_EMAIL": "jocelyn.grosjean@gmail.com"}
subprocess.run(["git", "-C", str(depot), "add", c["chemin_juge"]], check=True)
subprocess.run(["git", "-C", str(depot), "commit", "-q", "-m", f"juge {ID} (rédigé GLM, accepté par matrice pilote)"], check=False, env=env)  # rejouable : rien à commiter = juge inchangé
(projet / f"{ID}.md").write_text(f"# Tâche {ID}\n\n{c['tache'].strip()}\n")
tests = sorted({c["chemin_juge"], *(g.split("::")[0] for g in c["a_garder_verts"])})
m = {"id": ID, "produit": projet.parent.name, "type": "construction", "spec_ref": f"{ID}.md", "but": c["but"], "task_file": f"{ID}.md",
     "livrables": c["livrables"], "juge": {"a_faire_passer": c["a_faire_passer"], "a_garder_verts": c["a_garder_verts"]},
     "test_cmd": ["python3", "-m", "pytest", "-q", "-p", "no:cacheprovider", "-p", "no:rerunfailures", "--junitxml", "{junit}", *tests],
     "timeout_s": 600, "budget_moteur_s": 1800, "reseau_tests": False}
if c["chemin_juge"].startswith("juge_noyau/"): m["juge_isole"] = True   # noyau final : juge isolé obligatoire (lot O)
rm = projet / "ROADMAP.yaml"; t0 = rm.read_text()
K = next((k for k in (f"- id: {json.dumps(ID)}\n", f"- id: {ID}\n") if k in t0), None)  # 30/09 : l'id est écrit ENTRE GUILLEMETS → l'ancien bloc n'était jamais retrouvé (doublons, hash périmé)
if K:                                                     # rejouable : l'ancien bloc de CE jalon est remplacé, jamais dupliqué
    i = t0.index(K); j = t0.find("\n- id:", i + 1); t0 = t0[:i] + (t0[j + 1:] if j >= 0 else "")
    rm.write_text(t0 if t0.endswith("\n") else t0 + "\n")
with open(rm, "a") as f:
    f.write("".join(("- " if k == "id" else "  ") + f"{k}: {json.dumps(v, ensure_ascii=False)}\n" for k, v in m.items()))  # DURCI T5 : pas de yaml.safe_dump (CLAUDE.md §2) ; valeurs JSON = YAML valide
h = subprocess.run([sys.executable, str(NOYAU), "--hash-contrat", "--project", str(projet), "--milestone", ID], capture_output=True, text=True,
                   env={**os.environ, "FACTORY_NO_REAL_ENGINE": "1"}).stdout.strip().splitlines()[-1]
with open(projet / "ROADMAP.yaml", "a") as f:
    f.write(f'  valide: {{par: claude_pilote_auto, hash_contrat: "{h}", date: "2026-09-27", note: "matrice mécanique (base conforme, honnête verte, triches refusées) ; juge rédigé par GLM : sans indépendance de famille"}}\n')
to = subprocess.run([sys.executable, str(NOYAU), "--test-only", "--project", str(projet), "--milestone", ID], capture_output=True, text=True,
                    env={**os.environ, "FACTORY_NO_REAL_ENGINE": "1"}, timeout=2700)
if " VERT rc=0" not in to.stdout:                      # la base jouée DANS LE BAC du noyau (HOME neuf, réseau coupé) : ce que la matrice hors bac ne voit pas
    refus(f"--test-only du noyau non VERT (contrat écrit mais NON mis en file) : {(to.stdout + to.stderr).strip()[-300:]}")
import time
for _ in range(240):                                   # la chaîne tient le verrou mf pendant un run : attendre (≤ 40 min), jamais forcer
    r = subprocess.run([sys.executable, str(MF), "ajouter", ID, "--projet", str(projet), "--jalon", ID, "--moteur", MOTEUR, "--essais", "2"],
                       env={**os.environ, "MF_ETAT": str(projet.parent / "mf_etat"), "MF_NOYAU": f"python3 {NOYAU}"}, capture_output=True, text=True)
    if "autre mini-factory" not in r.stdout: break
    time.sleep(10)
if r.returncode: refus(f"mf ajouter rc={r.returncode} : NON mis en file ({r.stdout.strip()[-160:]})")
print(f"ACCEPTÉ {ID} : hash {h[:16]} ; mf ajouter rc={r.returncode} {r.stdout.strip()} {r.stderr.strip()[-200:]}")
