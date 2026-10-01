#!/bin/sh
# BRAS « IA SEULE » EN OMBRE (propriétaire 01/10 : « tester et se comparer ; parfois l'IA seule va plus vite et consomme moins »).
# Pour une étape déjà construite par le noyau : GLM SEUL reçoit la MÊME tâche (projet/<ID>.md), sur la MÊME base, dans un clone SANS juge
# (lecture limitée au clone, pas de shell). Puis la machine note son travail avec LE MÊME juge, dans LE MÊME isolement. Une ligne dans OMBRE.jsonl.
B="$(cd "$(dirname "$0")" && pwd)"; R="$B/../.."; P="$1"; ID="$2"; W="$HOME/temoin_runs/ombre_${P}_$ID"; J=$(ls "$B"/NOUVEAUX_*/"$ID"/test_*.py 2>/dev/null | tail -1)
RC=$(grep -l "\"milestone\": \"$ID\"" "$B/$P/copie/.factory_v3/runs"/*/RECEIPT.json 2>/dev/null | while read f; do [ -f "$(dirname "$f")/CONSIGNE.md" ] && echo "$f"; done | head -1)
[ -n "$J" ] && [ -n "$RC" ] || exit 0; BASE=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['base_sha'])" "$RC")
rm -rf "$W"; git clone -q "$B/$P/copie" "$W" && git -C "$W" checkout -q "$BASE" || exit 1
PERM='{"*":"deny","read":"allow","glob":"allow","grep":"allow","list":"allow","edit":"allow","bash":"deny","task":"deny","webfetch":"deny","websearch":"deny","external_directory":"deny","question":"deny","doom_loop":"deny"}'
T0=$(date +%s); OPENCODE_PERMISSION="$PERM" timeout 1800 opencode run --pure --dir "$W" --model zai-coding-plan/glm-5.3 --format json "$(cat "$B/$P/projet/$ID.md")" > "$W.jsonl" 2>&1; M=$(( ($(date +%s) - T0) / 60 ))
mkdir -p "$W/juge_noyau"; cp "$J" "$W/juge_noyau/"; LIVS=$(python3 -c "import yaml,sys;print(':'.join(sys.argv[2]+'/'+l for l in yaml.safe_load(open(sys.argv[1]))['livrables']))" "$(dirname "$J")/contrat.yaml" "$W")
exec 7>"$W.verdict"; (cd "$W" && python3 "$R/.context/ACTIF/noyau/factory_v3/juge_isole.py" 7 "$LIVS" -- -q -p no:cacheprovider "juge_noyau/$(basename "$J")" >/dev/null 2>&1); exec 7>&-
python3 - "$P" "$ID" "$W" "$M" "$RC" "$B/OMBRE.jsonl" <<'PY'
import json, re, sys, glob, os
P, ID, W, M, RC, OUT = sys.argv[1:]; tok = lambda f: sum(int(x) for l in open(f, errors="ignore") for x in re.findall(r'"(?:input|output|reasoning)":(\d+)', l))
v = json.loads(open(W + ".verdict").read() or "{}"); cas = v.get("cas", {}); ok = sum(1 for x in (cas.values() if isinstance(cas, dict) else cas) if str(x).lower() in ("pass", "passed", "vert", "true"))
runs = [os.path.dirname(f) for f in glob.glob(os.path.dirname(os.path.dirname(RC)) + "/*/RECEIPT.json") if f'"milestone": "{ID}"' in open(f).read() and os.path.exists(os.path.dirname(f) + "/CONSIGNE.md")]
rec = [json.load(open(r + "/RECEIPT.json")) for r in runs]
json.dump({"produit": P, "id": ID, "seul": {"reussis": ok, "total": len(cas), "rc_juge": v.get("rc"), "minutes": int(M), "tokens": tok(W + ".jsonl")},
           "noyau": {"essais": len(rec), "verdicts": [r.get("verdict") for r in rec], "minutes": round(sum(r.get("t_wall_total") or 0 for r in rec) / 60), "tokens": sum(tok(r + "/engine.log") for r in runs)}},
          open(OUT, "a"), ensure_ascii=False); open(OUT, "a").write("\n")
PY
