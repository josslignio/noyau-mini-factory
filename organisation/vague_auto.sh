#!/bin/sh
# PLANIFICATEUR AUTO (propriétaire 01/10 : « autopilot ») : un produit sans étape prête/en cours ni lot actif → GLM écrit les 2 prochaines
# consignes d'après SA roadmap et ce qui est déjà accepté, puis la mini-factory les prépare (juge dans le bac, correction auto) et l'enchaîneur construit.
B="$(cd "$(dirname "$0")" && pwd)"; R="$B/../.."; P="$1"; C="$2"; cd "$B"; N="NOUVEAUX_PLAN_${P}_$(date +%Y%m%d%H%M)"
[ "$(grep -cE '"etat": "(pret|en_cours)"' "$P/mf_etat/file.json" 2>/dev/null)" -ge 2 ] && exit 0  # 01/10 : planifie pendant la construction
[ "$(python3 -c "import json,sys,time;d=json.load(open(sys.argv[1]));d=d.get('items',d);T=lambda x:max([e.get('t','') for e in (x.get('reglages') or [])+(x.get('demarrages') or [])] or ['1970-01-01 00:00:00']);print(sum(x.get('etat')=='bloque' and time.time()-time.mktime(time.strptime(T(x),'%Y-%m-%d %H:%M:%S'))<21600 and not any(j!=k and j.startswith(k) and v.get('etat')=='accepte' for j,v in d.items()) for k,x in d.items()))" "$P/mf_etat/file.json" 2>/dev/null || echo 9)" -ge 4 ] && exit 0  # anti-boucle (BN0C…BN0H) : ≥ 4 bloqués DE MOINS DE 6 h ; 01/10 « enchaîne direct » : les vieux bloqués n'arrêtent plus le plan
pgrep -f "^sh .*lot_glm_decoupe\.sh NOUVEAUX_${P}_|^sh .*NOUVEAUX_PLAN_${P}_" >/dev/null && exit 0
[ -n "$(find . -maxdepth 1 -name "NOUVEAUX_PLAN_${P}_*" -mmin -60)" ] && exit 0; mkdir -p "$N"
{ echo "Tu es le planificateur (GLM). Ni shell ni sous-agent. Tu LIS ; tu écris SEULEMENT dans .context/RADAR/$N/ (_DONE_1.txt à SA RACINE). Fichiers ≤ 14 lignes, un à la fois, aucune réponse longue."
  echo "Produit $P : roadmap .context/RADAR/$P/copie/docs/ROADMAP.yaml ; déjà fait = jalons « accepte » de .context/RADAR/$P/mf_etat/file.json et code de .context/RADAR/$P/copie (CODE DE RÉFÉRENCE) ; échecs à ne pas répéter : jalons « bloque » du même fichier."
  case $P in savespace) DOC=DISK_CLEAN;; mailbox) DOC=INBOX_CLEAN;; *) DOC=TIKTOK;; esac
  echo "PLAN DÉTAILLÉ (autorité si présent) : .context/$DOC/PLAN_DETAILLE.md — la consigne REPREND l'étape du plan (livrable, interface, critères) sans rien inventer."
  echo "Format EXACT d'une consigne : .context/RADAR/CONSIGNES_GLM/DN0A.txt. UN livrable par étape, testable hors ligne, le juge ne lit JAMAIS le livrable dans son processus (sous-processus seulement)."
  echo "PASSE 1 — écris $N/CONSIGNE_<ID>.txt pour les DEUX prochaines étapes non faites de la roadmap (ID = id de la roadmap + lettre, ex. DN1A ; une étape de la roadmap qui a DÉJÀ un jalon dans file.json, même bloqué, n'est JAMAIS réécrite : passe à la suivante), puis $N/ORDRE.txt (« ID » par ligne), puis $N/_DONE_1.txt."; } > "$N/COMMUN.txt"; : > "$N/P1.txt"
sh "$R/.context/CLOTURE_20260927/glm_restreint.sh" "$R" ".context/RADAR/$N" 1 || exit 1
while read ID; do [ -f "$N/CONSIGNE_$ID.txt" ] || continue; cp "$N/CONSIGNE_$ID.txt" "CONSIGNES_GLM/$ID.txt"; L="NOUVEAUX_${P}_A_$ID"; mkdir -p "$L"
  printf '#!/bin/sh\nB="$(cd "$(dirname "$0")/.." && pwd)"; cd "$B"; sh lot_glm_decoupe.sh %s %s %s CONSIGNES_GLM/%s.txt CONSIGNES_GLM/%s.txt\n' "$L" "$ID" "$P" "$C" "$ID" > "$L/file_travail.sh"
  python3 "$R/.context/BUILD_V3_2026-09-25/detache.py" "$L/lancer.out" sh "$B/lancer.sh" "$B/$L" >/dev/null; echo "$(date '+%F %T') plan auto $P : $ID lancé" >> "$B/SENTINELLE.log"; done < "$N/ORDRE.txt"
