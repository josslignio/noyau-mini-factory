#!/usr/bin/env python3
"""Lance une commande dans SA PROPRE SESSION — elle survit à la mort de la session Claude.

Constat du 24/09 : nohup ne suffit pas ; quand le processus Claude Code s'arrête, tout son
arbre est tué. start_new_session=True détache le petit-fils du groupe ET de la session.
"""
import os, subprocess, sys
from pathlib import Path
sortie = Path(sys.argv[1])
cmd = sys.argv[2:]
f = sortie.open("ab")
p = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                     start_new_session=True, close_fds=True,
                     env={**os.environ, "FACTORY_NO_REAL_ENGINE": "1"})
print(f"detache pid={p.pid} sid_propre sortie={sortie}")
