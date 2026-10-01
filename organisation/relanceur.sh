#!/bin/sh
# Reprise des lots coupés (propriétaire 30/09 : « tu améliores la relance si coupé ») : tout dossier lancé par lancer.sh, sans _FINI,
# sans processus vivant, est relancé (la reprise repart de la passe manquante) ; 3 échecs → _ABANDON, plus de relance (anti-boucle).
B="$(cd "$(dirname "$0")" && pwd)"; L="$B/RELANCE.log"
for m in "$B"/NOUVEAUX_*/_LANCE; do
  [ -f "$m" ] || continue; D="$(dirname "$m")"; [ -f "$D/_FINI" ] || [ -f "$D/_ABANDON" ] && continue
  pgrep -f "^sh .*($(basename "$D")/file_travail\.sh|lancer\.sh $D)$" >/dev/null && continue
  E=$(cat "$D/_ESSAIS" 2>/dev/null | wc -l | tr -d ' ')  # essais lancés (pas seulement les échecs journalisés)
  if [ "$E" -ge 3 ]; then touch "$D/_ABANDON"; echo "$(date '+%F %T') ABANDON $(basename "$D") après $E échecs" >> "$L"; continue; fi
  python3 "$B/../BUILD_V3_2026-09-25/detache.py" "$D/relance.out" sh "$B/lancer.sh" "$D" >/dev/null || echo "$(date '+%F %T') détachement raté" >> "$D/_ESSAIS"
  echo "$(date '+%F %T') relancé $(basename "$D") (échecs précédents : $E)" >> "$L"
done
