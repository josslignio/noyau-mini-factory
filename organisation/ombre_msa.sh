#!/bin/sh
# 3e CAMP (propriétaire 01/10) : mini-swe-agent (harnais open source) + GLM, dans la VM Linux isolée, sur la MÊME tâche et la MÊME base que le noyau.
# Noté ensuite sur le Mac par LE MÊME juge dans LE MÊME isolement → une ligne dans OMBRE_MSA.jsonl.
B="$(cd "$(dirname "$0")" && pwd)"; R="$B/../.."; P="$1"; ID="$2"; W="$HOME/temoin_runs/msa_${P}_$ID"; J=$(ls "$B"/NOUVEAUX_*/"$ID"/test_*.py 2>/dev/null | tail -1)
RC=$(grep -l "\"milestone\": \"$ID\"" "$B/$P/copie/.factory_v3/runs"/*/RECEIPT.json 2>/dev/null | while read f; do [ -f "$(dirname "$f")/CONSIGNE.md" ] && echo "$f"; done | head -1)
[ -n "$J" ] && [ -n "$RC" ] || exit 0; BASE=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['base_sha'])" "$RC")
rm -rf "$W"; git clone -q "$B/$P/copie" "$W" && git -C "$W" checkout -q "$BASE" && rm -rf "$W/.git" "$W/.factory_v3" "$W/juge_noyau" || exit 1
. "$R/.context/BUILD_V3_2026-09-25/.env_reel"; printf '%s' "$ZAI_API_KEY" | limactl shell factory-linux -- sh -c 'umask 077; cat > ~/.zai_key'
COPYFILE_DISABLE=1 tar --no-xattrs -C "$W" -cf - . | limactl shell factory-linux -- sh -c "rm -rf ~/t && mkdir -p ~/t && tar -C ~/t -xf -"; cp "$B/$P/projet/$ID.md" "$W.tache"
T0=$(date +%s); limactl shell factory-linux -- sh -c "cd ~/t && OPENAI_API_KEY=\$(cat ~/.zai_key) OPENAI_API_BASE=https://api.z.ai/api/coding/paas/v4 OPENAI_BASE_URL=https://api.z.ai/api/coding/paas/v4 MSWEA_COST_TRACKING=ignore_errors timeout 1800 ~/msa/bin/mini -m openai/glm-5.3 -y -l 0 -t \"\$(cat)\" < /dev/stdin" < "$W.tache" > "$W.log" 2>&1; M=$(( ($(date +%s) - T0) / 60 ))
limactl shell factory-linux -- sh -c "tar -C ~/t -cf - ." | tar -C "$W" -xf -; mkdir -p "$W/juge_noyau"; cp "$J" "$W/juge_noyau/"
LIVS=$(python3 -c "import yaml,sys;print(':'.join(sys.argv[2]+'/'+l for l in yaml.safe_load(open(sys.argv[1]))['livrables']))" "$(dirname "$J")/contrat.yaml" "$W")
exec 7>"$W.verdict"; (cd "$W" && python3 "$R/.context/ACTIF/noyau/factory_v3/juge_isole.py" 7 "$LIVS" -- -q -p no:cacheprovider "juge_noyau/$(basename "$J")" >/dev/null 2>&1); exec 7>&-
python3 -c "import json,sys;v=json.loads(open(sys.argv[3]+'.verdict').read() or '{}');c=v.get('cas',{});print(json.dumps({'produit':sys.argv[1],'id':sys.argv[2],'msa':{'reussis':sum(1 for x in c.values() if x=='pass'),'total':len(c),'minutes':int(sys.argv[4])}}))" "$P" "$ID" "$W" "$M" >> "$B/OMBRE_MSA.jsonl"
