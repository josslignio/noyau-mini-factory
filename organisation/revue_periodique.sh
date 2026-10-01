#!/bin/sh
# REVUE QUOTIDIENNE (propriétaire 30/09) par GLM avec lecture du web : écarts docs/faits, bugs connus ailleurs, code à retirer, briques mesurables.
B="$(cd "$(dirname "$0")" && pwd)"; R="$B/../.."; LOT="REVUE_$(date +%Y%m%d)"; D="$B/$LOT"; cd "$B"
[ -f "$D/_DONE_1.txt" ] && [ -f "$D/_DONE_2.txt" ] && [ -f "$D/_DONE_3.txt" ] && exit 0; mkdir -p "$D"
for f in COMMUN P1 P2 P3; do sed "s/@LOT@/$LOT/g" "CONSIGNES_GLM/REVUE_$f.txt" > "$D/$f.txt"; done
WEB=1 sh "$R/.context/CLOTURE_20260927/glm_restreint.sh" "$R" ".context/RADAR/$LOT" 3
