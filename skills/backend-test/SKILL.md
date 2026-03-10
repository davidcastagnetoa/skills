---
name: backend-test
description: Escribe tests unitarios e integracion para el backend Express + Prisma con Vitest y Supertest. Usar para anadir cobertura de tests al backend.
origin: ocralis
---

# Backend Test Skill

Escribe tests unitarios e integracion para el backend Express + Prisma.

## When to Activate

- Anadir tests a un servicio o controller existente
- Crear tests para un nuevo modulo
- Validar integraciones con APIs externas (mock)
- Verificar autenticacion y autorizacion en endpoints
- Mejorar cobertura de tests

## Setup

### Instalacion

```bash
cd ocralis_backend
npm install -D vitest supertest @vitest/coverage-v8
```

### vitest.config.js

```javascript
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    globals: true,
    environment: "node",
    coverage: {
      provider: "v8",
      reporter: ["text", "html"],
      include: ["services/**", "controllers/**", "utils/**"],
    },
  },
});
```

### Script en package.json

```json
{
  "scripts": {
    "test": "vitest",
    "test:run": "vitest run",
    "test:coverage": "vitest run --coverage"
  }
}
```

## Patrones de Test

### Test Unitario de Servicio

```javascript
// tests/services/geocoding.service.test.js
import { describe, it, expect, vi } from "vitest";
import { getCoordinates } from "../../services/geocoding.service.js";

describe("geocoding.service", () => {
  it("deberia devolver coordenadas para una direccion valida", async () => {
    const result = await getCoordinates({
      street: "Gran Via 1",
      postalcode: "28013",
      state: "Madrid",
      country: "Spain",
    });

    expect(result).toHaveProperty("latitude");
    expect(result).toHaveProperty("longitude");
    expect(typeof result.latitude).toBe("number");
  });

  it("deberia devolver null para direccion invalida", async () => {
    const result = await getCoordinates({ street: "xxxxxxxxxxx" });
    expect(result).toBeNull();
  });
});
```

### Test de Integracion de Endpoint

```javascript
// tests/routes/auth.routes.test.js
import { describe, it, expect } from "vitest";
import request from "supertest";
import app from "../../app.js";

describe("POST /api/auth/login", () => {
  it("deberia rechazar credenciales invalidas", async () => {
    const res = await request(app)
      .post("/api/auth/login")
      .send({ email: "noexiste@test.com", password: "wrongpass" });

    expect(res.status).toBe(401);
    expect(res.body.success).toBe(false);
  });

  it("deberia devolver tokens con credenciales validas", async () => {
    const res = await request(app)
      .post("/api/auth/login")
      .send({ email: "test@test.com", password: "password123" });

    expect(res.status).toBe(200);
    expect(res.body).toHaveProperty("accessToken");
    expect(res.body).toHaveProperty("refreshToken");
  });
});
```

### Test con Endpoint Protegido

```javascript
// tests/routes/employee.routes.test.js
import { describe, it, expect, beforeAll } from "vitest";
import request from "supertest";
import app from "../../app.js";

describe("GET /api/employees", () => {
  let token;

  beforeAll(async () => {
    const res = await request(app)
      .post("/api/auth/login")
      .send({ email: "test@test.com", password: "password123" });
    token = res.body.accessToken;
  });

  it("deberia rechazar sin token", async () => {
    const res = await request(app).get("/api/employees");
    expect(res.status).toBe(401);
  });

  it("deberia devolver lista con token valido", async () => {
    const res = await request(app)
      .get("/api/employees")
      .set("Authorization", `Bearer ${token}`);
    expect(res.status).toBe(200);
    expect(res.body.success).toBe(true);
    expect(Array.isArray(res.body.data)).toBe(true);
  });
});
```

### Mock de Prisma

```javascript
import { vi } from "vitest";

vi.mock("../../prismaClient.js", () => ({
  prisma: {
    usuario: {
      findUnique: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
    },
    employee: {
      findMany: vi.fn(),
      findUnique: vi.fn(),
      create: vi.fn(),
    },
    company: {
      findMany: vi.fn(),
      findUnique: vi.fn(),
    },
    // ... otros modelos segun necesidad
  },
}));
```

### Mock de Servicio Externo

```javascript
import { vi } from "vitest";

vi.mock("../../services/saltra.service.js", () => ({
  darAlta: vi.fn().mockResolvedValue({ success: true, naf: "123456789012" }),
  darBaja: vi.fn().mockResolvedValue({ success: true }),
  consultarNSS: vi.fn().mockResolvedValue({ nss: "123456789012" }),
}));
```

## Estructura de Tests

```
ocralis_backend/tests/
├── services/
│   ├── geocoding.service.test.js
│   ├── saltra.service.test.js
│   ├── ai.service.test.js
│   ├── storage.service.test.js
│   └── documentType.service.test.js
├── controllers/
│   ├── auth.controller.test.js
│   ├── employee.controller.test.js
│   └── company.controller.test.js
├── routes/
│   ├── auth.routes.test.js
│   ├── employee.routes.test.js
│   └── company.routes.test.js
└── utils/
    ├── distance.test.js
    └── token.test.js
```

## Convenciones

| Concepto | Convencion |
|----------|-----------|
| Framework | Vitest (compatible con ES Modules) |
| HTTP testing | Supertest con la app Express (`import app from "../../app.js"`) |
| Mocks | `vi.mock()` para Prisma y servicios externos |
| Naming | `{archivo}.test.js` |
| Descripciones | En espanol |
| Cobertura | Objetivo minimo 60% para servicios criticos |
| Estructura | `tests/{capa}/{archivo}.test.js` |

## Checklist

- [ ] vitest.config.js creado
- [ ] Scripts de test en package.json
- [ ] Tests unitarios para servicios criticos
- [ ] Tests de integracion para endpoints principales
- [ ] Mocks de Prisma y servicios externos
- [ ] Tests de autenticacion (con y sin token)
- [ ] Tests de validacion (datos invalidos)
- [ ] Cobertura >= 60%
