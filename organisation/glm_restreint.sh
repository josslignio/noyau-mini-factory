#!/bin/sh
# Lot GLM SANS exécution : OPENCODE_PERMISSION par lancement (sonde 27/09 12:56 : bash/task absents, écriture hors zone refusée).
# $1 = racine du dépôt ; $2 = dossier du lot, relatif à la racine ; $3 = nombre de passes. Config globale inchangée.
R="$1"; REL="$2"; N="$3"; W=$([ "${WEB:-0}" = 1 ] && echo allow || echo deny); NV=$([ "${NAV:-0}" = 1 ] && echo allow || echo deny); [ "$NV" = allow ] && export OPENCODE_CONFIG="$1/.context/SEO/NAVIGATEUR/opencode_nav.json"; C="$R/$REL"; L="$C/FILE.log"; ABS="${C#/}"  # WEB=1 : lecture du web autorisée (études de concurrents, 30/09) ; secrets toujours interdits en lecture ; NAV=1 : pilotage du profil Chrome SÉPARÉ du SEO (port 9333), jamais le Chrome principal
PERM="{\"*\":\"deny\",\"read\":{\"*\":\"allow\",\"*.env*\":\"deny\",\"*env_reel*\":\"deny\",\"*auth.json\":\"deny\"},\"glob\":\"allow\",\"grep\":\"allow\",\"list\":\"allow\",\"todowrite\":\"allow\",\"edit\":{\"*\":\"deny\",\"$REL/*\":\"allow\",\"$ABS/*\":\"allow\"},\"bash\":\"deny\",\"task\":\"deny\",\"webfetch\":\"$W\",\"chrome_*\":\"$NV\",\"websearch\":\"$W\",\"external_directory\":\"deny\",\"skill\":\"deny\",\"lsp\":\"deny\",\"question\":\"deny\",\"doom_loop\":\"deny\"}"
echo "$PERM" > "$C/permission_effective.json"
# 01/10 : sortie 98 304 (49 coupures « length » = réflexion au plafond opencode 32 000). 30/09 : reprend au 1er _DONE absent (Codex n°14 Q8).
i=${DEBUT:-1}; [ -n "$DEBUT" ] || while [ -f "$C/_DONE_$i.txt" ]; do i=$((i+1)); done; while [ "$i" -le "$N" ]; do
  rm -f "$C/_DONE_$i.txt"; { cat "$C/COMMUN.txt"; echo; cat "$C/P$i.txt"; } > "$C/Q$i.txt"
  echo "$(date '+%H:%M:%S') passe $i lancée (restreinte)" >> "$L"
  for k in 1 2 3; do OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX=98304 OPENCODE_PERMISSION="$PERM" timeout 1200 opencode run --pure --dir "$R" --model zai-coding-plan/glm-5.3 --format json "$(cat "$C/Q$i.txt")" > "$C/glm_p$i.jsonl" 2> "$C/glm_p$i.err"; RC=$?; grep -q "database is locked" "$C/glm_p$i.err" || break; sleep $((k*9)); done  # PANNE 7 : lancements simultanés
  FIN=$(grep -o '"reason":"[a-z_]*"' "$C/glm_p$i.jsonl" | tail -1)
  NB=$(grep -c '"tool":"bash"' "$C/glm_p$i.jsonl")
  echo "$(date '+%H:%M:%S') passe $i rc=$RC fin=$FIN done=$([ -f "$C/_DONE_$i.txt" ] && echo oui || echo NON) appels_bash=$NB" >> "$L"
  [ $RC -eq 0 ] && [ -f "$C/_DONE_$i.txt" ] || { echo "$(date '+%H:%M:%S') ARRÊT : passe $i rc=$RC ou sans _DONE" >> "$L"; exit 1; }
  i=$((i+1))
done
echo "$(date '+%H:%M:%S') lot terminé" >> "$L"
