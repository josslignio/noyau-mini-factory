#!/bin/sh
# À lancer par le PROPRIÉTAIRE dans un terminal du Mac. AUCUN copier-coller : le jeton est lu dans la sortie de « claude setup-token »,
# écrit dans .env_claude (droits 600), puis l'enregistrement temporaire est effacé. Le jeton n'est jamais affiché par ce script.
F="$HOME/conductor/workspaces/Jocelyn-factory-control/factory-foundation-v2/.context/BUILD_V3_2026-09-25/.env_claude"
TS=$(mktemp "$HOME/.jeton_claude.XXXXXX"); chmod 600 "$TS"; trap 'rm -f "$TS"' EXIT
echo "Le navigateur va s'ouvrir : connecte-toi, valide, puis reviens ici. Rien d'autre à faire."
printf '\033[8;40;300t'; sleep 1                 # fenêtre élargie à 300 colonnes (le jeton ne doit plus être coupé)
C0=$(stty size | cut -d' ' -f2); stty cols 300    # et le terminal se déclare large de 300 colonnes, quoi qu'il arrive à l'écran
script -q "$TS" claude setup-token
stty cols "$C0"
python3 - "$TS" "$F" <<'PY'
import os, re, sys
brut = open(sys.argv[1], "rb").read().decode("utf-8", "replace")
txt = re.sub(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07]*\x07|\r", "", brut)
lignes = txt.split("\n"); best = ""
for i, l in enumerate(lignes):
    m = re.search(r"sk-ant-[A-Za-z0-9_\-]+", l)
    if not m: continue
    t = m.group(0)
    j = i + 1
    while len(t) < 90 and j < len(lignes) and re.fullmatch(r"[A-Za-z0-9_\-]+", lignes[j].strip() or "#"):
        t += lignes[j].strip(); j += 1                 # jeton coupé sur plusieurs lignes par la largeur du terminal
    k = re.search(r"AA(?=[A-Z][a-z])", t); t = t[:k.end()] if k else t   # 28/09 : le texte suivant (« Store… ») se collait au jeton
    best = max(best, t, key=len)
if len(best) < 90:
    sys.exit(print(f"Jeton non trouvé ou incomplet ({len(best)} caractères). Rien écrit. Envoie une capture à Claude.") or 1)
os.umask(0o077); open(sys.argv[2], "w").write(f"CLAUDE_CODE_OAUTH_TOKEN={best}\n"); os.chmod(sys.argv[2], 0o600)
print(f"OK : jeton enregistré ({len(best)} caractères). Tu peux fermer ce terminal.")
PY
