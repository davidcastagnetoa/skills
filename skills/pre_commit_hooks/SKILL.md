---
name: pre_commit_hooks
description: Ejecutar linting, formatting, type checking y seguridad automáticamente antes de cada commit
type: Tool
priority: Esencial
mode: Self-hosted
---

# pre_commit_hooks

`pre-commit` es un framework para gestionar hooks de Git que se ejecutan automáticamente antes de `git commit`. Garantiza que ningún código que no pase las validaciones llega al repositorio.

## When to use

Configurar en el `README.md` como paso obligatorio del setup del entorno de desarrollo. Cada developer ejecuta `pre-commit install` una vez al clonar el repositorio.

## Instructions

1. Instalar: `pip install pre-commit`
2. Crear `.pre-commit-config.yaml` en la raíz del repositorio (incluye black, ruff, mypy, bandit — ver skills correspondientes).
3. Añadir hooks adicionales de seguridad:
   ```yaml
   - repo: https://github.com/pre-commit/pre-commit-hooks
     rev: v4.5.0
     hooks:
       - id: check-merge-conflict
       - id: check-yaml
       - id: check-json
       - id: detect-private-key       # bloquear commits con claves privadas accidentales
       - id: no-commit-to-branch      # no commitear directamente a main
         args: [--branch, main]
       - id: end-of-file-fixer
       - id: trailing-whitespace
   - repo: https://github.com/Yelp/detect-secrets
     rev: v1.4.0
     hooks:
       - id: detect-secrets          # detectar secretos hardcodeados (tokens, passwords)
   ```
4. Instalar hooks: `pre-commit install && pre-commit install --hook-type commit-msg` (para commitlint).
5. Ejecutar sobre todo el repo: `pre-commit run --all-files`.
6. En CI: `pre-commit run --all-files` como primer step — falla rápido si hay problemas de formato.

## Notes

- `detect-private-key` y `detect-secrets` son críticos en un sistema KYC — previenen que claves de Vault o API keys lleguen al repositorio.
- `no-commit-to-branch: main` fuerza a trabajar siempre con feature branches y Pull Requests.
- Los hooks solo se ejecutan localmente — por eso también hay que ejecutarlos en CI (los desarrolladores pueden saltarse los hooks con `--no-verify`).