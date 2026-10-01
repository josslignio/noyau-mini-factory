#!/bin/sh
# Verrou système (chflags uchg) sur les scripts d'outillage : aucune écriture en place possible, ni par Claude ni par un outil.
# Puis TÉMOIN : tente d'écrire dans chaque fichier ; une seule réussite = verrou cassé → sortie 1. Modifier : sh remplacer.sh <cible> <nouveau>.
X="$(cd "$(dirname "$0")/.." && pwd)"; L="$X/RADAR/VERROU.log"
F=$(ls "$X"/RADAR/*.sh "$X"/RADAR/*.py "$X"/CLOTURE_20260927/glm_restreint.sh "$X"/ESSAI_TEMOIN/*.sh "$X"/BUILD_V3_2026-09-25/detache.py "$X"/VIDEOS_YT/recup.sh 2>/dev/null)
n=0; k=0; for f in $F; do chflags uchg "$f"; n=$((n+1)); ( : >> "$f" ) 2>/dev/null && { k=$((k+1)); echo "$(date '+%F %T') VERROU CASSÉ : $f accepte l'écriture" >> "$L"; }; done
echo "$(date '+%F %T') verrou : $n fichiers, $k acceptent encore l'écriture" >> "$L"; [ $k -eq 0 ]
