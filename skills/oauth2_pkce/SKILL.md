---
name: oauth2_pkce
description: Flujo OAuth 2.0 con PKCE para autenticación segura de clientes móviles
type: Protocol
priority: Recomendada
mode: Self-hosted
---

# oauth2_pkce

PKCE (Proof Key for Code Exchange) es la extensión de OAuth 2.0 recomendada para apps móviles y SPAs donde el client secret no puede guardarse de forma segura. Previene el ataque de interceptación del authorization code.

## When to use

Usar para el flujo de autenticación de la app móvil KYC. Para integraciones server-to-server (otros backends que llaman al API), usar API Keys directamente.

## Instructions

1. Instalar Keycloak como authorization server self-hosted:
   ```yaml
   keycloak:
     image: quay.io/keycloak/keycloak:23.0
     command: start-dev
     environment:
       KC_DB: postgres
       KC_DB_URL: jdbc:postgresql://postgres:5432/keycloak
   ```
2. Crear realm `kyc`, client `kyc-mobile` con PKCE habilitado (`S256`).
3. Flujo en la app móvil:
   - Generar `code_verifier` (random 43-128 chars) y `code_challenge = BASE64URL(SHA256(code_verifier))`.
   - Redirigir a Keycloak con `code_challenge` y `code_challenge_method=S256`.
   - Tras autorización, canjear `code` + `code_verifier` por access_token (JWT RS256).
4. El JWT resultante contiene el `sub` del cliente y se valida con el skill `jwt_rs256_validation`.
5. Configurar `access_token_lifespan=15m` y `refresh_token_lifespan=8h` en Keycloak.

## Notes

- PKCE no requiere client_secret en la app — la seguridad proviene del code_verifier único por sesión.
- Keycloak puede federar con proveedores externos (LDAP, Active Directory) si el cliente lo requiere.
- Para testing de la API (Postman, pytest), usar el flujo Client Credentials con API Key.
