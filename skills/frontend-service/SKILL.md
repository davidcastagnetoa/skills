---
name: frontend-service
description: Crea servicios Axios para el frontend siguiendo el patron de company.service.ts. Usar para generar los servicios API faltantes (employee, establishment, tramite, ocr, payroll).
origin: ocralis
---

# Frontend Service Skill

Crea un servicio Axios para el frontend siguiendo el patron establecido en `company.service.ts`.

## When to Activate

- Crear un nuevo servicio frontend para comunicarse con la API
- Completar los servicios pendientes (employee, establishment, tramite, ocr, payroll)
- Agregar funciones de upload con FormData
- Conectar una pantalla con el backend

## Patron Base (`src/services/{modulo}.service.ts`)

```typescript
import api from "../lib/api";

// 1. Interfaces del modelo (mapean al schema Prisma)
export interface ModelName {
  id: number;
  nombre: string;
  // campos del modelo segun schema.prisma
  createdAt?: string;
  updatedAt?: string;
}

// 2. DTO para creacion (sin id, timestamps)
export interface CreateModelDto {
  nombre: string;
  // campos requeridos para creacion
}

// 3. DTO para actualizacion (todos opcionales)
export type UpdateModelDto = Partial<CreateModelDto>;

// 4. Funciones CRUD
export const getModels = async (): Promise<ModelName[]> => {
  const token = localStorage.getItem("accessToken");
  const response = await api.get("/api/{modulo}", {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data.data;
};

export const getModelById = async (id: number): Promise<ModelName> => {
  const token = localStorage.getItem("accessToken");
  const response = await api.get(`/api/{modulo}/${id}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data.data;
};

export const createModel = async (data: CreateModelDto): Promise<ModelName> => {
  const token = localStorage.getItem("accessToken");
  const response = await api.post("/api/{modulo}", data, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data.data;
};

export const updateModel = async (id: number, data: UpdateModelDto): Promise<ModelName> => {
  const token = localStorage.getItem("accessToken");
  const response = await api.put(`/api/{modulo}/${id}`, data, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data.data;
};

export const deleteModel = async (id: number): Promise<void> => {
  const token = localStorage.getItem("accessToken");
  await api.delete(`/api/{modulo}/${id}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
};
```

## Upload con FormData

```typescript
export const uploadFile = async (id: number, file: File): Promise<any> => {
  const token = localStorage.getItem("accessToken");
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post(`/api/{modulo}/${id}/upload`, formData, {
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
};
```

## Servicios Pendientes de Crear

| Servicio | Archivo | Funciones principales |
|----------|---------|----------------------|
| Employee | `employee.service.ts` | CRUD + `darAlta()` + `darBaja()` + `consultarNSS()` + `checkDni()` |
| Establishment | `establishment.service.ts` | CRUD con geocoding |
| Tramite | `tramite.service.ts` | `listarTramites()` + `descargarDocumento()` |
| OCR | `ocr.service.ts` | `uploadForScan()` (web + mobile vision) |
| Payroll | `payroll.service.ts` | CRUD de nominas |

## Convenciones del Proyecto

| Concepto | Convencion |
|----------|-----------|
| Import Axios | `import api from "../lib/api"` (instancia con baseURL) |
| Auth | `localStorage.getItem("accessToken")` → header `Authorization: Bearer` |
| Response | Backend: `{ success, data }` → Servicio retorna `response.data.data` |
| Tipos | Interfaces TypeScript que mapean al schema Prisma |
| Naming | camelCase para funciones, PascalCase para interfaces |
| Ubicacion | `src/services/{modulo}.service.ts` |
| IDs | `number` (Prisma usa Int autoincrement) |

## Checklist

- [ ] Interfaces del modelo y DTO definidas
- [ ] Funciones CRUD exportadas (get, getById, create, update, delete)
- [ ] Token de auth en cada request
- [ ] Tipos de retorno correctos (Promise<T>)
- [ ] FormData para uploads si aplica
- [ ] Funciones especificas del dominio (alta, baja, consultarNSS, etc.)
