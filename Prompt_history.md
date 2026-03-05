revisa el contenido del proyecto actual, sobretodo el archivo CLAUDE.md, deseo desarrollar el proyecto, pero no dispongo de todas las skilles, solo algunas, en teoria el proyecto requiere 213 skilles (ver `231_list_skills.md`) pero solo dispongo de las listadas en la carpeta `list_skills`.

1. Verifica que las skiles disponibles sean suficientes.
2. Verifica que los agentes listados en `Agents.md` sean suficientes.
3. Si faltan skilles, crealas crealas en una carpeta llamada `pending_skills`.
4. Indicame como crear los agentes o hazlo tu mismo (tanto los agentes como las skilles son locales, es decir solo para el proyecto actual) NO GLOBALES.
5. Una vez disponga de las skilles y los agentes indicame como iniciar el desarrollo del proyecto.

NO respondas todas las peticiones a la vez, en cuanto acabes una pide confirmacion para la siguiente.
Aun no escribas codigo, primero quiero definidir el proceso que se llevara paso a paso (genera un plan de desarrollo detallado cuando ya se dispongan de todas las skiles y agentes necesarios).

---

Debido al limite diario, no has creado todas las skilles necesarias. Crea las skilles faltantes en la carpeta `pending_skills`. Cuando termines de crear las skilles faltantes. pasamos los siguientes pasos :

- 4. Indicarme como crear los agentes o hacerlo tu mismo (tanto los agentes como las skilles son locales, es decir solo para el proyecto actual) NO GLOBALES.
- 5. Una vez disponga de las skilles y los agentes indicame como iniciar el desarrollo del proyecto.

Recuerda: NO respondas todas las peticiones a la vez, en cuanto acabes una pide confirmacion para la siguiente.
Aun no escribas codigo, primero quiero definidir el proceso que se llevara paso a paso (genera un plan de desarrollo detallado cuando ya se dispongan de todas las skiles y agentes necesarios).

Las skills faltantes son:

- health_monitor_agent (1)
  - chaos_engineering (separada de chaos_toolkit)

- observability_agent (5)
  - prometheus (separada de prometheus_grafana)
  - grafana (separada de prometheus_grafana)
  - opentelemetry_sdk (separada de opentelemetry_jaeger)
  - jaeger (separada de opentelemetry_jaeger)
  - thanos

- database_agent (3)
  - postgresql (separada de postgresql_sqlalchemy_async)
  - pgbouncer (separada de pgbouncer_asyncpg)
  - pgbackrest

- architecture_agent (1)
  - adr_tools (separada de adr_framework)

---

🍺

guarda el plan en uno o varios archivos markdown, debido a las restrincciones y al limite diario, hazlo por partes de tal forma que se pueda continuar en caso de /rate-limit-options - out of extra usage

---

Debido al limite diario te has quedado en Phase 4.2 — Observability.

Has creado/actualizado los archivos:
Write(infra/nginx/nginx.conf)
Write(infra/nginx/lua/auth.lua)
Write(infra/nginx/lua/circuit_breaker.lua)
Write(infra/nginx/lua/circuit_breaker_log.lua)
Write(infra/nginx/ssl/generate-dev-certs.sh)
Write(infra/nginx/Dockerfile)
Update(infra/docker/docker-compose.yml)
Write(backend/infrastructure/metrics.py)

Te quedas a medio camino en :
Write(backend/infrastructure/middleware.py)  
 ⎿  Wrote 51 lines to backend/infrastructure/middleware.py

Verifica los checkpoints en `docs/plan/04-production-infra.md` Continua.

---

has terminado Phase 4 — Production Infrastructure, y lo has documentado en `docs/plan/04-production-infra.md` en los checkpoints correspondientes. Continua

---

Debido al limite diario te has quedado en Phase 5 — Frontend
Has creado/actualizado los archivos:
Write(frontend/mobile/package.json)
Write(frontend/mobile/tsconfig.json)
Write(frontend/mobile/app.json)
Write(frontend/mobile/app/types.ts)
Write(frontend/mobile/app/navigation/AppNavigator.tsx)
Write(frontend/mobile/app/screens/WelcomeScreen.tsx)
Write(frontend/mobile/app/screens/SelfieCapture.tsx)
Write(frontend/mobile/app/screens/ActiveChallenges.tsx)
Write(frontend/mobile/app/screens/DocumentCapture.tsx)
Write(frontend/mobile/app/screens/ProcessingScreen.tsx)
Te quedas a medio camino en :
Write(frontend/mobile/app/screens/ResultScreen.tsx)  
 ⎿  Wrote 107 lines to frontend/mobile/app/screens/ResultScreen.tsx

Verifica los checkpoints en `docs/plan/05-frontend.md` y Continua.
