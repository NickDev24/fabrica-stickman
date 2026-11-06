# CLEANUP_REPORT.md

Audit of source workspace `/home/facu/Documentos/Documentales-Generator` performed before
scaffolding `fabrica-stickman`. Only the final product (factory + CLI + 2D office +
connectors + docs) is included in the new repo.

## Excluded (not part of final product)

| Path | Reason | Action |
|------|--------|--------|
| `projects/` | User-generated documentary projects (content, not product) | Excluded |
| `state/` | Runtime caches, logs, LLM cache | Excluded |
| `models/` | TTS model binaries (large, gitignored) | Excluded |
| `assets/` (documentary) | Documentary assets, not product assets | Excluded |
| `vibe_images/` | Scratch image dumps | Excluded |
| `avatar_4f/` | Experimental avatar assets | Excluded |
| `youtube-mcp/` | Separate MCP server (keep as external dependency) | Excluded (reference only) |
| `stickman-video-director/` | Separate tool (referenced, not vendored) | Excluded |
| `factory/`, `pipeline/`, `scripts/`, `tools/`, `registry/`, `docker/` | Documentary pipeline internals | Excluded |
| `.env` | Secrets | Excluded (gitignored) |
| `*.onnx`, `*.onnx.json` | Large model files | Excluded (gitignored) |
| `.venv/`, `__pycache__/`, `.pytest_cache/` | Python artifacts | Excluded (gitignored) |
| `.freebuff/`, `.kilo/node_modules/` | Tool caches | Excluded (gitignored) |
| `tests/` (root) | Documentary pipeline tests | Excluded |
| `docs/` (root, existing) | Documentary docs | Replaced by new VitePress docs |

## Included (final product)

- `apps/web` — 2D office frontend (Vite + React + Phaser 3)
- `apps/cli` — publishable CLI
- `packages/agents-core` — dialogue engine
- `packages/connectors` — API/MCP/Skills/Zernio connectors
- `docs/` — VitePress documentation
- `.github/workflows/` — CI/CD
- Root config, README, LICENSE, CONTRIBUTING, etc.

## Action taken

New clean repository initialized at `/home/facu/Documentos/fabrica-stickman` pointing
to `https://github.com/NickDev24/fabrica-stickman.git`. No files deleted from the
source workspace; cleanup is achieved by *not* copying excluded paths.
