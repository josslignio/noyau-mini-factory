#!/bin/sh
# SEULE façon de changer un script verrouillé (PANNE 6, 30/09) : vérifie la syntaxe, puis remplacement ATOMIQUE (mv) —
# un processus en cours garde l'ancien fichier entier, le prochain lancement lit le nouveau entier. Usage : sh remplacer.sh <cible> <nouveau>
C="$1"; N="$2"; L="$(dirname "$0")/VERROU.log"
case "$C" in *.sh) sh -n "$N" ;; *.py) python3 -m py_compile "$N" ;; *) true ;; esac || { echo "$(date '+%F %T') REFUS syntaxe $N" >> "$L"; exit 2; }
cp -p "$C" "$C.avant_$(date +%Y%m%d_%H%M%S)" 2>/dev/null; chflags nouchg "$C" 2>/dev/null
chmod +x "$N"; mv -f "$N" "$C" || { chflags uchg "$C"; echo "$(date '+%F %T') ÉCHEC remplacement $C (re-verrouillé)" >> "$L"; exit 3; }; chflags uchg "$C" && echo "$(date '+%F %T') remplacé $C" >> "$L"
