---
name: waf_modsecurity
description: Web Application Firewall para detectar y bloquear ataques SQL injection, XSS y otros OWASP Top 10
type: Tool
priority: Esencial
mode: Self-hosted
---

# waf_modsecurity

ModSecurity con el ruleset OWASP CRS (Core Rule Set) actúa como WAF delante del API KYC. Analiza cada petición HTTP en busca de patrones maliciosos y bloquea automáticamente los más peligrosos.

## When to use

Activar antes de exponer el API en producción. El CRS en modo `DetectionOnly` primero, luego `Prevention` tras revisar los falsos positivos.

## Instructions

1. Usar Nginx con ModSecurity v3 (módulo dinámico):
   ```dockerfile
   FROM openresty/openresty:alpine
   RUN apk add --no-cache git gcc musl-dev make &&        git clone --depth 1 -b v3/master https://github.com/SpiderLabs/ModSecurity &&        cd ModSecurity && ./build.sh && ./configure && make && make install
   ```
2. Alternativamente, usar Coraza WAF (implementación Go de ModSecurity, más moderna):
   ```bash
   docker pull ghcr.io/corazawaf/coraza-proxy-wasm:latest
   ```
3. Descargar OWASP CRS:
   ```bash
   wget https://github.com/coreruleset/coreruleset/archive/v4.0.0.tar.gz
   tar -xzf v4.0.0.tar.gz
   ```
4. Configuración inicial en modo DetectionOnly:
   ```nginx
   modsecurity on;
   modsecurity_rules_file /etc/nginx/modsecurity/modsecurity.conf;
   # SecRuleEngine DetectionOnly (audit, no block)
   # Cambiar a: SecRuleEngine On (producción)
   ```
5. Reglas CRS específicas para KYC: deshabilitar reglas que bloquean uploads de imagen base64 (pueden activar falsos positivos).
6. Monitorizar `modsec_audit.log` durante 2 semanas en DetectionOnly para identificar falsos positivos antes de activar Prevention.

## Notes

- El CRS en `Paranoia Level 1` (por defecto) tiene pocos falsos positivos. Level 2+ requiere más tuning.
- Los campos de imagen en base64 son grandes y activan reglas de tamaño — ajustar `SecRequestBodyLimit` a 20MB.
- Integrar los logs del WAF con Grafana Loki para correlacionar ataques bloqueados con las métricas de seguridad.