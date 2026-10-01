#!/bin/sh
# CONTRÔLE HORAIRE (propriétaire 30/09 18:2x : « check toi-même toutes les 30 min ou 1 h que ça délivre, optimisé, sans perdre temps, rapidité ou quota »).
# Résumé MACHINE, court, pour que le pilote Claude décide vite et à bas coût : les 3 faits + anomalies. Aucune action ici.
B="$(cd "$(dirname "$0")" && pwd)"; cd "$B"
echo "== $(TZ=Asia/Bangkok date '+%d/%m %H:%M') contrôle horaire"
echo "RÉGLÉ (1 h, reçus VERT) : $(find */copie/.factory_v3/runs -name RECEIPT.json -mmin -60 -exec grep -l '"VERT"' {} + 2>/dev/null | while read f; do [ -f "$(dirname "$f")/CONSIGNE.md" ] && echo "$f"; done | sed 's#/copie/.factory_v3/runs/# #; s#/RECEIPT.json##' | tr '\n' ';')"
echo "ACCEPTÉ/REFUS (1 h) : $(find NOUVEAUX_* -name 'acceptation*.out' -mmin -60 -exec grep -lh ACCEPTÉ {} + 2>/dev/null | wc -l | tr -d ' ') / $(find NOUVEAUX_* -name 'acceptation*.out' -mmin -60 -exec grep -lh REFUS {} + 2>/dev/null | wc -l | tr -d ' ')"
echo "DERNIER VERT : $(grep -E '→ VERT' CHAINE.log | tail -1 | cut -c1-60)"
for P in $(ls -d */mf_etat | cut -d/ -f1); do [ -f "$P/ARRET" ] && continue; printf "%s " "$P"; MF_ETAT="$P/mf_etat" python3 ../ACTIF/mini_factory/mf.py statut 2>/dev/null | python3 -c "import json,sys,collections;d=json.load(sys.stdin);print(dict(collections.Counter(v.get('etat') for v in d.values())))" 2>/dev/null || echo "?"; done
echo "LOTS COINCÉS (6 h, ni fini, ni vivant, ni accepté) : $(for d in $(find . -maxdepth 1 -name 'NOUVEAUX_*' -mmin -360); do [ -f "$d/_FINI" ] || [ -f "$d/_ABANDON" ] || pgrep -f "$(basename "$d")" >/dev/null || tail -1 "$d/FILE.log" 2>/dev/null | grep -qE 'ACCEPTÉ|lot terminé' || echo "$(basename "$d")[$(tail -1 "$d/FILE.log" 2>/dev/null | cut -c10-60)]"; done | tr '\n' ' ')"
echo "REFUS APRÈS CORRECTION (6 h) : $(grep -l "après correction : REFUS" $(find . -maxdepth 2 -name FILE.log -mmin -360) 2>/dev/null | cut -d/ -f2 | tr '\n' ' ')"
echo "LOTS GLM VIVANTS : $(pgrep -f '^opencode run' | wc -l | tr -d ' ') ; CHAÎNE : $(pgrep -f '^sh .*chaine_mf\.sh' >/dev/null && echo oui || echo non)"
echo "ALERTES (1 h) : $(awk -v h="$(date -v-1H '+%F %T')" '$1" "$2>=h' SENTINELLE.log | grep -v 'ronde faite' | cut -c21-120 | tr '\n' ';')"
echo "SENTINELLE dernière ronde : $(grep 'ronde faite' SENTINELLE.log | tail -1 | cut -c1-19) ; ENCHAÎNEUR : $(grep -v NOTICE ENCHAINEUR.log | tail -1 | cut -c1-19)"
M=$(ls -t ../PREUVE_48H_*/MESURES.jsonl | head -1); echo "48 h : $(wc -l < "$M" | tr -d ' ') relevés, dernier $(tail -1 "$M" | cut -c8-26), erreurs $(wc -l < "$(dirname "$M")/erreurs.log" | tr -d ' ')"
echo "PLAFONDS : $(python3 verifier_plafonds.py | head -1 | cut -c1-60)"
echo "QUOTAS : $(python3 ../../factory_v2/quota_live.py 2>/dev/null | awk '/^  [a-z]/{e=$1} /seven_day |weekly /{printf "%s %s%% ; ", e, int($3)}')"
python3 "$B/tableau_bord.py" >/dev/null 2>&1  # tableau de bord Obsidian mis à jour à chaque contrôle
V=$(find */copie/.factory_v3/runs -name RECEIPT.json -mmin -90 -exec grep -l '"VERT"' {} + 2>/dev/null | while read f; do [ -f "$(dirname "$f")/CONSIGNE.md" ] && echo "$f"; done | wc -l | tr -d ' '); A=""; [ "$V" -eq 0 ] && A="$A aucun VERT en 90 min;"; pgrep -f "^opencode run" >/dev/null || pgrep -f "^sh .*chaine_mf" >/dev/null || A="$A GLM à l'arrêt;"
python3 verifier_plafonds.py >/dev/null || A="$A plafonds;"; [ -n "$(find ../PREUVE_48H_* -name MESURES.jsonl -mmin -45)" ] || A="$A 48 h muette;"
echo "VERDICT MACHINE : $([ -z "$A" ] && echo "RAS ($V VERT en 90 min)" || echo "À REGARDER :$A")"  # le pilote ne creuse QUE si « À REGARDER » (économie du quota Claude)
