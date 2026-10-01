#!/bin/sh
# BOUCLE DE CORRECTION (propriétaire 29/09 : « à fond ») : GLM ne peut pas exécuter ses juges ; on lui rend la SORTIE RÉELLE
# de la matrice d'acceptation (refus mesuré) et il corrige UNE fois ; puis ré-acceptation. Usage : corriger_lot_glm.sh <lot> <ID> <produit>
B="$(cd "$(dirname "$0")" && pwd)"; R="$B/../.."; N="$B/$1"; ID="$2"; P="$3"; cd "$B"
A="$N/$ID/acceptation.out"; [ -f "$A" ] || { echo "$(date +%T) pas d'acceptation à corriger" >> "$N/FILE.log"; exit 1; }
mkdir -p "$N/passes_initiales"; mv "$N"/P*.txt "$N"/Q*.txt "$N"/_DONE_*.txt "$N/passes_initiales/" 2>/dev/null
E0=$(python3 -c "import yaml,sys;print(\" \".join(sorted(yaml.safe_load(open(sys.argv[1])).get(\"a_faire_passer\") or [])))" "$N/$ID/contrat.yaml" 2>/dev/null)
{ echo "PASSE DE CORRECTION — $ID. La matrice d'acceptation a REFUSÉ ton jalon. Voici sa sortie réelle (fin) :"; echo '```'; tail -40 "$A"; echo '```'; echo 'Échecs pytest réels (JUnit) :'; grep -h -o '<failure message="[^"]*' "$N/$ID"/acceptation/*/j.xml 2>/dev/null | cut -c1-300 | head -20
  echo "Corrige UNIQUEMENT ce qui est refusé, dans $1/$ID/ (contrat.yaml, test_*.py, honnete.patch.md, triche*.patch.md). Rappels : a_faire_passer = ROUGES sur le code ACTUEL,"
  echo "a_garder_verts = VERTS sur le code ACTUEL (relis le code avant d'écrire l'attendu) ; blocs « ancien » copiés À L'OCTET ; une triche doit faire échouer une assertion."
  echo "SI un test échoue par « PermissionError: juge isolé » : ton juge OUVRE, IMPORTE ou COMPILE le livrable dans son propre processus — interdit ; lis-le ou exécute-le en SOUS-PROCESSUS (subprocess : cat, sys.executable -c)."
  echo "SI le refus vient du « --test-only du noyau » : lis le RECEIPT.json et les rapports junit du run cité dans la sortie ; le noyau rejoue ton juge DANS SON BAC (HOME neuf, réseau coupé, PATH réduit, le processus du juge n'ouvre JAMAIS un livrable) : un test vert dans la matrice mais rouge dans le noyau dépend de l'environnement — rends-le indépendant."
  echo "CODE DE RÉFÉRENCE (le SEUL qui compte) : .context/RADAR/$P/copie à HEAD — l'acceptation rejoue tes blocs « ancien » sur CETTE version : recopie-les à l'octet depuis SES fichiers, jamais depuis une autre copie ; chemins relatifs à SA racine, dans « livrables »."
  echo "écris chaque fichier IMMÉDIATEMENT avec l'outil d'écriture, un fichier à la fois ; ne rédige AUCUNE réponse longue. Puis $1/_DONE_1.txt."; } > "$N/P1.txt"
sh "$R/.context/CLOTURE_20260927/glm_restreint.sh" "$R" ".context/RADAR/$1" 1 || exit 1
mv "$A" "$A.refus1"; timeout 3000 python3 accepter_jalon.py "$P/projet" "$P/copie" "$N/$ID" > "$A" 2>&1
E1=$(python3 -c "import yaml,sys;print(\" \".join(sorted(yaml.safe_load(open(sys.argv[1])).get(\"a_faire_passer\") or [])))" "$N/$ID/contrat.yaml" 2>/dev/null)
if [ -n "$(for e in $E0; do echo " $E1 " | grep -qF " $e " || echo x; done)" ] && grep -q "ACCEPTÉ" "$A"; then MF_ETAT="$B/$P/mf_etat" python3 ../ACTIF/mini_factory/mf.py regler "$ID" bloque --raison "exigence RETIRÉE par la correction GLM (id a_faire_passer disparu) : revue avant construction" >> "$N/FILE.log" 2>&1; echo "$(date +%T) EXIGENCE MODIFIÉE → jalon bloqué pour revue" >> "$N/FILE.log"; fi
echo "$(date +%T) acceptation après correction : $(grep -E 'ACCEPTÉ|REFUS' "$A" | tail -1 | cut -c1-200)" >> "$N/FILE.log"
