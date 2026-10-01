# Croisement après B1 (GLM G/AVIS.md, Codex CODEX.txt, Claude C_CLAUDE.md) — 01/10 11:25
UNANIME : corriger les pièces en service ; aucune pièce nouvelle, aucun outil externe ; réécriture B1 arrêtée.
FAIT DU PILOTE (opérateur) : après kill -9 du noyau, mf laisse l'item « inconnu » ; c'est le PILOTE qui l'a remis « pret » (PILOTE.sh:59) → en production, arrêt muet. Le 7/7 ne prouve PAS la reprise automatique.
LOT B4 (mf.py, release v14 sur VRAIE copie) — retenu à ≥ 2/3 :
 C1 reprise d'un « en_cours » orphelin (GLM 1-2, Claude 1, Codex 1-2) : sonder le flock du noyau (verrou TENU → laisser en_cours) ; libre → lire le reçu de CE démarrage sur disque (VERT → accepte ; ROUGE → règle normale ; absent/RUNNING → panne technique → pret) ; plafond technique 3 puis bloque.
 C2 panne technique ≠ échec métier dans mf (GLM 3, Codex B1ter P1 mf.py:102) : le budget d'essais ne compte que les démarrages non techniques.
 C3 statut lisible pendant un run (Codex 5).
Hors lot, petites corrections opérateur avec test : exigence retirée vérifiée AVANT acceptation (Codex 4) ; commit du juge annulé si --test-only refuse (GLM 5).
Différé (1 voix ou à mesurer) : identité canonique d'étape (Codex 3 / Claude 2), flock par produit dans chaine_mf (GLM 4, doublon à vérifier), retrait enchaineur_absence (GLM), écrivain caché de la sentinelle (Codex 8), reçus worktree (Codex 7).
Ménage : dossiers B1/B1bis/B1ter → musée (3 179 lignes, 0 promue).
