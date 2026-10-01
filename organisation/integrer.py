"""Ramène les corrections VERTES des copies dans les VRAIS dépôts (propriétaire 28/09 : « ok on fait tt »). Aucun moteur. Aucun push.
Pour chaque produit : clone local de la copie → branche factory/corrections-nuit depuis la base réelle → cherry-pick du SEUL commit de
correction de chaque VERT (le plus récent par jalon ; un reçu n'entre QUE sur verdict == "VERT" ET rc == 0 explicites — Q4e)
→ juges recopiés depuis les octets FIGÉS du run (figes/ du run, sinon l'arbre git du base_sha du reçu ; sinon REFUS « juge non rattaché »,
JAMAIS l'état courant de la copie — Q4e) → PORTE : chaque juge ≥ 1 cas exécuté, aucun sauté, tous les ids a_faire_passer/a_garder_verts
du contrat PRÉSENTS et verts (Q4b) ; suite tests/ en 3 passages TOUJOURS rejoués des deux côtés (Q4d) : tout identifiant exécuté à la base
présent à l'intégration, aucune erreur (collecte comprise) nouvelle (Q4c), et nouveau rouge seulement s'il est rouge à l'intégration dans
≥ 1 passage ET vert à la base dans ≥ 1 passage (Q4d) → si porte OK : branche importée dans le vrai dépôt puis avance rapide --ff-only ;
échec = sortie rc ≠ 0 sans « FIN », HEAD de la branche active vérifié == branche intégrée (Q4f). Chaque rapport JUnit a un nom UNIQUE,
l'ancien est supprimé AVANT pytest et le code retour pytest est contrôlé (2/3/4 = illisible — Q4a). Sinon : rien dans le vrai dépôt, raison écrite.
Usage : python3 integrer.py job|twitter [--sans-ff] [--exclure ID,ID]"""
import hashlib, os, json, subprocess, sys, shutil, time, xml.etree.ElementTree as ET
from itertools import count
from pathlib import Path

B = Path(__file__).resolve().parent
RC_ILLISIBLE = (2, 3, 4)  # pytest interrompu / erreur interne / erreur d'usage : le rapport ne prouve rien (Q4a)
_NU = count()


def correspond(jid, cid):
    """id pytest du contrat (fichier[::Classe]::test) ↔ cas JUnit (classname::name) — même règle que le noyau."""
    (cn, _, nm), (f, _, rest) = cid.partition("::"), jid.partition("::")
    mod = (f[:-3] if f.endswith(".py") else f).replace("/", ".")
    if not rest:
        return cn == mod or cn.startswith(mod + ".")
    parts = rest.split("::")
    return cn == ".".join([mod, *parts[:-1]]) and (nm == parts[-1] or nm.startswith(parts[-1] + "["))


def lire_rapport(x):
    """Rapport JUnit → états ; None si illisible. Un <error> est une erreur (collecte comprise) ET un rouge."""
    try:
        tcs = list(ET.parse(x).iter("testcase"))
    except Exception:
        return None
    cle = lambda t: f"{t.get('classname')}::{t.get('name')}"  # noqa: E731
    ids = {cle(t) for t in tcs}
    rouges = {cle(t) for t in tcs if t.find("failure") is not None or t.find("error") is not None}
    sautes = {cle(t) for t in tcs if t.find("skipped") is not None} - rouges
    return {"n": len(tcs), "ids": ids, "rouges": rouges, "sautes": sautes, "verts": ids - rouges - sautes,
            "errs": {cle(t) for t in tcs if t.find("error") is not None}}


def rapport(cwd, cibles, nom):
    """Q4a : rapport à nom UNIQUE (jamais réutilisé), ancien supprimé AVANT pytest, code retour pytest contrôlé."""
    x = cwd / f"_{nom}_{next(_NU)}.xml"
    x.unlink(missing_ok=True)
    try:
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-p", "no:rerunfailures",
                            "-p", "no:randomly", "--continue-on-collection-errors", "--junitxml", str(x), *cibles],
                           cwd=cwd, capture_output=True, text=True, timeout=3600, env=os.environ | {"PYTHONPATH": "src"})
    except subprocess.TimeoutExpired:
        return None
    if r.returncode in RC_ILLISIBLE:
        return None
    return lire_rapport(x)


def juger(rap, exig):
    """Q4b : ≥ 1 cas exécuté, AUCUN sauté, chaque id a_faire_passer/a_garder_verts du contrat PRÉSENT et vert."""
    if rap is None:
        return "rapport illisible (rc pytest ou XML)"
    if rap["n"] < 1:
        return "0 cas exécuté"
    if rap["sautes"]:
        return f"cas sautés : {sorted(rap['sautes'])[:4]}"
    for i in exig:
        sel = {c for c in rap["ids"] if correspond(i, c)}
        if not sel:
            return f"id du contrat absent : {i}"
        if sel - rap["verts"]:
            return f"id non vert : {i}"
    return None


def porte_suite(pb, pi):
    """Q4c : suite non vide ; TOUT identifiant exécuté à la base présent à l'intégration (pas un % de cas) ; exécuté à la base jamais SAUTÉ à l'intégration ; aucune erreur (collecte comprise) nouvelle côté intégration."""
    if not pb["ids"]:
        return "suite vide à la base : 0 identifiant exécuté"
    m = sorted(pb["ids"] - pi["ids"])
    if m:
        return f"identifiants exécutés à la base absents de l'intégration ({len(m)}) : {m[:6]}"
    s = sorted((pb["verts"] | pb["rouges"]) & pi["sautes"])
    if s:
        return f"identifiants exécutés à la base sautés à l'intégration ({len(s)}) : {s[:6]}"
    return None   # 28/09 : erreurs nouvelles comptées avec les rouges, à la MAJORITÉ des passages (nouveaux_rouges)


def nouveaux_rouges(paires):
    """Q4d : rouge à l'intégration dans ≥ 1 passage ET vert à la base dans ≥ 1 passage ; un rouge apparu pendant un rejeu EST ajouté (union)."""
    ri = set().union(*(pi["rouges"] | pi["errs"] for _, pi in paires))   # Codex n°4 : UNION bloquante (1 passage suffit)
    br = set().union(*(pb["rouges"] | pb["errs"] for pb, _ in paires))   # seule exemption : instabilité VUE à la base
    return sorted(ri - br)   # nouveaux tests rouges (absents de la base) compris


def selection_vert(recus):
    """Q4e : un reçu n'entre QUE sur verdict == "VERT" ET rc == 0 explicites (+ motif, commit, run_uuid, base_sha) ; le plus récent par jalon."""
    vert = {}
    for r in recus:
        c = r.get("commit") or {}
        if r.get("verdict") == "VERT" and r.get("rc") == 0 and c.get("sha") and r.get("run_uuid") and r.get("base_sha") \
           and str(r.get("motif", "")).startswith("tests du juge verts") \
           and r["finished_at"] > vert.get(r["milestone"], ("",))[0]:
            vert[r["milestone"]] = (r["finished_at"], c["sha"], r["run_uuid"], r["base_sha"])
    return vert


def source_juge(run_dir, f, git_show=None):
    """Q4e : octets FIGÉS du run uniquement — figes/ (livrable-test gelé) ou jugement/ (run --keep), sinon l'arbre git du base_sha du reçu ; jamais la copie courante."""
    for c in (run_dir / "figes" / f, run_dir / "jugement" / f):
        if c.is_file():
            return c.read_bytes()
    return git_show(f) if git_show else None


def git_show(repo, sha, f):
    r = subprocess.run(["git", "-C", str(repo), "show", f"{sha}:{f}"], capture_output=True)
    return r.stdout if r.returncode == 0 else None


def avance_rapide(g, log, reel, branche, actif):
    """Q4f : échec du merge --ff-only → SystemExit(3) (rc ≠ 0, « FIN » non imprimé par l'appelant) ; HEAD de la branche active vérifié == branche intégrée."""
    r = g("merge", "--ff-only", branche, cwd=reel, ok=True)
    log(f"avance rapide de {actif} : rc={r.returncode} {(r.stdout + r.stderr).strip()[-200:]}")
    if r.returncode:
        log("PORTE REFUSÉE : avance rapide impossible"); raise SystemExit(3)  # noqa: E701
    if g("rev-parse", "HEAD", cwd=reel).stdout.strip() != g("rev-parse", branche, cwd=reel).stdout.strip():
        log(f"PORTE REFUSÉE : HEAD de {actif} ≠ {branche} après avance rapide"); raise SystemExit(3)  # noqa: E701


def main():
    import fcntl
    P = sys.argv[1]; FF = "--sans-ff" not in sys.argv
    REEL = {"job": Path.home() / "job-opportunity-radar",
            "twitter": Path.home() / "conductor/workspaces/twitter-radar/twitter-radar-foundation-v2",
            "tiktok": Path.home() / "pepita-video", "mailbox": Path.home() / "inbox-clean", "savespace": Path.home() / "savespace-drive"}[P]
    REMPLACE = {"JR_E4_DIGEST_DATE": "JR_E4_BN", "JR_D1_JC_SERVER_DATE": "JR_D1_BN",
                "TR_CASHTAG_TEXTE": "TR_CASHTAG_BN", "TR_UNIVERS_NEGOCIABLE": "TR_UNIVERS_BN"}
    COPIE = B / P / "copie"; I = Path.home() / "factory_integration"; W = I / P
    LOG = B / "INTEGRATION" / f"{P}.log"; BR = "factory/corrections-nuit"
    _VERROU = open(I / f"{P}.lock", "a")   # 28/09 01:15 : deux intégrations dans le même dossier se sont écrasées
    try:
        fcntl.flock(_VERROU, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        sys.exit(print(f"REFUS : une intégration {P} tourne déjà") or 3)

    def j(*a):
        LOG.parent.mkdir(exist_ok=True); LOG.open("a").write(time.strftime("%H:%M:%S ") + " ".join(map(str, a)) + "\n"); print(*a)

    def g(*a, cwd=None, ok=False):
        r = subprocess.run(["git", *a], cwd=cwd or W, capture_output=True, text=True)
        return r if ok else (r.check_returncode() or r)

    base = sys.argv[sys.argv.index("--base") + 1] if "--base" in sys.argv else g("rev-parse", "HEAD", cwd=REEL).stdout.strip()  # Codex Q4 : recertifier contre la base ORIGINALE
    base = g("rev-parse", base, cwd=REEL).stdout.strip(); actif = g("branch", "--show-current", cwd=REEL).stdout.strip()
    vert = selection_vert(json.loads(f.read_text()) for f in sorted(COPIE.glob(".factory_v3/runs/*/RECEIPT.json")))
    EXCLU = set(sys.argv[sys.argv.index("--exclure") + 1].split(",")) if "--exclure" in sys.argv else set()   # jalons réservés à une décision propriétaire
    VETO = {x.split(":")[0].strip() for v in B.glob("RELECTURES/*/VERDICTS.md") for x in v.read_text().splitlines()
            if ": À REVOIR" in x and x.strip().split(":")[0].startswith(("JO_", "JR_", "TW_", "TR_"))}  # relecture croisée
    EXCLU |= VETO; j(f"VETO relecture : {sorted(VETO)}") if VETO else None
    choix = sorted((t, m, s, u, bs) for m, (t, s, u, bs) in vert.items() if REMPLACE.get(m) not in vert and m not in EXCLU)
    if EXCLU: j(f"EXCLUS (décision propriétaire) : {sorted(EXCLU)}")
    j(f"== {P} réel={REEL} actif={actif} base={base[:8]} ; {len(choix)} corrections : {[m for _, m, _, _, _ in choix]}")
    shutil.rmtree(W, ignore_errors=True); subprocess.run(["git", "clone", "-q", str(COPIE), str(W)], check=True)
    g("config", "user.name", "Jocelyn Factory"); g("config", "user.email", "jocelyn.grosjean@gmail.com")
    # Chaque VERT a été construit sur une base SANS les autres corrections : on empile une à une, et chaque ajout doit laisser VERTS
    # le juge du jalon ET ceux déjà empilés ; sinon il est retiré (INCOMPATIBLE, à reconstruire sur la base intégrée).
    g("fetch", "-q", str(REEL), base); g("checkout", "-q", "-b", BR, base); pris = []   # base réelle absente de la copie
    # 28/09 00:30 : hors de l'arbre factory (sinon pytest remonte au pytest.ini de la factory : --reruns inconnu → faux rouges/illisible) ;
    # juge = fichier(s) réel(s) du contrat (ROADMAP), où qu'ils soient — pas seulement juge_noyau/ (TR_G1/TR_G2 passaient sans contrôle).
    import yaml
    _r = yaml.safe_load((B / P / "projet/ROADMAP.yaml").read_text()); _r = _r.get("milestones", []) if isinstance(_r, dict) else _r
    RM = {m["id"]: m for m in _r if isinstance(m, dict) and "id" in m and "juge" in m}
    fj = lambda m: sorted({x.split("::")[0] for x in RM[m]["juge"]["a_faire_passer"] + RM[m]["juge"]["a_garder_verts"]}) if m in RM else []  # noqa: E731
    exig = lambda m: RM[m]["juge"]["a_faire_passer"] + RM[m]["juge"]["a_garder_verts"]  # noqa: E731
    for _, m, s, u, bs in choix:
        r = g("cherry-pick", "-x", s, ok=True)
        if r.returncode:
            g("cherry-pick", "--abort", ok=True); j(f"CONFLIT {m} {s[:8]} : écarté ({(r.stdout + r.stderr).strip()[-160:]})"); continue
        if not fj(m):
            g("reset", "-q", "--hard", "HEAD~1"); j(f"SANS JUGE {m} : écarté"); continue
        drun = COPIE / ".factory_v3" / "runs" / u
        octets = {f: source_juge(drun, f, lambda x, bs=bs: git_show(COPIE, bs, x)) for f in fj(m)}   # Q4e : octets figés du run
        manq = sorted(f for f, o in octets.items() if o is None)
        if manq:
            g("reset", "-q", "--hard", "HEAD~1"); j(f"REFUS {m} : juge non rattaché au run {u} : {manq}"); continue
        ajout = [f for f in fj(m) if not (W / f).exists()]
        for f in fj(m):
            (W / f).parent.mkdir(parents=True, exist_ok=True); (W / f).write_bytes(octets[f])
        rouges = [x for x in pris + [m] if juger(rapport(W, fj(x), "jug"), exig(x))]   # Codex n°4 : TOUS les juges évalués
        mauvais = next((x for x in rouges if any(juger(rapport(W, fj(x), "jug"), exig(x)) for _ in range(2))), None)
        [j(f"juge instable {x} (1 rouge sur 3, sous {m}) : gardé ; la suite complète tranche") for x in rouges if x != mauvais]
        if mauvais:
            g("reset", "-q", "--hard", "HEAD~1"); [(W / f).unlink(missing_ok=True) for f in ajout]
            j(f"INCOMPATIBLE {m} {s[:8]} : écarté (juge de {mauvais} non VERT une fois empilé)"); continue
        pris.append(m); j(f"pris {m} {s[:8]}")
    garder = sorted({f for m in pris for f in fj(m) if f.startswith("juge_noyau/")})  # 28/09 : un juge sous tests/ perturbe la suite
    if garder:
        g("add", *garder); g("commit", "-q", "-m", f"juges de non-régression de la factory ({len(garder)}) pour les corrections de la nuit")
    M = W / "APP007_INTEGRATION_MANIFEST.json"   # --manifeste (propriétaire 28/09 « débloque tout ») : empreintes suivies
    if M.exists() and "--manifeste" in sys.argv:
        d = json.loads(M.read_text())
        for it in d["assembled_head_bindings"]["files"]:
            it["sha256"] = hashlib.sha256((W / it["path"]).read_bytes()).hexdigest()
        M.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
        g("commit", "-qam", "manifeste d'autorité : empreintes des fichiers intégrés (décision propriétaire 28/09)", ok=True)
    wb = I / f"{P}_base"; shutil.rmtree(wb, ignore_errors=True); wb.mkdir()
    subprocess.run(f"git -C '{W}' archive {base} | tar -x -C '{wb}'", shell=True, check=True)
    wi = I / f"{P}_integ"; shutil.rmtree(wi, ignore_errors=True); wi.mkdir()
    subprocess.run(f"git -C '{W}' archive {BR} | tar -x -C '{wi}'", shell=True, check=True)
    # 28/09 00:20 : la 1re porte a laissé passer une suite ARRÊTÉE à la collecte (2 cas des deux côtés = « aucun nouveau rouge ») → vert gratuit.
    paires = []
    for k in ("", "_r1", "_r2"):                            # Q4d : 2 rejeux complets TOUJOURS faits, suspects ou non
        pb, pi = rapport(wb, ["tests"], "base" + k), rapport(wi, ["tests"], "integ" + k)
        if pb is None or pi is None:
            j("PORTE REFUSÉE : suite tests/ illisible (rc pytest ou rapport absent)"); sys.exit(3)
        if (raison := porte_suite(pb, pi)):
            j(f"PORTE REFUSÉE : {raison}"); sys.exit(3)
        paires.append((pb, pi))
    nouveaux = nouveaux_rouges(paires)
    inst = {x for c in (0, 1) for x in set().union(*(q[c]["rouges"] for q in paires)) & set().union(*(q[c]["verts"] for q in paires))}
    (B / P / "INSTABLES.txt").write_text("\n".join(sorted(inst | set((B / P / "INSTABLES.txt").read_text().split()
        if (B / P / "INSTABLES.txt").exists() else ()))) + "\n")  # règle 3 : rouge ET vert selon le passage = instable
    j(f"suite tests/ : {len(paires)} passages complets des deux côtés ; NOUVEAUX rouges persistants : {nouveaux}")
    if nouveaux:
        j("PORTE REFUSÉE : nouveaux rouges"); sys.exit(3)
    g("fetch", "-q", str(W), f"+{BR}:{BR}", cwd=REEL); j(f"branche {BR} importée dans {REEL} ({g('rev-parse', BR, cwd=REEL).stdout.strip()[:8]})")
    if FF:
        avance_rapide(g, j, REEL, BR, actif)                 # Q4f : échec → SystemExit(3) avant « FIN » ; HEAD vérifié
        g("fetch", "-q", str(W), BR, cwd=COPIE); fu = g("merge", "-q", "--no-edit", "FETCH_HEAD", cwd=COPIE, ok=True)
        j(f"copie avancée sur la base intégrée : rc={fu.returncode}")  # les prochains jalons partent des corrections intégrées
        fu.returncode and g("merge", "--abort", cwd=COPIE, ok=True)
    j(f"FIN {P} : {len(pris)} corrections intégrées {pris}")


if __name__ == "__main__":
    main()
