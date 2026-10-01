"""Test du test : chaque correctif v8 (rounds 1 et 2) retiré doit faire rougir son test. Copie jetable sous _mut/.
Rejeu : python3 _mutation_v8.py (v9 lot B : 3 mutants --apres retirés avec la fonction, 9 ajoutés) — aucun moteur, aucun noyau lancé en vrai, aucun mutant de code qui tue."""
import shutil, subprocess, sys
from pathlib import Path
W = Path(__file__).resolve().parent
K, J, SB, MF = "cand_v8/factory_v3/run.py", "cand_v8/factory_v3/juge_isole.py", "cand_v8/factory_v3/bornage.sb", "mini_factory/mf.py"
CT = "cand_v8/tests/v3/conftest.py"  # v9 relecture Codex n°7 : fixture adaptée, corrigée avec le noyau
M = [  # (fichier, fragment actuel, remplacement, filtre -k)
 # ---- round 1 ----
 (SB, '(if (equal? (param "NET") "0") (allow file-read* (subpath (param "CONTROL"))))', '(allow file-read* (subpath (param "CONTROL")))', "test_a_f1_bornage"),
 (K, 'os.path.relpath(real(self.repo), real(ROOT)).split("/")[0] in ("..", ".context")', 'real(self.repo) != real(ROOT)', "test_a_f1_depot"),
 (K, 'f"contrat touché : {len(viol)} violation(s), liste dans reçu contrat.violations"', 'f"contrat touché : {viol[:10]}"', "test_b1_motif"),
 (K, 'rc={r.returncode}")', 'rc={r.returncode} {r.stderr.decode(errors=\'replace\')}")', "test_b1_motif"),
 (MF, '([mo.group(1) for mo in re.finditer(r"(?m)^\\[v3\\] reçu (\\S+)$", p.stdout)] or [None])[-1]', '([mo.group(1) for mo in re.finditer(r"\\[v3\\] reçu (\\S+)", p.stdout)] or [None])[0]', "test_b1_b9_mf"),
 (MF, 'and Path(recu).parent.name == R["run_uuid"]', 'and True', "test_b1_b9_mf"),
 (MF, ' and sha_noyau() == h else None', ' else None', "test_b1_b9_mf"),
 (MF, 'ok = ok and R.get("hash_contrat") == t.get("hash_contrat")', 'ok = ok', "test_b1_b9_mf"),
 (K, '"PYTHONDONTWRITEBYTECODE": "1", ', '"PYTHONPYCACHEPREFIX": str(d / "pyc"), ', "test_b2"),
 (K, '"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",', '', "test_b2"),
 (K, 'q = lire_quota(pool) if self.moteur else None', 'q = lire_quota(pool)', "test_c_a7"),
 (K, 'exiger(free >= 10.0,', 'exiger(free >= float(os.environ.get("FACTORY_MIN_FREE_GB", 10)),', "test_c_a7"),
 (K, '            if self.R["quota"]:\n                self.R["quota"]["pct_apres"]', '            if rc and not usage.get("complet") and any(e.get("type") == "error" for e in lire_jsonl(self.run / "engine.log")): raise abort("panne")\n            if self.R["quota"]:\n                self.R["quota"]["pct_apres"]', "test_b5"),
 (J, 'max(st, self.cas.get(report.nodeid, st), key=PIRE)', '"fail" if self.cas.get(report.nodeid) == "fail" else st', "test_b6"),
 (K, 'return c == jid or c.startswith((jid + "::", jid + "[", jid + "/"))', 'return c == jid or c.startswith(jid)', "test_b6"),
 (K, '        (self.run / "CONTRAT.json").write_bytes(c)\n', '', "test_b7_contrat"),
 (K, 'min(int(m.get("timeout_s") or 600), BUDGET_MAX)', 'int(m.get("timeout_s") or 600)', "test_b7_contrat"),
 (K, '    ap.add_argument("--budget-s", type=int)\n', '    ap.add_argument("--budget-s", type=int)\n    ap.add_argument("--essai", type=int)\n', "test_b8"),
 (MF, 'for f in [d / n for n in FICHIERS]', 'for f in [d / "run.py"]', "test_b9_mf_empreinte"),
 (MF, 'os.environ.get("MF_NOYAU", "")', 'os.environ.get("MF_NOYAU", "python3 x/run.py")', "test_b9_r2_mf_noyau"),
 (MF, '            if x.id not in F:\n', '            if False:\n', "test_b9_r2_mf_noyau"),
 (MF, 'if hash_contrat(t) != t.get("hash_contrat"):', 'if False:', "test_b9_mf_contrat"),
 (K, 'b""))), daemon=True)', 'b""))))', "test_c_a1"),
 (K, "        finally:  # C:A1", "        except BaseException: raise\n        if True:  # C:A1", "test_c_a1"),
 (K, '            signal.signal(s, signal.SIG_IGN)', '            pass', "test_c_a3"),
 (K, '            os.close(self.lockfd)', '            pass', "test_c_a3"),  # v13 : le verrou est un flock rendu par close (remplace le mutant unlink)
 (K, ', *self.run.glob("t_*"))', ')', "test_c_a5"),
 (K, 'self.run / "engine" / "tmp", *self.run.glob', 'self.run / "engine" / "tmp", self.run / "engine" / "verdict_x", *self.run.glob', None),
 ("cand_v8/factory_v3/moteurs/glm.json", '"signal_2": "SIGKILL"', '"signal_2": "SIGTERM"', "test_c_a6"),
 (K, 'mono = time.monotonic', 'mono = lambda: time.monotonic() + float(os.environ.get("FACTORY_V3_NOW_MONOTONIC_OFFSET_S") or 0)', "test_b8_essai"),
 # ---- round 2 ----
 (K, '        support.ecrire_octets(self.run / f"verdict_{phase}.json", bytes(lu))', '        (d / "verdict.json").write_bytes(lu)', "test_r2_verdict"),
 (K, '        support.ecrire_octets(self.run / f"verdict_{phase}.json", bytes(lu))', '        support.ecrire_octets(d / "verdict.json", bytes(lu))', "test_r2_verdict"),
 (K, 'if self.jouer_tests("apres2") != p1 or rc == 124:', 'if self.jouer_tests("apres2")[1] != cases:', "test_b3_r2"),
 (K, 'if self.jouer_tests("apres2") != p1 or rc == 124:', 'if self.jouer_tests("apres2") != p1:', "test_b3_r2"),
 (SB, '(if (equal? (param "NET") "1")\n    (allow file-read* (literal (string-append (param "RUN") "/CONSIGNE.md"))', '(if #t\n    (allow file-read* (literal (string-append (param "RUN") "/CONSIGNE.md"))', "test_r2_bornage"),
 (K, 'exiger(cfg.get("actif", True) is not False,', 'exiger(True,', "test_r2_codex_inactif", "test_codex_v8.py"),
 (K, 'if mag and not (os.path.islink(home / mag) and os.readlink(home / mag) == real(Path.home() / mag)):', 'if False:', "test_r2_lien", "test_codex_v8.py"),
 (K, 'if mag and not (os.path.islink(home / mag) and os.readlink(home / mag) == real(Path.home() / mag)):', 'if mag and not os.path.exists(home / mag):', "test_r2_lien", "test_codex_v8.py"),
 (K, 'home = None if f.motif_echec in ("magasin remplacé", "panne_moteur") else self.run / "engine" / "home"', 'home = self.run / "engine" / "home"', "test_c_a5_r2"),
 (MF, 'for f in [d / n for n in FICHIERS] + sorted((d / "moteurs").glob("*.json")):', 'for f in sorted(x for x in d.rglob("*") if x.is_file()):', "test_r2_mf_empreinte_fichiers"),
 (MF, 'if x.cmd in ("ajouter", "suivant") and not NOYAU:', 'if not NOYAU:', "test_b9_r2_mf_noyau"),
 (MF, '    ok = ok and "test_only" not in ((R.get("noyau") or {}).get("flags") or [])\n', '', "test_r2_mf_recu_refuse"),
 (MF, 'return ok and (R.get("verdict") != "VERT" or (rc == 0 and bool((R.get("commit") or {}).get("sha"))))', 'return ok', "test_r2_mf_recu_refuse"),
 (MF, '(rc == 0 and bool((R.get("commit") or {}).get("sha")))', '(rc == 0)', "test_r2_mf_recu_refuse"),
 (MF, '    with contextlib.suppress(OSError, ValueError, TypeError, AttributeError, KeyError):  # R2/R3', '    if True:  # R2/R3', "test_r2_mf_recu_refuse"),
 (MF, '    with contextlib.suppress(subprocess.TimeoutExpired):\n        p = subprocess.run(argv, capture_output=True, text=True, timeout=120)', '    if True:\n        p = subprocess.run(argv, capture_output=True, text=True, timeout=120)', "test_r2_mf_hash_contrat"),
 # ---- round 3 ----
 (MF, "        lu = json.loads(Path(recu).read_text())\n        R = lu if recevable(lu, t, recu, p.returncode) and sha_noyau() == h else None", "        R = json.loads(Path(recu).read_text())\n    R = R if recevable(R, t, recu, p.returncode) and sha_noyau() == h else None", "test_r3_mf_recu_mal_type"),
 (MF, '    ok = ok and all(isinstance(R.get(k) or {}, dict) for k in ("noyau", "commit", "engine"))\n', '', "test_r3_mf_recu_mal_type"),
 (MF, '    ok = ok and isinstance(R.get("verdict"), str) and isinstance(R.get("run_uuid"), str)', '    ok = ok', "test_r3_mf_recu_mal_type"),
 (MF, 'capture_output=True, text=True, timeout=DELAI_S)', 'capture_output=True, text=True)', "test_r3_mf_appel"),
 (MF, '    except subprocess.TimeoutExpired:\n        p = types.SimpleNamespace', '    except ZeroDivisionError:\n        p = types.SimpleNamespace', "test_r3_mf_appel"),
 (MF, '"noyau": h, "mf": MF_SHA, "base_sha"', '"noyau": h, "base_sha"', "test_r3_mf_preuve"),
 # ---- v9 (sonde vidéo n°9, Codex Q2 n°8/n°9) ----
 (SB, "(allow process-fork)\n(allow process-exec\n", "(allow process-fork)\n(allow process-exec)\n(allow process-exec\n",
  "test_v9_bornage_exec"),
 (K, '            git(self.repo, "archive", "--format=tar", "-o", str(tar), self.R["base_sha"], "--", *paths)',
  '            subprocess.run([GIT, "-C", str(self.repo), *SAFE_GIT, "archive", "--format=tar", "-o", str(tar),'
  ' self.R["base_sha"], "--", *paths], env=GIT_ENV)', "test_k5", "test_durci_v7.py"),
 (K, "            tar.unlink(missing_ok=True)", "            pass", "test_k5", "test_durci_v7.py"),
 (MF, "DELAI_S = 6 * 5400", "DELAI_S = 9000", "test_r3_mf_appel"),
 # ---- v9 lot B (élagage) : borne exacte, refus donnees, index dérivé, lecteur tolérant, C12 ----
 (MF, "DELAI_S = 6 * 5400", "DELAI_S = 6 * 5400 * 1000", "test_r3_mf_appel"),
 (K, 'exiger("donnees" not in j,', 'exiger(not j.get("donnees"),', "test_v9_juge_donnees"),
 (K, 'final = [derives.get(x.get("run_uuid"), x) for x in lignes]', 'final = [x for x in lignes]', "test_v9_index"),
 (K, '.get("schema") == SCHEMA and R.get("verdict") not in', '.get("schema") != 0 and R.get("verdict") not in',
  "test_v9_index"),
 (K, 'R.get("verdict") not in (None, "RUNNING") and (u :=', 'R.get("verdict") is not None and (u :=', "test_v9_index"),
 (K, "            with contextlib.suppress(ValueError):\n                out.append", "            if True:\n                out.append",
  "test_jsonl_tronque", "test_v3_sans_moteur.py"),
 (K, 'durable = (support.read_json(r.run / "RECEIPT.json") or {}).get("verdict") not in (None, "RUNNING")',
  'durable = False', "test_b7_index", "test_v3_trous.py"),
 (J, "    sys.addaudithook(garde)\n", "    pass\n", "test_v9_juge_isole"),
 (J, "    sys.exit(int(rc))", "    sys.exit(0)", "test_v9_juge_isole"),
 # ---- v9 relecture Codex n°7 (Q1, 28-29/09) : 3 corrections ----
 (MF, 'if t.get("apres"):', 'if False and t.get("apres"):', "test_v9_mf_apres_non_vide_refuse_jamais_ignore"),
 (CT, "r.returncode == 0 and r.stdout.strip() == '3'", "r.stdout.strip() == '3'", "test_v9_conftest_mod_rouge_exige_rc0"),
 # ---- v10 (besoin propriétaire 29/09) : regler pret→bloque, raison obligatoire, en_cours hors de portée ----
 (MF, '"pret": ("bloque",)}', '}', "test_v10_regler_pret_vers_bloque"),
 (MF, '"pret": ("bloque",)}', '"pret": ("bloque",), "en_cours": ("bloque",)}', "test_v10_regler_en_cours_toujours_refuse"),
 (MF, 'if x.vers not in TRANS.get(t["etat"], ()):', 'if False:', "test_v10_regler_pret_vers_pret_refuse"),
 # ---- v13 (01/10, croisement 3 IA + B2/B2bis/B2ter/B2q, GO Codex) ----
 (K, '            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)', '            pass', "test_flock_tenu", "test_b2_2.py"),
 (K, '        if viol:  # B:1', '        if not touches and not (self.run / "engine.log").read_bytes().strip(): raise abort("panne", "panne_moteur")  # noqa\n        if viol:  # B:1', "test_violation_jugee_avant_panne", "test_b2bis_1.py"),
 (K, '.split("[", 1)[0] for i in', ' for i in', "test_dernier_rouge_noms_seuls", "test_b2ter_3.py"),
 (K, '        if rouges := getattr(self, "rouges_precedents", ()):', '        if rouges := ():', "test_dernier_rouge_noms_seuls", "test_b2ter_3.py"),
 (K, 'x.get("verdict") == "ROUGE" and x.get("base_sha") == base)', 'x.get("verdict") == "ROUGE")', "test_rouge_autre_base", "test_b2ter_3.py"),
 (K, ', x.get("essai") or 0)', ')', "test_egalite_finished_at", "test_b2q_4.py"),
 # ---- v14 (01/10, B6/B6bis/B6ter, GO Codex) : panne moteur ≠ essai ----
 (K, 'if not touches and (u == 0 or', 'if (u == 0 or', "test_fichier_touche_journal_erreur_pas_panne", "test_v14_complements.py"),
 (K, '(ev := lire_jsonl(self.run / "engine.log")) and all(', '(ev := lire_jsonl(self.run / "engine.log")) or all(', "test_journal_vide_usage_absent_pas_panne", "test_b6ter_9.py"),
 (K, 'all(e.get("type") == "error" for e in ev)', 'any(e.get("type") == "error" for e in ev)', "test_journal_mixte_usage_absent_pas_panne", "test_v14_complements.py"),
 (K, 'home = None if f.motif_echec in ("magasin remplacé", "panne_moteur") else', 'home = None if f.motif_echec in ("magasin remplacé",) else', "test_home_moteur_conserve_sur_panne", "test_b6bis_8.py"),
 (MF, 'if d.get("technique")) < 3 else "bloque"', 'if d.get("technique")) < 9 else "bloque"', "test_1re_2e_panne_pret_3e_bloque", "test_b6bis_8.py"),
 (MF, 't["demarrages"][-1]["technique"] = True', 'pass', "test_panne_repassse_pret_budget_intact", "test_b6_7.py"),
 (MF, 'if not d.get("technique")) >= t["essais"]:', 'if True) >= t["essais"]:', "test_historique_mixte_budget_non_technique", "test_b6_7.py"),
]
res = []
for i, (f, a, b, t, *fic) in enumerate(M):
    if t is None:
        continue
    d = W / "_mut"
    shutil.rmtree(d, ignore_errors=True)
    shutil.copytree(W / "cand_v8", d / "cand_v8", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(W / "mini_factory", d / "mini_factory", ignore=shutil.ignore_patterns("__pycache__"))
    p = d / f; s = p.read_text()
    assert s.count(a) >= 1, (i, f, a)
    p.write_text(s.replace(a, b, 1))
    r = subprocess.run([sys.executable, "-m", "pytest", "-c", "/dev/null", "--rootdir", ".", "-q", "-p", "no:cacheprovider",
                        "-x", "-k", t, *(fic or ["test_durci_v8.py"])],
                       cwd=d / "cand_v8/tests/v3", capture_output=True, text=True, timeout=300,
                       env={"PATH": "/usr/bin:/bin", "HOME": str(Path.home()), "PYTHONDONTWRITEBYTECODE": "1"})
    last = (r.stdout.strip().splitlines() or ["?"])[-1]
    res.append((i, t, v := "ROUGE" if " failed" in last else "INVALIDE" if r.returncode else "VERT(!)", last))
    print(i, t, v, last, flush=True)
shutil.rmtree(W / "_mut", ignore_errors=True)
print("mutants", len(res), "tués", sum(x[2] == "ROUGE" for x in res))
