---
name: sonarqube
description: Análisis estático de código para detectar code smells, duplicación y cobertura de tests
type: Tool
priority: Recomendada
mode: Self-hosted
---

# sonarqube

SonarQube analiza el código Python en busca de code smells, complejidad ciclomática elevada, duplicación de código y coverage insuficiente. El Quality Gate bloquea merges que degradan la calidad del código.

## When to use

Implementar en la segunda iteración del proyecto, cuando ya hay tests y un pipeline CI/CD básico funcionando. SonarQube es complementario a ruff/mypy — detecta problemas de diseño que el linting no ve.

## Instructions

1. Arrancar SonarQube con Docker:
   ```yaml
   sonarqube:
     image: sonarqube:community
     ports: ["9000:9000"]
     volumes:
       - sonar_data:/opt/sonarqube/data
       - sonar_extensions:/opt/sonarqube/extensions
   ```
2. Crear proyecto `kyc-system` en la UI de SonarQube, obtener token.
3. Instalar scanner: `pip install sonar-scanner` o usar la acción de GitHub.
4. Configurar `sonar-project.properties`:
   ```properties
   sonar.projectKey=kyc-system
   sonar.sources=backend/
   sonar.tests=backend/tests/
   sonar.python.coverage.reportPaths=coverage.xml
   sonar.python.version=3.11
   ```
5. En CI: `sonar-scanner -Dsonar.host.url=http://sonarqube:9000 -Dsonar.token=$SONAR_TOKEN`
6. Configurar Quality Gate: fallar si coverage < 80%, duplicación > 3%, o hay issues bloqueantes nuevos.

## Notes

- SonarQube Community es gratuito y self-hosted. Para análisis de PRs individuales se necesita Developer Edition.
- Los code smells más relevantes para este proyecto: métodos con demasiados parámetros (señal de necesidad de refactoring), complejidad cognitiva > 15 en funciones de decisión.