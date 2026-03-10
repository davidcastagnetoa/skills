---
description: Mantener README.md actualizado con documentación del proyecto
globs: **/*
---

# Regla: Actualizar README.md al crear o modificar archivos del proyecto

Cada vez que se cree un archivo nuevo significativo (controlador, servicio, módulo, componente, pantalla, configuración) o se modifique sustancialmente uno existente, DEBES actualizar el archivo `README.md` en la raíz del proyecto.

## Qué documentar en README.md

### Backend (apps/api/)

- **Módulos creados**: nombre, responsabilidad y archivos principales (controller, service, use-cases, repository).
- **Endpoints implementados**: método HTTP, ruta, descripción breve, autenticación requerida.
- **Guards y decoradores custom**: nombre y propósito.
- **Colas y jobs**: nombre de la cola, procesador, trigger y comportamiento.
- **Integraciones externas**: servicio (FCM, Cloud Storage, etc.), configuración requerida y cómo probarlo.

### Frontend Mobile (apps/mobile/)

- **Pantallas creadas**: ruta del archivo, propósito y navegación asociada.
- **Componentes reutilizables**: nombre, props principales y uso.
- **Hooks custom**: nombre, qué hace y dónde se usa.
- **Configuración de Expo**: plugins, permisos y assets relevantes.

### Frontend Web (apps/web/)

- **Páginas y rutas**: ruta del archivo y propósito.
- **Componentes**: nombre y uso.

### Instrucciones operativas

- **Cómo ejecutar en local**: comandos para backend, frontend mobile y web.
- **Variables de entorno necesarias**: listar con descripción (sin valores reales).
- **Cómo ejecutar tests**: comandos y cobertura esperada.
- **Cómo hacer deploy a producción**: pasos, servicios GCP involucrados.
- **Servicios externos integrados**: cómo configurarlos y probarlos localmente (Redis, PostgreSQL, FCM, etc.).
- **Seeds y migraciones**: cómo ejecutar seeds y migraciones de Prisma.

## Cómo actualizar

- Usar el tool `Edit` para modificar las secciones relevantes de README.md.
- Si README.md no existe, crearlo con una estructura base que incluya las secciones mencionadas.
- Mantener el formato Markdown consistente y legible.
- Agrupar la información por dominio (backend, mobile, web, infra).
- Incluir ejemplos de comandos cuando sea útil (ej: `npm run start:dev`, `npx prisma migrate dev`).

## Cuándo NO actualizar

- Cambios triviales que no afectan la comprensión del proyecto.
- Archivos de test (a menos que se establezca una nueva estrategia de testing).
- Ajustes de estilo o formato sin impacto funcional.
