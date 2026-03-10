---
name: express-endpoint
description: Crea endpoints Express siguiendo el patron Controller → Service → Prisma del proyecto Ocralis. Usar cuando se necesita un nuevo endpoint REST con validacion Zod, middleware de autenticacion y servicio.
origin: ocralis
---

# Express Endpoint Skill

Crea un nuevo endpoint Express siguiendo el patron del proyecto Ocralis.

## When to Activate

- Crear un nuevo endpoint REST en el backend
- Agregar operaciones CRUD para un recurso
- Integrar un nuevo modulo con validacion y autenticacion
- Extender un controller existente con nuevos handlers

## Patron Completo

### 1. Controller (`controllers/{modulo}.controller.js`)

```javascript
import { prisma } from "../prismaClient.js";
import logger from "../utils/logger.js";
import { z } from "zod";

// Schema de validacion Zod
const createSchema = z.object({
  nombre: z.string().min(1, "Nombre requerido"),
  email: z.string().email("Email invalido"),
  // campos con tipos y validaciones segun el recurso
});

export const create = async (req, res) => {
  try {
    // 1. Validar input con Zod
    const validated = createSchema.parse(req.body);

    // 2. Obtener usuario autenticado
    const usuario = req.user;

    // 3. Logica de negocio (llamar servicio si es externo)
    const result = await prisma.model.create({
      data: { ...validated, usuarioId: usuario.id },
    });

    // 4. Respuesta consistente
    res.status(201).json({ success: true, data: result });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return res.status(400).json({
        success: false,
        error: "Datos invalidos",
        details: error.errors,
      });
    }
    logger.error(error, "Error en create");
    res.status(500).json({ success: false, error: "Error interno del servidor" });
  }
};

export const list = async (req, res) => {
  try {
    const usuario = req.user;
    const items = await prisma.model.findMany({
      where: { usuarioId: usuario.id },
      orderBy: { createdAt: "desc" },
    });
    res.json({ success: true, data: items });
  } catch (error) {
    logger.error(error, "Error en list");
    res.status(500).json({ success: false, error: "Error interno del servidor" });
  }
};

export const getById = async (req, res) => {
  try {
    const { id } = req.params;
    const item = await prisma.model.findUnique({
      where: { id: parseInt(id) },
    });
    if (!item) {
      return res.status(404).json({ success: false, error: "No encontrado" });
    }
    res.json({ success: true, data: item });
  } catch (error) {
    logger.error(error, "Error en getById");
    res.status(500).json({ success: false, error: "Error interno del servidor" });
  }
};

export const update = async (req, res) => {
  try {
    const { id } = req.params;
    const validated = updateSchema.parse(req.body);
    const item = await prisma.model.update({
      where: { id: parseInt(id) },
      data: validated,
    });
    res.json({ success: true, data: item });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return res.status(400).json({
        success: false,
        error: "Datos invalidos",
        details: error.errors,
      });
    }
    logger.error(error, "Error en update");
    res.status(500).json({ success: false, error: "Error interno del servidor" });
  }
};

export const remove = async (req, res) => {
  try {
    const { id } = req.params;
    await prisma.model.delete({ where: { id: parseInt(id) } });
    res.json({ success: true, data: { message: "Eliminado correctamente" } });
  } catch (error) {
    logger.error(error, "Error en remove");
    res.status(500).json({ success: false, error: "Error interno del servidor" });
  }
};
```

### 2. Routes (`routes/{modulo}.routes.js`)

```javascript
import express from "express";
import { create, list, getById, update, remove } from "../controllers/{modulo}.controller.js";
import { authenticateToken } from "../middleware/auth.middleware.js";

const router = express.Router();

// Aplicar auth a todas las rutas del modulo
router.use(authenticateToken);

router.post("/", create);
router.get("/", list);
router.get("/:id", getById);
router.put("/:id", update);
router.delete("/:id", remove);

export default router;
```

### 3. Registrar en `app.js`

```javascript
import moduloRoutes from "./routes/{modulo}.routes.js";
app.use("/api/{modulo}", moduloRoutes);
```

### 4. Service externo (opcional) (`services/{modulo}.service.js`)

Solo crear si el endpoint necesita integrar con APIs externas (SALTRA, GCS, Gemini, etc.). Para operaciones CRUD puras con Prisma, la logica va directamente en el controller.

## Convenciones del Proyecto

| Concepto | Convencion |
|----------|-----------|
| Modulos | ES Modules (`import/export`, no `require`) |
| Prisma | `import { prisma } from "../prismaClient.js"` |
| Auth | `req.user` contiene el usuario autenticado (set por `authenticateToken`) |
| Respuestas | `{ success: true/false, data: ..., error: "mensaje" }` |
| Logging | Pino: `logger.info`, `logger.error`, `logger.debug` |
| Validacion | Zod inline en el controller |
| IDs | Integer autoincrement en Prisma |
| Errores Zod | Status 400 con `details: error.errors` |
| Errores 404 | `{ success: false, error: "No encontrado" }` |
| Errores 500 | `{ success: false, error: "Error interno del servidor" }` |

## Checklist

- [ ] Controller creado con try/catch y logging en cada handler
- [ ] Schema Zod para validacion de input (create y update)
- [ ] Routes con `authenticateToken` middleware
- [ ] Registrado en `app.js` con prefijo `/api/{modulo}`
- [ ] Service creado si hay integracion externa
- [ ] Respuestas consistentes (`success`/`data`/`error`)
- [ ] IDs parseados con `parseInt()` en params
- [ ] 404 para recursos no encontrados
- [ ] Actualizar README.md y README_CONTROLLERS.md
