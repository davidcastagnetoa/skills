---
name: semantic_release
description: Versionar automáticamente el proyecto basándose en los commits convencionales
---

# semantic_release

`semantic-release` lee los mensajes de commit en formato Conventional Commits y determina automáticamente la próxima versión semántica (major.minor.patch), genera el CHANGELOG y publica el release.

## When to use

Usar para versionar el sistema KYC y las imágenes Docker. Cada merge a `main` que pase CI genera un nuevo release automáticamente.

## Instructions

1. Instalar: `npm install --save-dev semantic-release @semantic-release/changelog @semantic-release/git`
2. Configurar `.releaserc.json`:
   ```json
   {
     "branches": ["main"],
     "plugins": [
       "@semantic-release/commit-analyzer",
       "@semantic-release/release-notes-generator",
       "@semantic-release/changelog",
       ["@semantic-release/exec", {
         "publishCmd": "docker tag kyc-api kyc-api:${nextRelease.version} && docker push kyc-api:${nextRelease.version}"
       }],
       "@semantic-release/git"
     ]
   }
   ```
3. Convenciones de commit (ver skill `conventional_commits`): `feat:` → minor, `fix:` → patch, `feat!:` → major.
4. Ejecutar en CI tras merge a main: `npx semantic-release`.
5. El tag de la versión en Git permite hacer `helm upgrade kyc --set image.tag=v1.2.3` con versión específica.

## Notes

- Nunca tagear versiones manualmente — dejar que semantic-release sea la única fuente de verdad.
- La versión `0.x.y` indica que la API puede tener breaking changes — pasar a `1.0.0` al estabilizar el contrato.