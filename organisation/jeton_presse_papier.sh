#!/bin/sh
# Enregistre le jeton Claude COPIÉ (Cmd+C) sans le coller nulle part. Les espaces et retours à la ligne sont retirés. Presse-papiers vidé ensuite.
F="$HOME/conductor/workspaces/Jocelyn-factory-control/factory-foundation-v2/.context/BUILD_V3_2026-09-25/.env_claude"
T=$(pbpaste | tr -d ' \t\r\n')
case "$T" in
  *export*|*CLAUDE_CODE*) T=$(printf '%s' "$T" | sed 's/.*=//') ;;
esac
case "$T" in
  sk-ant-*) [ ${#T} -ge 90 ] || { echo "Le jeton copié est trop court (${#T} caractères) : sélectionne bien les 2 lignes du jeton, Cmd+C, et relance."; exit 1; }
            umask 077; printf 'CLAUDE_CODE_OAUTH_TOKEN=%s\n' "$T" > "$F"; chmod 600 "$F"; printf '' | pbcopy
            echo "OK : jeton enregistré (${#T} caractères). Presse-papiers vidé." ;;
  *) echo "Le presse-papiers ne contient pas de jeton Claude (il doit commencer par sk-ant-). Sélectionne le jeton, Cmd+C, puis relance."; exit 1 ;;
esac
