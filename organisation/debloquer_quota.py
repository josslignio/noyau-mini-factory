"""Au renouvellement du quota : remet « prêt » les SEULS jalons dont le DERNIER reçu est un REFUS pour quota (aucun moteur lancé). Tout autre blocage reste bloqué.
Usage : python3 debloquer_quota.py [--oui]   (sans --oui : liste seulement)"""
import glob, json, os, subprocess, sys
from pathlib import Path
B = Path(__file__).parent.resolve(); MF = B.parent / "ACTIF/mini_factory/mf.py"; env = os.environ | {"MF_ETAT": str(B / os.getenv("PRODUIT","job") / "mf_etat")}
dernier = {}
for f in glob.glob(str(B / "*/copie/.factory_v3/runs/*/RECEIPT.json")):
    r = json.load(open(f)); m, t = r.get("milestone"), r.get("finished_at") or ""
    if m and t > dernier.get(m, ("",))[0]: dernier[m] = (t, r.get("verdict"), r.get("motif") or "", (r.get("engine") or {}).get("rc"))
etat = json.loads(subprocess.run([sys.executable, str(MF), "statut"], env=env, capture_output=True, text=True).stdout or "{}")
cibles = [k for k, v in etat.items() if v.get("etat") == "bloque" and k in dernier and dernier[k][1] == "REFUS" and dernier[k][2].startswith("quota")]
print("à débloquer (dernier reçu = REFUS quota, aucun moteur) :", cibles)
if "--oui" in sys.argv:
    for k in cibles:
        r = subprocess.run([sys.executable, str(MF), "regler", k, "pret", "--raison", "REFUS quota ≥ 90 % pendant la nuit du 28/09 ; quota renouvelé ; aucun moteur n'avait été lancé"], env=env, capture_output=True, text=True)
        print(k, "rc", r.returncode, r.stdout.strip()[-120:])
