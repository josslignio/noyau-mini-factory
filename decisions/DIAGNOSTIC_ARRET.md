# Reprise automatique après plantage — ARRÊT du 01/10 13:10 (4 NO-GO : B4, B4bis, B4ter, B5)
Constat : le problème n'est pas dans mf seul. Codex (NOUVEAUX_B5_REPRISE/CODEX_B5.txt) montre des trous dans trois pièces à la fois :
1. mf : VERT suivi d'un REFUS doublon → bloque (tri par finished_at) ; SIGKILL noyau avec mf vivant → « inconnu » jamais repris ; égalité False == 0 sur rc.
2. noyau : publication non idempotente — crash après création de branche, avant reçu final → publication sans VERT (run.py:~599).
3. fenêtre avant flock : un noyau suspendu avant son verrou fausse le budget.
Pourquoi 4 échecs : GLM écrit une machine à états SANS pouvoir exécuter ses tests (TEST_5 ne se collectait même pas : ModuleNotFoundError BANC_5).
Approche suivante (après renouvellement Claude, ven. 17:00) : constructeur QUI EXÉCUTE ses tests hermétiques (FACTORY_NO_REAL_ENGINE=1) dans la copie X_CAND, en TDD (épreuve rouge d'abord), Codex réfute ; périmètre : (a) noyau — publication idempotente par run_uuid, reçu final avant publication visible ; (b) mf — règles de reprise sur les seuls faits flock + reçu final du contrat, VERT prioritaire sur tout REFUS doublon ; (c) sentinelle — relancer la chaîne si une étape est en_cours/inconnu sans chaîne vivante.
Recherche à réutiliser : RECHERCHE/AILLEURS.md (12 systèmes : la preuve de vie est toujours tenue par un tiers qui survit).
En attendant : comportement prudent de la v13 conservé (étape « inconnu » → alerte, pas de relance aveugle). TROU CONNU ET NOMMÉ.
