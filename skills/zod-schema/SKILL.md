---
name: zod-schema
description: Crea schemas de validacion Zod para backend (inline en controllers) y frontend (archivos separados con React Hook Form). Incluye patrones de validacion para documentos espanoles (DNI, NIE, CIF, NSS).
origin: ocralis
---

# Zod Schema Skill

Crea schemas de validacion Zod para backend y frontend.

## When to Activate

- Validar input de un endpoint backend
- Crear schema de validacion para un formulario frontend
- Validar documentos espanoles (DNI, NIE, CIF, CCC, NSS)
- Agregar validaciones cruzadas entre campos
- Conectar validacion Zod con React Hook Form

## Backend — Schema Inline en Controller

```javascript
import { z } from "zod";

const createEmployeeSchema = z.object({
  nombre: z.string().min(1, "Nombre requerido"),
  primer_apellido: z.string().min(1, "Primer apellido requerido"),
  segundo_apellido: z.string().optional(),
  email: z.string().email("Email invalido"),
  telefono: z.string().regex(/^[0-9]{9}$/, "Telefono debe tener 9 digitos").optional(),
  tipo_documento: z.enum(["DNI", "NIE", "Pasaporte", "Tarjeta de residencia"]),
  numero_documento: z.string().min(1, "Documento requerido"),
  fecha_nacimiento: z.string().refine(val => !isNaN(Date.parse(val)), "Fecha invalida"),
  sexo: z.enum(["H", "M"]),
  companyId: z.number().int().positive().or(z.string().transform(Number)),
});

// Uso en controller:
export const createEmployee = async (req, res) => {
  try {
    const validated = createEmployeeSchema.parse(req.body);
    // ... logica
  } catch (error) {
    if (error instanceof z.ZodError) {
      return res.status(400).json({
        success: false,
        error: "Datos invalidos",
        details: error.errors,
      });
    }
    // ...
  }
};
```

## Frontend — Schema en Archivo Separado

### Schema (`src/schemas/{modulo}Schema.ts`)

```typescript
import { z } from "zod";

export const employeeSchema = z.object({
  nombre: z.string().min(2, "Minimo 2 caracteres"),
  primer_apellido: z.string().min(2, "Minimo 2 caracteres"),
  segundo_apellido: z.string().optional(),
  tipo_documento: z.enum(["DNI", "NIE", "Pasaporte", "Tarjeta de residencia"]),
  numero_documento: z.string().min(1, "Documento requerido"),
  email: z.string().email("Email invalido"),
  telefono: z.string().regex(/^[0-9]{9}$/, "9 digitos").optional().or(z.literal("")),
  fecha_nacimiento: z.string()
    .refine(val => /^\d{2}\/\d{2}\/\d{4}$/.test(val), "Formato DD/MM/YYYY"),
}).superRefine((data, ctx) => {
  // Validaciones cruzadas por tipo de documento
  if (data.tipo_documento === "DNI" && !/^[0-9]{8}[A-Z]$/.test(data.numero_documento)) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: "DNI invalido (8 digitos + letra)",
      path: ["numero_documento"],
    });
  }
  if (data.tipo_documento === "NIE" && !/^[XYZ][0-9]{7}[A-Z]$/.test(data.numero_documento)) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: "NIE invalido (X/Y/Z + 7 digitos + letra)",
      path: ["numero_documento"],
    });
  }
});

// Tipo inferido para TypeScript
export type EmployeeFormData = z.infer<typeof employeeSchema>;
```

### Integracion con React Hook Form

```tsx
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { employeeSchema, type EmployeeFormData } from "../../schemas/employeeSchema";

const { register, handleSubmit, formState: { errors } } = useForm<EmployeeFormData>({
  resolver: zodResolver(employeeSchema),
});
```

## Patrones de Validacion para Documentos Espanoles

| Campo | Regex | Descripcion |
|-------|-------|-------------|
| DNI | `/^[0-9]{8}[A-Z]$/` | 8 digitos + 1 letra mayuscula |
| NIE | `/^[XYZ][0-9]{7}[A-Z]$/` | X/Y/Z + 7 digitos + 1 letra |
| CIF | `/^[A-Z][0-9]{7}[A-Z0-9]$/` | Letra + 7 digitos + letra/digito |
| CCC | `/^[0-9]{11}$/` | 11 digitos (Codigo Cuenta Cotizacion) |
| NSS | `/^[0-9]{12}$/` | 12 digitos (Numero Seguridad Social) |
| Telefono | `/^[0-9]{9}$/` | 9 digitos |
| Cod. Postal | `/^[0-9]{5}$/` | 5 digitos |
| Fecha | DD/MM/YYYY o ISO 8601 | Formato espanol o estandar |

## Validaciones Avanzadas

### Letra de Control DNI

```typescript
const validarLetraDNI = (dni: string): boolean => {
  const letras = "TRWAGMYFPDXBNJZSQVHLCKE";
  const numero = parseInt(dni.slice(0, 8));
  const letra = dni.charAt(8);
  return letras[numero % 23] === letra;
};

// En schema:
numero_documento: z.string()
  .regex(/^[0-9]{8}[A-Z]$/, "Formato DNI invalido")
  .refine(validarLetraDNI, "Letra de control DNI incorrecta"),
```

### Campo Opcional que Puede ser String Vacio

```typescript
// Permitir string vacio o valor valido
telefono: z.string()
  .regex(/^[0-9]{9}$/, "9 digitos")
  .optional()
  .or(z.literal("")),
```

### Transformar String a Number

```typescript
// Aceptar string o number, siempre devolver number
companyId: z.number().int().positive()
  .or(z.string().transform(Number)),
```

## Convenciones

| Concepto | Convencion |
|----------|-----------|
| Backend | Schemas inline en el controller |
| Frontend | Archivos separados en `src/schemas/{modulo}Schema.ts` |
| Errores | Mensajes en espanol |
| Opcionales | `.optional()` o `.nullable()` |
| Transformaciones | `.transform()` para coercion de tipos |
| Validacion cruzada | `.superRefine()` para validaciones entre campos |
| Tipos | `z.infer<typeof schema>` para TypeScript |

## Checklist

- [ ] Schema definido con todos los campos requeridos
- [ ] Mensajes de error en espanol
- [ ] Validaciones regex para documentos espanoles
- [ ] Validaciones cruzadas con `.superRefine()` si aplica
- [ ] Tipo inferido exportado (`type FormData = z.infer<typeof schema>`)
- [ ] Integrado con React Hook Form via `zodResolver` (frontend)
- [ ] Manejo de `z.ZodError` en catch (backend)
