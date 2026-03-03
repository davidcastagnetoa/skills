---
name: owasp_top10_mitigations
description: Implementar protecciones estándar contra las vulnerabilidades más comunes del OWASP Top 10
type: Algorithm
priority: Esencial
mode: Self-hosted
---

# owasp_top10_mitigations

El OWASP Top 10 define las vulnerabilidades de seguridad más críticas en aplicaciones web. Para un sistema KYC que procesa datos biométricos, mitigar estas vulnerabilidades es obligatorio antes de cualquier despliegue en producción.

## When to use

Implementar como checklist de seguridad antes de cada release a producción. Incluir en las fitness functions del pipeline CI/CD.

## Instructions

1. **A01 - Broken Access Control**: implementar RBAC (ver skill `rbac`), validar ownership de sesiones (`session.user_id == jwt.sub`).

2. **A02 - Cryptographic Failures**: usar AES-256-GCM para datos en reposo (ver skill `aes_256_gcm`), TLS 1.3 en tránsito, nunca MD5/SHA1 para datos sensibles.

3. **A03 - Injection**: usar SQLAlchemy ORM (nunca f-strings en queries SQL), Pydantic para validación de inputs, parameterized queries siempre.
   ```python
   # NUNCA hacer esto:
   query = f"SELECT * FROM sessions WHERE id = '{session_id}'"
   # SIEMPRE usar ORM o parámetros:
   result = await db.execute(select(Session).where(Session.id == session_id))
   ```

4. **A05 - Security Misconfiguration**: deshabilitar endpoints de debug en producción (`app = FastAPI(docs_url=None, redoc_url=None)` si la API es privada), eliminar headers que revelan versiones del servidor.

5. **A06 - Vulnerable Components**: `pip-audit` + Trivy en CI (ver skills correspondientes), actualizar dependencias mensualmente.

6. **A07 - Identification and Authentication Failures**: JWT RS256 con expiración corta (ver skill `jwt_rs256_validation`), rate limiting en endpoints de auth (ver skill `rate_limiting_gateway`).

7. **A09 - Security Logging and Monitoring Failures**: structlog + Prometheus + Alertmanager (ver skills de audit y observabilidad).

8. **A10 - Server-Side Request Forgery (SSRF)**: validar que URLs proporcionadas por clientes no apuntan a IPs internas:
   ```python
   import ipaddress
   def validate_no_ssrf(url: str):
       host = urllib.parse.urlparse(url).hostname
       ip = ipaddress.ip_address(socket.gethostbyname(host))
       if ip.is_private or ip.is_loopback:
           raise HTTPException(400, "SSRF attempt blocked")
   ```

## Notes

- Ejecutar OWASP ZAP en modo pasivo contra staging antes de cada release para detectar issues automáticamente.
- El OWASP ASVS Level 2 es el estándar de referencia para sistemas KYC — mapear cada control del ASVS a su implementación en el código.
- Documentar en un ADR las decisiones de mitigación de riesgo cuando no se puede implementar un control OWASP al 100%.