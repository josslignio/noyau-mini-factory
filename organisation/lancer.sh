#!/bin/sh
# Lance le travail d'un dossier de lot et marque la fin : _FINI si réussi, une ligne dans _ECHECS sinon. Le relanceur reprend les lots sans _FINI.
D="$(cd "$1" && pwd)"; touch "$D/_LANCE"; echo "$(date '+%F %T') essai" >> "$D/_ESSAIS"; sh "$D/file_travail.sh"; RC=$?  # essai compté AVANT (Codex n°14 Q8 : mort précoce = relances illimitées)
[ $RC -eq 0 ] && touch "$D/_FINI" && python3 "$(dirname "$0")/indexer_etudes.py" >/dev/null 2>&1 || echo "$(date '+%F %T') rc=$RC" >> "$D/_ECHECS"; exit $RC
