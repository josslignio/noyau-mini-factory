#!/bin/sh
# SENTINELLE (propriétaire 30/09 : « le système aurait dû s'en rendre compte lui-même, fixer puis relancer »). launchd toutes les 15 min,
# SÉPARÉE de l'enchaîneur : un programme ne voit pas qu'il n'a pas démarré. Elle regarde des FAITS (âges de fichiers, états), jamais des intentions.
B="$(cd "$(dirname "$0")" && pwd)"; L="$B/SENTINELLE.log"; AL="$HOME/Obsidian/Factory/ALERTES.md"
a() { K="$B/.alerte_$(echo "$1" | cksum | cut -d" " -f1)"; [ -f "$K" ] && [ $(( $(date +%s) - $(stat -f %m "$K") )) -lt 3600 ] && return; touch "$K"; shift; echo "$(date '+%F %T') $*" >> "$L"; echo "- $(date '+%d/%m %H:%M') $*" >> "$AL"; osascript -e "display notification \"$*\" with title \"Factory\"" >/dev/null 2>&1; }
age() { echo $(( $(date +%s) - $(stat -f %m "$1" 2>/dev/null || echo 0) )); }
BL=""; for d in "$B"/*/mf_etat; do P=$(basename "$(dirname "$d")"); [ -f "$B/$P/ARRET" ] && continue
  S=$(MF_ETAT="$d" python3 "$B/../ACTIF/mini_factory/mf.py" statut 2>/dev/null | python3 -c "import json,sys;d=json.load(sys.stdin);print(' '.join(k+':'+v.get('etat','') for k,v in d.items()))" 2>/dev/null)
  n=$(echo "$S" | tr ' ' '\n' | grep -c ':pret$'); [ "$n" -gt 0 ] && ! pgrep -f "^sh .*chaine_mf\.sh .* $P$" >/dev/null && \
    { a "pret$P" "$P : $n jalon(s) prêt(s) sans construction → chaîne du produit lancée TOUT DE SUITE (01/10 propriétaire : « démarre »)"; R=$(cd "$B/../.." && pwd); python3 "$B/../BUILD_V3_2026-09-25/detache.py" "$B/chaine_$P.out" sh -c "env -u FACTORY_NO_REAL_ENGINE sh '$B/chaine_mf.sh' '$R' '$P'; [ '$P' = usine ] || timeout 1500 python3 '$B/integrer.py' '$P'" >/dev/null; }
  for k in $(echo "$S" | tr ' ' '\n' | grep ':bloque$' | cut -d: -f1); do BL="$BL $P/$k"; grep -q "bloqué $P/$k" "$L" 2>/dev/null || a "b$P$k" "bloqué $P/$k : à relire (Codex groupé)"; done
  echo "$S" | tr ' ' '\n' | grep -qE ':(inconnu|en_cours)$' && [ "$(age "$d/file.json")" -gt 7200 ] && a "etat$P" "$P : jalon en_cours/inconnu figé depuis 2 h ($(echo "$S" | tr ' ' '\n' | grep -E ':(inconnu|en_cours)$' | tr '\n' ' '))"
done
QG=$(python3 "$B/../../factory_v2/quota_live.py" 2>/dev/null | awk '/^  glm/{g=1} g && /weekly/{print int($3); exit}'); [ "${QG:-0}" -ge 90 ] && a quota "GLM à ${QG} % : la construction est arrêtée jusqu'au renouvellement"
J=$(date +%F); [ "${QG:-99}" -lt 60 ] && [ ! -f "$B/REVUE_$(date +%Y%m%d)/_DONE_3.txt" ] && ! pgrep -f "^sh .*revue_periodique\.sh" >/dev/null && [ "$(grep -c "^$J.*revue quotidienne lancée" "$L")" -lt 3 ] && { echo "$(date '+%F %T') revue quotidienne lancée" >> "$L"; python3 "$B/../BUILD_V3_2026-09-25/detache.py" "$B/REVUE_PERIODIQUE.out" sh "$B/revue_periodique.sh" >/dev/null; }  # 01/10 : reprise de l'enchaîneur retiré
python3 "$B/verifier_plafonds.py" >/dev/null || a plafonds "plafonds dépassés : la chaîne refusera de construire ($(python3 "$B/verifier_plafonds.py" | head -1 | cut -c1-120))"
sh "$B/verrouiller.sh" || a verrou "verrou des scripts cassé (VERROU.log)"
M48=$(ls -t "$B"/../PREUVE_48H_*/MESURES.jsonl 2>/dev/null | head -1); [ -n "$M48" ] && [ "$(age "$M48")" -gt 2700 ] && [ "$(age "$M48")" -lt 7200 ] && a m48 "mesure 48 h muette depuis 45 min ($M48)"
CU="$B/usine/copie"; for f in "$B"/*.sh "$B"/*.py "$B/../CLOTURE_20260927/glm_restreint.sh"; do cmp -s "$f" "$CU/outils/$(basename "$f")" || cp "$f" "$CU/outils/"; done  # copie usine = outils EN SERVICE
[ -n "$(git -C "$CU" status --porcelain outils)" ] && git -C "$CU" add outils && git -C "$CU" -c user.name=sentinelle -c user.email=s@local commit -qm "resynchro outils en service" && a sync "copie usine resynchronisée (elle avait dérivé des outils en service)"
RF=$(find "$B"/NOUVEAUX_* -name 'acceptation*.out' -mmin -180 -exec grep -l "REFUS" {} + 2>/dev/null); NR=$(echo "$RF" | grep -c .); NA=$(find "$B"/NOUVEAUX_* -name 'acceptation*.out' -mmin -180 2>/dev/null | wc -l)
[ "$NR" -ge 4 ] && [ $((NR * 2)) -gt "$NA" ] && D="$B/NOUVEAUX_DIAG_$(date +%Y%m%d%H)" && [ ! -d "$D" ] && ! ls -d "$B"/NOUVEAUX_DIAG_* -mmin -360 >/dev/null 2>&1 && { mkdir -p "$D"; echo "$RF" > "$D/REFUS.txt"; sed "s/@LOT@/$(basename "$D")/g" "$B/CONSIGNES_GLM/DIAGNOSTIC_REFUS.txt" > "$D/COMMUN.txt"; : > "$D/P1.txt"
  printf '#!/bin/sh\nB="$(cd "$(dirname "$0")/.." && pwd)"; sh "$B/../CLOTURE_20260927/glm_restreint.sh" "$B/../.." ".context/RADAR/%s" 1\n' "$(basename "$D")" > "$D/file_travail.sh"
  python3 "$B/../BUILD_V3_2026-09-25/detache.py" "$D/lancer.out" sh "$B/lancer.sh" "$D" >/dev/null; a refus "$NR refus sur $NA acceptations en 3 h → diagnostic GLM lancé ($(basename "$D"))"; }
[ "${QG:-99}" -lt 85 ] && for pc in tiktok:COMMUN_TIKTOK_BRIEF $([ "${QG:-99}" -lt 75 ] && echo savespace:COMMUN_SAVESPACE mailbox:COMMUN_MAILBOX); do python3 "$B/../BUILD_V3_2026-09-25/detache.py" "$B/vague_${pc%%:*}.out" sh "$B/vague_auto.sh" "${pc%%:*}" "${pc#*:}" >/dev/null; done  # étapes suivantes auto
O=$(for P in savespace mailbox tiktok usine; do python3 -c "import json,sys;[print(sys.argv[1],k) for k,v in json.load(open(sys.argv[2])).items() if v.get('etat')=='accepte']" $P "$B/$P/mf_etat/file.json" 2>/dev/null; done | while read P I; do grep -q "\"id\": \"$I\"" "$B/OMBRE.jsonl" 2>/dev/null || echo "$P $I"; done | head -1)
[ "${QG:-99}" -lt 60 ] && [ -n "$O" ] && ! pgrep -f "^sh .*ombre_seul\.sh" >/dev/null && python3 "$B/../BUILD_V3_2026-09-25/detache.py" "$B/ombre.out" sh "$B/ombre_seul.sh" $O >/dev/null  # comparaison IA seule, 1 à la fois
O2=$(grep -o '"produit": "[a-z]*", "id": "[A-Z0-9_]*"' "$B/OMBRE.jsonl" 2>/dev/null | sed 's/"produit": "//; s/", "id": "/ /; s/"$//' | while read P I; do grep -q "\"id\": \"$I\"" "$B/OMBRE_MSA.jsonl" 2>/dev/null || echo "$P $I"; done | head -1)
[ "${QG:-99}" -lt 60 ] && [ -n "$O2" ] && ! pgrep -f "^sh .*ombre_msa\.sh" >/dev/null && python3 "$B/../BUILD_V3_2026-09-25/detache.py" "$B/ombre_msa.out" sh "$B/ombre_msa.sh" $O2 >/dev/null  # 3e camp : mini-swe-agent
sh "$B/relanceur.sh"; echo "$(date '+%F %T') ronde faite" >> "$L"
