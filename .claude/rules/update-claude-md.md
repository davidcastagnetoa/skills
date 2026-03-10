---
description: Mantener CLAUDE.md actualizado con el contexto del proyecto
globs: **/*
---

# Regla: Actualizar CLAUDE.md al avanzar en el desarrollo

Cada vez que se complete una tarea de desarrollo significativa (nuevo módulo, endpoint, cambio arquitectónico, integración de servicio externo, cambio en el modelo de datos, nueva funcionalidad o decisión técnica relevante), DEBES actualizar el archivo `CLAUDE.md` en la raíz del proyecto.

## Qué actualizar

- **Modelo de datos**: si se añaden, modifican o eliminan entidades o campos en el schema de Prisma, reflejar los cambios en la sección "Modelo de Datos".
- **Endpoints REST**: si se crean o modifican endpoints, actualizar la sección "Endpoints REST Principales".
- **Stack tecnológico**: si se añade una nueva librería o servicio relevante, documentarlo en la sección correspondiente.
- **Estructura de archivos**: si se crean nuevos módulos o se reorganiza la estructura, actualizar el árbol de directorios.
- **Variables de entorno**: si se añaden nuevas variables requeridas, incluirlas en la sección de variables de entorno.
- **Algoritmos críticos**: si se implementa o modifica lógica de negocio crítica, documentar el algoritmo.
- **Decisiones arquitectónicas**: si se toma una decisión técnica importante, registrarla.
- **Convenciones**: si se establece una nueva convención, añadirla a la tabla de convenciones.
- **Requisitos no funcionales**: si cambian los requisitos de rendimiento, seguridad u observabilidad.

## Cómo actualizar

- Usar el tool `Edit` para modificar las secciones relevantes de CLAUDE.md.
- NO reescribir todo el archivo; solo editar las secciones afectadas.
- Mantener el formato y estructura existentes del documento.
- Ser conciso: documentar lo esencial sin redundancia.
- No eliminar información existente a menos que esté obsoleta o sea incorrecta.

## Cuándo NO actualizar

- Cambios triviales (typos, ajustes de formato, refactors menores sin impacto funcional).
- Trabajo exploratorio o de investigación que no produce cambios en el código.
