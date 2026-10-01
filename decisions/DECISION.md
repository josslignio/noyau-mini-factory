# DÉCISION ARCHITECTURE — GLM, phase 3 (01/10). Décision, pas négociation.
Sources : PROGRAMME.md (exigences 1-4, exécution immédiate :26) ; croisements X=Codex croise.txt:14864-14964, G=CROISE.md (GLM), C=CROISE.md (Claude). Règle : tranché par preuve = RETENU ; disputé sans preuve = OUVERT (§12). Rien exécuté ; aucune écriture hors ce dossier.

## 1. ARCHITECTURE RETENUE — noyau corrigé + UNE machine d'états + launchd
- noyau ACTIF (run.py+juge_isole+support+bornage.sb, 910 l.) : preuve isolée, juge sous bac, reçus recalculables. 4 changements (§2), rien d'autre.
- ouvrier.py (~170 l., mf.py FUSIONNÉ, tué pas dupliqué — retenu aussi par C:17) : SEULE source d'état. États pret/en_cours/accepte/livre/echecs/a_decider ; issues typées ATTENTE_EXTERNE|REPRISE_TECHNIQUE|ECHEC_METIER ; genres construire/planifier/corriger/relire/integrer/ombre ; ID=(produit, étape roadmap) SANS suffixe lettre (X:14936 : « +lettre » contournait mf:128) ; budget CUMULÉ par étape logique ; tout état non-terminal porte prochaine_heure ; statut lu HORS verrou (mf.py:121 corrigé, décidé le 30/09 DECISIONS.md:9).
- alerteur.sh (≤12 l., launchd 15 min) : LECTURE SEULE, sens unique, 1 alerte/motif/h. Signale des FAITS : livrés/h=0, echecs>3 h, quota illisible, état sans prochaine_heure. JAMAIS de kickstart sur mtime (X:14930 : file.json n'est écrit qu'avant/après moteur — l'immobilité n'est pas la mort) ; la relance appartient à launchd seul.
- launchd : KeepAlive=true + ThrottleInterval + WatchPaths(ROADMAP+file.json). Plists actuels LUS par X:14928 : StartInterval 900/3600, RunAtLoad, AUCUN KeepAlive → nouveaux plists. Zéro kickstart croisé (Hermes lifecycle_guard.py:1-8).
- integrer.py (gardé, adapté O6) : écrit LIVRÉ — SEUL état terminal compté (X:14944 ; mf.py:15 rendait accepte terminal ; FC:1184 VERT non versés).
- accepter_jalon.py RÉDUIT à l'admission : prépare en zone temporaire, écrit UNE SEULE FOIS toutes vérifications passées (X:14940 : écrit avant admission → fenêtre de lancement non autorisée). Matrice via run.py --test-only étendu (§2d).
- Sauvegarde (rclone) + recherche : jobs launchd SÉPARÉS, essais bornés, hors livraison (G1 A1 : 26 h, ~78 essais, 0 effet).
Garanties par construction : un écrivain par file (flock, écritures seules) ; un superviseur (launchd) ; un juge (juge_isole sous bac) ; un état (file v2) ; une terminal comptée (LIVRÉ). Un produit de plus = 0 ligne.

## 2. NOYAU — 4 changements, chacun justifié par écrit (devise 1) et mutanté
a) AM1 verrou flock : O_EXCL « jamais purgé » (run.py:236,238) = verrou mort bloquant. −5/−7 l. M12.
b) Panne moteur ≠ échec métier : reçu SANS travail moteur (aucune sortie moteur — pas seulement la brièveté, X:14934) → ABORT panne_moteur, essai rendu, budget TECHNIQUE séparé du métier. Preuve : CHAINE.log:433-446, ROUGE 3-5 s vs ≥47 s de construction. M7.
c) Hash du contrat lié aux OCTETS du juge (run.py:180) : le gel juge ce qui est gelé. M11.
d) --test-only étendu à la matrice complète (base+honnête+triches) : l'actuel s'arrête après la base (run.py:616, X:14938) — sinon l'admission rejuge hors bac (12 runs perdus, FC:1206). Justification écrite de l'ajout : ferme un trou prouvé ET tue le 2e juge d'accepter_jalon — solde en lignes négatif.

## 3. CE QU'ON RETIRE (→ .context/MUSEE_ORCHESTRATION/, rien effacé ; C:20 concorde)
33 pièces ≈510-620 l. (liste G3 §2) : sentinelle, enchaineur_absence, chaine_mf, vague_auto, relanceur, lancer, relecture_bloques, controle_horaire, usine_nuit*, file_job, tableau.py, debloquer_quota, lot_glm_decoupe, corriger_lot_glm, acceptations_*, jetons, revue_periodique, reprise/relance_corrections ; + 47 fichiers .alerte_*, drapeaux _LANCE/_FINI/_ESSAIS/_ABANDON. mf.py fusionné-tué. Double comptabilité d'essais (lot vs file) : collapse sur la file.

## 4. CE QU'ON PREND AILLEURS (comparer puis prendre — CLAUDE.md §5b)
- launchd KeepAlive/WatchPaths/ThrottleInterval : 0 ligne (man launchd.plist(5)).
- Hermes, 3 règles, 0 ligne : interdiction de respawn-loop ; hash d'octets avant réveil (monitor.py:1-11) ; inactivité ≠ temps mur.
- Symphony : états+réconciliation avant dispatch+backoff plafonné, en COMPORTEMENT (~15 l.), pas l'Elixir.
- mini-swe-agent : CHALLENGER épinglé, jamais adopté d'office (X:14948 : bornage.sb:8 autorise des binaires — équivalence non prouvée).
- Ancienne factory, en comportement : quota_live.py officialisée (SEULE lecture quota) ; UNKNOWN≠0 dans tout verdict ; waste PAR CAUSE (motif_echec, run.py:109) ; sémantique safe-restart (2 signaux, fail-closed) avant tout bootout.

## 5. TEMPORAL — tranché CONTRE, par preuves (2 vs 1)
(a) X limite sa propre proposition : « estimation de conception », serveur/stockage/dépendances comptés à part, « gain économique encore à démontrer » (X:14958).
(b) Le rejeu existe déjà (reçus + index run.py:102-114) ; le trou réel est la découverte du reçu via stdout (mf.py:65, X:14926) — on répare CE trou (ouvrier lit RECEIPT sur disque), on n'achète pas un serveur.
(c) Un serveur+DB = un store d'état de plus — la maladie mesurée de l'ancienne (9 magasins, C:10).
(d) STRATEGY_CTO.md:95 interdit leurs runtimes ; licence non vérifiée (C:14).
(e) §5b : ADAPT = code upstream dans l'arbre ET du nôtre supprimé — importer un serveur sans mesurer ce qu'il retire viole la règle.
Réouverture UNIQUEMENT si le banc de charge (§9) montre flock+launchd insuffisant (O1).

## 6. LIGNES AVANT/APRÈS (estimations ; recompte OBLIGATOIRE en B8 au périmètre mesuré X:14905)
AVANT : noyau 910/4 + mf 149/1 + RADAR 1139/41 = 2198 l./46 pièces.
APRÈS visé : orchestration ≤665 l./11 pièces (ouvrier ~170, alerteur ~12, accepter_jalon ~90, integrer 238, glm_restreint 18, tableau_bord 28, verrouiller 7, remplacer 7, ombres ~36) ; noyau 910±15.
Promesse mesurable (devise 4) : baisse ≥40 % des lignes d'orchestration AU MÊME PÉRIMÈTRE, publiée avant/après — jamais un absolu.

## 7. BASCULE — chaque retrait : étape unique, mutantée, mesurée, réversible (PROGRAMME.md:26)
B0 point zéro : copie musée r0 ; mesures avant (LIVRÉ/h 72 h par produit, pièces/lignes, incidents 36 h).
B1 ouvrier.py+alerteur.sh+convertisseur v2↔v1 AVEC inverse, posés par remplacer.sh, À SEC (FACTORY_NO_REAL_ENGINE=1) : M1-M13 doivent passer sur l'honnête ET rougir sur leur mutant. Un mutant mou = banc menteur = STOP.
B2 noyau §2 (a-d), un changement par jour maximum, chacun avec mutant et rollback .avant_.
B3 pilote UN produit, genre construire : handover = DRAIN — ARRET posé, attente « aucune construction en vol » (X:14954 : ARRET n'est lu qu'avant lancement) PUIS transfert exclusif ; launchd charge ouvrier+alerteur ; kill -9 hebdo programmé (M1 joue seul). Critère : LIVRÉ/h pilote ≥70 % de sa base 72 h ET quota/livré ≤110 % — sinon retour arrière écrit et rejoué à sec.
B4-B5 genres corriger/relire puis planifier (24 h chacun ; M5, M6, puis M3 en production : 100 % d'ids uniques/24 h).
B6 généralisation 1 produit/jour ; « 0 ligne par produit » mesurée par diff.
B7 bootout sentinelle+enchaineur, SEULEMENT si prérequis : items ombre vivants, alerteur couvre quota/plafonds/témoin de verrou, aucune file en_cours à l'instant T. Plists conservés.
B8 retrait des 33 pièces + recompte lignes/pièces + LIVRÉ/h avant/après ; convertisseur archivé ALORS seulement.
B9 tenue : 48 h sans commit ni intervention (LONG_RUN_PROOF_2) puis 7 j avec renouvellements de quota.
Abandon : 2 retours arrière sur la MÊME étape = défaut de conception → retour complet, diagnostic écrit, pas de 3e essai.

## 8. ÉPREUVES — un vert ne compte que si le banc sait rougir (devise 4)
M1 EN VIE : kill -9 ouvrier → relancé ≤10 s, 0 item perdu (mutant : KeepAlive retiré → reste mort).
M2 ORPHELIN : en_cours + pilote tué → RÉCONCILIATION (X:14924 : jamais de reset aveugle) : reçu VERT sur disque → accepte ; reçu partiel → reprise au dernier pas PROUVÉ ; rien → pret, démarrages intacts (mutant : reset aveugle → rouge).
M3 ANTI-BOUCLE : id existant réajouté, tout état tout suffixe → REFUS ; 50 renommages → budget cumulé constant, 0 nouvel ID actif.
M4 DÉLIVRE : masquer un reçu ou une intégration → LIVRÉ/h baisse.
M5 AMÉLIORE : ROUGE → item corriger posé auto ; 2× même motif → echecs + relire (mutant : pose désactivée → rouge).
M6 PAS D'ATTENTE MUELTE : echecs 3 h sans ligne d'alerte → rouge.
M7 PANNE MOTEUR : 2 pannes consécutives → 0 échec métier, retard borné (mutant : recompter ROUGE → rouge).
M8 RÉVERSIBLE : chaque étape rejouée à rebours ; bijection file v2↔v1 relisible par l'ANCIEN mf.py.
M9 LIVRÉ : kill entre VERT et intégration → ni livré perdu ni publié deux fois.
M11 GEL-JUGE : juge modifié après épinglage → REFUS.
M12 VERROU : détenteur tué → verrou libéré (mutant : retour O_EXCL → rouge).
M13 ADMISSION : matrice jouée hors bac système → REFUS.

## 9. TENUE ET MONTÉE EN CHARGE (X:14962 retenu)
Fautes injectées d'abord : SIGKILL ouvrier/noyau, reboot machine, disque plein, reçu tronqué, coupure après CHAQUE écriture puis après CHAQUE publication ; un reçu durable demeure reconnu, un ancien worker ne peut plus publier.
Charge : 1→3→10→30 produits, 100 items en attente, 100 000 reçus ; mesurer p95 admission/statut, RSS, disque, débit LIVRÉ/h, équité, coût de réconciliation. Concurrence : 20 demandes du même jalon → 1 seul claim ; un écrivain par dépôt ; chaos hermétique (jamais les processus de prod). Anomalie de contrôle détectée ≤60 s.

## 10. COMPARAISON PERMANENTE (exigence 4) — un GENRE de la file, pas une intention
Ombre corrigée D'ABORD (sélection déterministe ; mêmes Git+juges+base+budget+oracle caché ; commentaires exacts — l'actuelle est invalide, X:14950). Camps : GLM seul / noyau / mini-swe-agent / Temporal en banc isolé. Ordre randomisé, répétitions, ÉCHECS INCLUS. Publication : qualité du constructeur et fiabilité de l'orchestrateur mesurés SÉPARÉMENT. Un challenger ne remplace rien sans gain hors échantillon.

## 11. MESURE (exigence 3)
METRIQUES.jsonl dérivé des reçus + LIVRÉ : livrés/h, réussite au 1er coup logique, minutes+quota PAR LIVRÉ (préparation et intégration comprises), waste PAR CAUSE, pannes, boucles, interventions, taux de reprise (échec→accepté). UNKNOWN≠0 dans TOUT verdict machine (FC:1221 : « RAS » pendant l'arrêt). « En vie » se mesure UNIQUEMENT par livrés/h + états de file (X:14932 : des lancements avaient lieu pendant le prétendu « arrêt total » de 148 min).

## 12. POINTS OUVERTS — chacun avec la preuve qui le tranchera
O1 Temporal : banc de charge §9 aux cibles ; si flock+launchd insuffisant → réouverture écrite.
O2 mini-swe-agent : ombre appariée ≥10 tâches ; victoire mesurée → vendor, sinon reste challenger.
O3 LaunchAgents liés à la session macOS (doc Apple, X:14928) : test reboot SANS login ; s'ils ne démarrent pas → alternative documentée ou risque accepté par écrit par le propriétaire.
O4 Comportement exact de mf.py:89-92 (lecture divergente G1 vs X:14924) : relecture commune du code + M2 en banc. La cible (réconciliation avant reprise) est fixée quoi qu'il en soit.
O5 Cible ≤665/11 : recompte B8 au périmètre 2198/46 ; si la baisse mesurée est <40 %, c'est le PLAN qui est en défaut, pas la mesure.
O6 integrer.py : sélection par jalon sans version courante de contrat (integrer.py:97, X:14940) → épreuve de conflit en banc avant B4 ; LIVRÉ lié au contrat épinglé.
O7 Seuils (70 %, 110 %, 3 h, +10 min, ≤60 s, kill -9 hebdo) : hypothèses, à caler sur les mesures B0.

## 13. NON VÉRIFIÉ (dit, pas caché)
ouvrier.py, alerteur.sh, convertisseur N'EXISTENT PAS : aucune affirmation de tenue avant B1-B9 (devise 2 — une fausse garantie est pire que pas de garantie). Chiffres X repris de sa sortie, recoupés sur les points décisifs que j'ai lus directement (plists, run.py:616, mf.py:65/121/128, bornage.sb:8, CHAINE.log). Listes de retrait : estimations jusqu'au recompte B8. Rien exécuté pour cette décision.

## 14. CALENDRIER ACCÉLÉRÉ — décision du propriétaire 01/10 ~06:00 (« ça prend plus de temps que la création du noyau entier, c'est n'importe quoi »)
Le temps d'attente est remplacé par des épreuves de panne provoquées (plus fiables qu'une attente passive) ; les protections restent : épreuve mutante par garantie, pilote avant généralisation, retour arrière documenté.
- J0 (aujourd'hui) : B1 ouvrier/alerteur/épreuves à sec ; B2 les 4 corrections du noyau le MÊME jour, l'une après l'autre, chacune seulement si son mutant rougit ET la suite noyau reste verte.
- J0-J1 : B3 pilote 1 produit, 6 h avec pannes provoquées (kill -9 ouvrier et noyau, reçu tronqué, disque plein simulé, coupure après écriture) au lieu de 24 h d'attente.
- J1 : B4-B6 tous les produits dès que le pilote passe ; B7-B8 retrait des anciennes pièces au musée le même jour.
- En tâche de fond, sans bloquer l'usage : B9 preuve 48 h puis 7 jours.
Règle d'abandon inchangée : 2 retours arrière sur la même étape → arrêt et revue de conception.

## 15. MODE RADICAL — propriétaire 01/10 ~06:05 (« beaucoup plus vite, beaucoup plus radical et pragmatique »)
- PAS de phase pilote séparée : dès que les épreuves à sec de B1 passent (mutants compris) et que Codex ne dit pas NO-GO, bascule de TOUS les produits d'un coup ; retour arrière = recharger les 2 anciens plists (1 commande, testée avant).
- Noyau : les 2 corrections qui débloquent le débit tout de suite (panne moteur ≠ échec métier ; verrou flock), les 2 autres ensuite.
- Plus de scripts supplémentaires, plus d'audits : on bascule, on mesure (LIVRÉ/h vs 0,4/h au B0), on corrige.

## 16. BRIQUES « LEGO » — exigence du propriétaire depuis le début, rappelée 01/10 ~06:10
« Tout doit être détachable et complémentaire, comme des Lego d'un même moteur ; si un truc bug, on revient en arrière et on analyse pièce par pièce, comme un vrai CTO long terme ; code ultra épuré, efficace et bien pensé. »
Chaque brique = UN fichier, avec, dans .context/NOYAU_MF/BRIQUES.md : rôle unique ; entrée et sortie écrites (formats exacts) ; ce qu'elle ne fait JAMAIS ; ses épreuves propres (qui rougissent si elle casse) ; version active et version précédente (retour arrière = remplacer.sh sur CE fichier seul) ; sa mesure.
Briques : noyau (juge + construction isolée) · ouvrier (file d'état unique) · alerteur (observation, lecture seule) · accepter (admission d'un jalon) · intégrer (versement → LIVRÉ) · planifier (étapes suivantes) · comparer (ombres) · tableau (mesure). Aucune brique n'écrit l'état d'une autre ; elles ne communiquent que par la file de l'ouvrier et les reçus sur disque. Une brique remplacée = ses épreuves + les épreuves de contrat de ses voisines, rien d'autre à retester.

## 17. TRANCHÉ — vérification finale à 3 IA indépendantes (01/10 ~06:25) : UNANIMITÉ
Sources : VERIF_FINALE/{glm.md,codex.txt,claude.md}. Les 3 disent : architecture §1-§13 GO ; §15 « tous les produits d'un coup après épreuves à sec, retour = 2 plists » NO-GO (il contredit le verdict Codex qu'il cite, croise.txt:14913 ; le retour arrière ne restaure pas l'ÉTAT ; aucun cycle avec un vrai moteur). §15 est REMPLACÉ par :
1. MAINTENANT : B1 (ouvrier, alerteur, épreuves à sec) + 2 corrections noyau de débit (panne moteur ≠ échec métier ; verrou flock) + fermeture des 2 trous de preuve (juge figé sur ses octets ; matrice d'admission rejouée dans le bac), chacune mutantée et réversible.
2. PUIS UN produit pilote RÉEL, quelques heures : vraie livraison, pannes provoquées (kill -9 ouvrier et noyau, coupure après écriture), reprise, et RETOUR ARRIÈRE COMPLET éprouvé (programmes ET état : file convertie, budgets conservés, livrés non republiés), redémarrage sans session ouverte testé (O3).
3. PUIS extension rapide aux autres produits, un par un dans la même journée si le pilote tient.
RETIRÉ du plan (sur-ingénierie, 2 IA sur 3 ou plus) : charge à 30 produits/100 000 reçus (→ 3 produits + pannes suffisent, charge seulement si O1) ; Temporal comme camp courant ; kill -9 hebdo en production ; « une brique = un fichier » strict (→ interface stable et remplacement compatible) ; tailles arbitraires par fichier comme garanties (→ réduction globale mesurée).
AJOUTÉ (manques pointés) : cadence de comparaison budgétée (≥ 1 ombre appariée/jour, promotion du gagnant sur preuve) ; plafond des reprises techniques et attente quota avec réveil ; « ne s'arrête jamais » annoncé seulement après B9 ; règle d'abandon appliquée aussi à B9.

## 18. LA LOGIQUE DU NOYAU APPLIQUÉE À TOUTE LA MINI-FACTORY — propriétaire 01/10 ~06:20
Le noyau est solide parce qu'il est un ENTONNOIR : contrat fixé avant, frontière physique, gel, juge hors de portée, reçu recalculable, rien cru sur parole. Les mêmes 6 règles s'appliquent désormais à CHAQUE brique d'orchestration :
1. CONTRAT AVANT : l'interface (entrée, sortie, interdits) et les épreuves d'une brique sont écrites et figées AVANT son code ; son constructeur ne les écrit pas.
2. FRONTIÈRE : chaque brique a le minimum de droits (alerteur en lecture seule ; seul l'ouvrier écrit la file ; seul l'intégrateur écrit LIVRÉ ; aucune brique ne touche au juge).
3. GEL : la version en service de chaque brique est épinglée par son empreinte et notée dans chaque reçu.
4. JUGE : une brique n'entre en service que si SES épreuves passent ET que chaque mutant les fait rougir, joués par la MACHINE, jamais par le constructeur.
5. REÇU : chaque décision de l'orchestration (lancer, reprendre, bloquer, débloquer, livrer, alerter) écrit un reçu : faits lus, règle appliquée, résultat — recalculable par un tiers.
6. RIEN SUR PAROLE : l'orchestration ne décide QUE sur des faits (reçus, états, empreintes, quotas mesurés), jamais sur le texte d'une IA. Conséquence : le déblocage « Codex ET GLM disent DÉBLOQUER » (relecture_bloques.sh) est une décision sur du texte → à remplacer, dans l'ouvrier, par une décision sur faits (matrice d'admission rejouée dans le bac + empreinte du juge + épreuves mutantes), l'avis des IA restant consultatif.
