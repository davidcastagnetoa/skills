# ADR-007: Estructura de monorepo

- **Estado**: accepted
- **Fecha**: 2026-03-03
- **Autores**: software-architecture-agent

## Contexto

El sistema VerifID tiene multiples componentes: backend Python (FastAPI + modulos ML), frontend movil (React Native), frontend web, infraestructura (Docker, K8s, Helm), documentacion y scripts. Se necesita decidir si estos componentes viven en un unico repositorio (monorepo) o en repositorios separados (multi-repo).

## Opciones Evaluadas

### Opcion A: Monorepo
- Pros: cambios atomicos entre backend y frontend, refactorings transversales en un solo PR, CI/CD unificado, busqueda global de codigo, un solo punto de verdad para toda la documentacion (CLAUDE.md, Agents.md, ADRs), mas facil para equipos pequenos.
- Contras: build times potencialmente largos si no se filtran paths, conflictos de merge mas frecuentes con equipos grandes, herramientas de build deben soportar paths selectivos.

### Opcion B: Multi-repo (backend, frontend, infra separados)
- Pros: independencia total entre equipos, builds aislados, permisos granulares por repositorio.
- Contras: cambios transversales requieren PRs coordinados en multiples repos, versionado de contratos API mas complejo, duplicacion de CI/CD, mas dificil mantener coherencia de documentacion.

## Decision

**Monorepo** con la siguiente estructura:

```
verifid/
├── backend/        # Python: FastAPI + modulos ML + tests
├── frontend/       # React Native (mobile) + Web
├── infra/          # Docker, K8s, Helm, chaos experiments
├── models/         # Pesos ML (gitignored, descargados via script)
├── docs/           # ADRs, plan, API docs
├── scripts/        # Setup, download, seed
├── skills/         # Claude Code skills (project-local)
├── .claude/        # Claude Code agents (project-local)
└── .github/        # CI/CD workflows
```

Para un equipo de tamano pequeno-mediano, el monorepo simplifica drasticamente la coordinacion. Los contratos entre backend y frontend (schemas Pydantic ↔ TypeScript types) se validan en el mismo PR. La documentacion arquitectonica (ADRs, Agents.md) esta junto al codigo que describe.

## Consecuencias

- GitHub Actions se configura con `paths` filters para ejecutar solo los jobs afectados por cada PR (ej: cambios en `backend/` solo ejecutan tests de Python).
- Los modelos ML (~1-2GB) no se commitean; se descargan via `scripts/download-models.sh` y estan en `.gitignore`.
- Si el equipo crece significativamente (> 15 personas), se reevaluara la decision hacia multi-repo con un schema registry compartido.
- Se usa `pyproject.toml` en `backend/` y `package.json` en `frontend/` como raices de cada sub-proyecto.
