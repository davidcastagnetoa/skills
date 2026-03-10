---
name: saltra-integration
description: Integra nuevas operaciones con la API SALTRA v4 (Seguridad Social espanola) para alta, baja, consulta NSS y gestion de certificados digitales. Usar para cualquier interaccion con la Seguridad Social.
origin: ocralis
---

# SALTRA Integration Skill

Integra nuevas operaciones con la API SALTRA v4 (Seguridad Social espanola).

## When to Activate

- Registrar alta de un trabajador en la Seguridad Social
- Registrar baja de un trabajador
- Consultar NSS (Numero de la Seguridad Social) por DNI
- Subir certificado digital de empresa
- Cualquier nueva operacion con SALTRA

## Patron de Integracion

### Token Caching (Reutilizar mientras sea valido)

```javascript
import axios from "axios";
import config from "../config/config.js";
import logger from "../utils/logger.js";

let saltraToken = null;
let tokenExpiry = 0;

const getSaltraToken = async () => {
  if (saltraToken && Date.now() < tokenExpiry) return saltraToken;

  const response = await axios.post(`${config.SALTRA_API_URL}/auth/login`, {
    email: config.SALTRA_EMAIL,
    password: config.SALTRA_PASSWORD,
  });

  saltraToken = response.data.access_token;
  tokenExpiry = Date.now() + (response.data.expires_in - 300) * 1000; // 5min safety margin
  return saltraToken;
};
```

### Operacion Generica

```javascript
export const nuevaOperacionSaltra = async (datos, certSecret) => {
  const token = await getSaltraToken();

  const response = await axios.post(
    `${config.SALTRA_API_URL}/seg-social/operacion`,
    {
      ...datos,
      test: config.NODE_ENV !== "production" ? 1 : 0,
    },
    {
      headers: {
        Authorization: `Bearer ${token}`,
        "X-Cert-Secret": certSecret,
        "Content-Type": "application/json",
      },
    }
  );

  logger.debug({ request: datos, response: response.data }, "SALTRA operacion");
  return response.data;
};
```

## Endpoints SALTRA v4

| Metodo | Ruta | Descripcion | Estado |
|--------|------|-------------|--------|
| POST | `/auth/login` | Obtener token de acceso | Implementado |
| POST | `/seg-social/alta` | Registrar alta de trabajador | Implementado |
| POST | `/seg-social/baja` | Registrar baja de trabajador | Implementado |
| GET | `/seg-social/nss-by-ipf` | Consultar NSS por DNI + apellidos | Implementado |
| POST | `/certificate` | Subir certificado digital p12/pfx | Implementado |

## Datos Requeridos para Alta

```javascript
{
  naf: "123456789012",           // NSS (12 digitos)
  ipf: "12345678A",             // DNI/NIE
  nombre: "Juan",
  apellido1: "Garcia",
  apellido2: "Lopez",
  fecha_nacimiento: "1990-01-15",
  sexo: "H",                    // H = Hombre, M = Mujer
  regimen: "0111",              // Regimen general
  ccc: "28123456789",           // CCC empresa (11 digitos)
  grupo_cotizacion: "07",
  fecha_alta: "2024-01-15",
  cno: "5120",                  // Codigo Nacional de Ocupacion
  tipo_contrato: "100",
  coeficiente_jornada: "1000",  // 1000 = jornada completa
  cert_secret: "xxx",           // Del certificado digital de la empresa
  test: 1                       // 1 = modo prueba, 0 = produccion
}
```

## Datos Requeridos para Baja

```javascript
{
  naf: "123456789012",           // NSS
  ipf: "12345678A",             // DNI/NIE
  fecha_baja: "2024-06-30",
  causa_baja: "51",             // Codigo causa (51 = baja voluntaria)
  ccc: "28123456789",
  cert_secret: "xxx",
  test: 1
}
```

## Manejo de Errores SALTRA

```javascript
try {
  const result = await darAlta(datos, certSecret);
  return result;
} catch (error) {
  if (error.response?.data?.message) {
    // Error legible de SALTRA
    logger.error({ saltraError: error.response.data }, "Error SALTRA");
    throw new Error(`Error SALTRA: ${error.response.data.message}`);
  }
  throw error;
}
```

## Convenciones

| Concepto | Convencion |
|----------|-----------|
| Token cache | Siempre reutilizar con margen de 5 minutos antes de expiracion |
| Modo test | Forzar `test=1` en entornos que NO sean produccion |
| cert_secret | Se obtiene de `Company.saltra_cert_secret`, se almacena al subir certificado |
| Errores | Parsear `response.data.message` para errores legibles al usuario |
| Logging | Loguear request y response completos en nivel `debug` |
| Config | Variables en `config.js`: `SALTRA_API_URL`, `SALTRA_EMAIL`, `SALTRA_PASSWORD` |

## Checklist

- [ ] Token cacheado y reutilizado
- [ ] Modo test activo en no-produccion (`test: 1`)
- [ ] cert_secret obtenido de la Company asociada
- [ ] Errores parseados y logueados
- [ ] Datos validados con Zod antes de enviar a SALTRA
- [ ] Tramite creado/actualizado con el resultado
