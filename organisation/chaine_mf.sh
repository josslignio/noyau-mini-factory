#!/bin/sh
# ENCHAÎNEMENT SANS HUMAIN (autopilote 27/09) : mf suivant en boucle jusqu'à « rien de prêt », blocage, issue inconnue ou 8 tours. Vrais runs GLM.
# Autorisation : « jautorise tt oui » (17:40) — même noyau, même moteur, copies isolées, rien publié. Lancer par detache_reel.py.
R="$1"; P="${2:-job}"; B="$R/.context/RADAR"; L="$B/CHAINE.log"; A=$(cd "$R/.context/ACTIF" && pwd -P) || exit 3   # couple figé (Codex n°3)
[ -z "$FACTORY_NO_REAL_ENGINE" ] || { echo "$(date '+%H:%M:%S') REFUS : FACTORY_NO_REAL_ENGINE hérité" >> "$L"; exit 3; }
cd "$R" || exit 3; PL=$(python3 "$B/verifier_plafonds.py") || { echo "$(date '+%H:%M:%S') CHAÎNE ARRÊT : $PL" >> "$L"; exit 3; }   # plafonds à cliquet (28/09)
sh "$R/.context/BUILD_V3_2026-09-25/identifiants.sh" > /dev/null 2>&1; . "$R/.context/BUILD_V3_2026-09-25/.env_reel"; export ZAI_API_KEY
export MF_ETAT="$B/$P/mf_etat" MF_NOYAU="python3 $A/noyau/factory_v3/run.py" MF_MOTEURS_RELIES=glm
# REPLI (propriétaire 30/09 : « Codex reprend, puis Claude après Codex ») : 1er moteur à quota < 90 %, profil noyau actif.
q() { python3 "$R/factory_v2/quota_live.py" 2>/dev/null |
  awk -v m="^  $1 " '/^  [a-z]/{if(g)exit; if($0~m)g=1} g && /seven_day |weekly /{print int($3); exit}'; }
M=""; for m in glm codex claude; do Q=$(q $m)
  [ -n "$Q" ] && [ "$Q" -lt 90 ] && ! grep -q '"actif": *false' "$A/noyau/factory_v3/moteurs/$m.json" && { M=$m; break; }; done
[ -n "$M" ] || { echo "$(date '+%H:%M:%S') CHAÎNE ARRÊT : aucun moteur disponible (GLM, Codex, Claude)" >> "$L"; exit 3; }
[ "$M" = claude ] && . "$R/.context/BUILD_V3_2026-09-25/.env_claude" && export CLAUDE_CODE_OAUTH_TOKEN
export MF_MOTEUR_FORCE=$M MF_MOTEURS_RELIES=$M; [ "$M" = glm ] || echo "$(date '+%H:%M:%S') REPLI : moteur $M (GLM indisponible)" >> "$L"
echo "$(date '+%H:%M:%S') CHAÎNE début ; noyau $(shasum -a 256 "$A/noyau/factory_v3/run.py" | cut -c1-16)" >> "$L"
i=0; while [ $i -lt 8 ]; do
  i=$((i+1)); T0=$(date +%s)
  OUT=$(python3 "$A/mini_factory/mf.py" suivant 2>&1); RC=$?
  echo "$(date '+%H:%M:%S') [$P] tour $i rc=$RC durée=$(( $(date +%s) - T0 ))s : $(echo "$OUT" | head -1 | cut -c1-220)" >> "$L"
  echo "$OUT" | grep -q "aucun travail prêt" && { echo "$(date '+%H:%M:%S') CHAÎNE fin : rien de prêt" >> "$L"; break; }
  # 28/09 : un ROUGE/REFUS « bloque » est une issue CONNUE (jalon clos) → on passe au suivant ; seuls ABORT/inconnu arrêtent la chaîne
  echo "$OUT" | head -1 | grep -qE "→ (ROUGE|REFUS) \((bloque|pret)\)" && continue
  [ $RC -eq 0 ] || { echo "$(date '+%H:%M:%S') CHAÎNE ARRÊT : rc=$RC (blocage/inconnu, aucune relance)" >> "$L"; ECH=$RC; break; }
done
echo "$(date '+%H:%M:%S') CHAÎNE terminée ; processus avec cwd dans les copies : $(lsof -d cwd -Fn 2>/dev/null | grep -c "^n$B/.*/copie")" >> "$L"
exit ${ECH:-0}
