---
name: prisma-migration
description: Gestiona cambios en schema.prisma y genera/aplica migraciones de forma segura. Usar cuando se modifica el modelo de datos (nuevos campos, relaciones, indices, enums).
origin: ocralis
---

# Prisma Migration Skill

Gestiona cambios en el schema de Prisma y migraciones de forma segura.

## When to Activate

- Agregar un nuevo modelo al schema
- Agregar o modificar campos en un modelo existente
- Crear o modificar relaciones entre modelos
- Agregar nuevos enums
- Crear indices para optimizar queries
- Cambiar tipos de datos de campos existentes

## Pasos

### 1. Modificar el Schema (`prisma/schema.prisma`)

```prisma
model NuevoModelo {
  id        Int      @id @default(autoincrement())
  campo     String
  campoOpt  String?
  estado    EstadoAlta @default(PENDIENTE)

  // Relacion N:1
  usuario   Usuario  @relation(fields: [usuarioId], references: [id])
  usuarioId Int

  // Relacion N:M (implicita)
  companies Company[]

  // Timestamps
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  // Indices
  @@index([usuarioId])
  @@index([estado])
}
```

### 2. Generar y Aplicar Migracion

```bash
# Desarrollo: crea migracion con nombre descriptivo
cd ocralis_backend
npx prisma migrate dev --name add_nuevo_modelo

# Staging/Produccion: aplica migraciones pendientes (sin generar)
npx prisma migrate deploy

# Solo desarrollo (sin historial de migracion):
npx prisma db push
```

### 3. Regenerar el Cliente Prisma

```bash
npx prisma generate
```

### 4. Verificar con Prisma Studio

```bash
npx prisma studio
```

## Modelos Existentes

| Modelo | Descripcion |
|--------|-------------|
| Usuario | Cuentas de usuario con tier, roles, OAuth, ubicacion, billing |
| Company | Entidad empresarial (CIF, CCC, direccion fiscal, cert SALTRA) |
| Establishment | Ubicaciones fisicas con geolocalizacion |
| Employee | Perfiles de trabajadores (documento, NSS, contrato, geolocalizacion) |
| EmployeeCompanies | Join table implicita Employee ↔ Company (N:M) |
| Tramite | Procedimientos (alta/baja) con estado y PDF resolucion |

## Enums Existentes

```prisma
enum Provider      { EMAIL GOOGLE GITHUB SSO CUSTOM }
enum Role          { USER SUPERUSER ADMIN SUPPORT GUEST }
enum SubscriptionTier { FREE BASIC PRO ENTERPRISE CUSTOM }
enum TipoTramite   { ALTA BAJA SUSPENDIDO INACTIVO }
enum EstadoAlta    { PENDIENTE EN_PROCESO COMPLETADO ERROR }
enum BillingCycle  { MONTHLY ANNUAL }
enum Status        { INACTIVE PENDING ACTIVE CANCELED EXPIRED }
```

## Convenciones del Proyecto

| Concepto | Convencion |
|----------|-----------|
| IDs | `Int @id @default(autoincrement())` |
| Timestamps | `createdAt DateTime @default(now())` + `updatedAt DateTime @updatedAt` |
| Foreign Keys | `{modelo}Id` (ej: `usuarioId`, `companyId`, `establishmentId`) |
| Enums | `enum NombreEnum { VALOR1 VALOR2 }` en PascalCase |
| Provider | `postgresql` con Supabase |
| Modelos | PascalCase singular (`Employee`, no `Employees`) |
| Campos | camelCase (`firstName`, no `first_name`) |
| Campos opcionales | `String?` con `?` |
| Valores default | `@default(value)` o `@default(now())` |
| Migraciones | Nombre descriptivo en snake_case: `add_campo_to_modelo` |

## Precauciones

- **Nunca** eliminar campos en produccion sin migracion de datos previa
- **Nunca** cambiar tipos de campos con datos existentes sin `@map` o migracion manual
- Usar `npx prisma migrate dev` solo en desarrollo local
- Usar `npx prisma migrate deploy` en staging/produccion
- Hacer backup de la base de datos antes de migraciones destructivas
- Probar migraciones en staging antes de produccion

## Checklist

- [ ] Schema modificado correctamente con convenciones
- [ ] Migracion generada con nombre descriptivo (`--name`)
- [ ] Cliente Prisma regenerado (`npx prisma generate`)
- [ ] Servidor reiniciado para cargar cambios
- [ ] Verificado con Prisma Studio
- [ ] Actualizar CLAUDE.md si cambia el modelo de datos
- [ ] Actualizar README.md del backend
