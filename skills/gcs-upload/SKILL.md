---
name: gcs-upload
description: Gestiona subida y acceso a archivos en Google Cloud Storage con signed URLs. Usar para operaciones de almacenamiento en la nube (avatars, documentos, OCR, certificados).
origin: ocralis
---

# GCS Upload Skill

Gestiona subida y acceso a archivos en Google Cloud Storage.

## When to Activate

- Subir archivos (imagenes, PDFs, certificados) a GCS
- Generar signed URLs para acceso temporal
- Gestionar avatars de usuario
- Almacenar documentos generados (TA.2/S, contratos)
- Almacenar imagenes subidas para OCR
- Subir certificados digitales de empresas

## Patron Base (`services/storage.service.js`)

```javascript
import { Storage } from "@google-cloud/storage";
import config from "../config/config.js";
import logger from "../utils/logger.js";

const storage = new Storage({ projectId: config.GOOGLE_CLOUD_PROJECT_ID });
const bucket = storage.bucket(config.GCS_BUCKET_NAME);

export const uploadBufferToGCS = async (buffer, filename, contentType) => {
  const file = bucket.file(filename);

  await file.save(buffer, {
    metadata: { contentType },
    resumable: false, // false para archivos < 5MB
  });

  // Generar URL firmada (7 dias de validez)
  const [signedUrl] = await file.getSignedUrl({
    action: "read",
    expires: Date.now() + 7 * 24 * 60 * 60 * 1000,
  });

  return signedUrl;
};
```

## Casos de Uso

### Subir Avatar desde Multer

```javascript
// En el controller
const buffer = req.file.buffer;
const filename = `avatars/${userId}/${Date.now()}_${req.file.originalname}`;
const url = await uploadBufferToGCS(buffer, filename, req.file.mimetype);

// Guardar URL en usuario
await prisma.usuario.update({
  where: { id: userId },
  data: { avatarUrl: url },
});
```

### Subir PDF Generado

```javascript
const pdfBuffer = await rellenarFormularioPDF(datos);
const filename = `documentos/${employeeId}/TA2S_${dni}_${Date.now()}.pdf`;
const url = await uploadBufferToGCS(pdfBuffer, filename, "application/pdf");

// Guardar URL en tramite
await prisma.tramite.update({
  where: { id: tramiteId },
  data: { resolucion_pdf_url: url },
});
```

### Subir Imagen para OCR

```javascript
const filename = `ocr/${Date.now()}_${req.file.originalname}`;
const url = await uploadBufferToGCS(req.file.buffer, filename, req.file.mimetype);
// Pasar URL al servicio de OCR
```

### Subir Certificado Digital

```javascript
const filename = `certificados/${companyId}/${Date.now()}_cert.pfx`;
const url = await uploadBufferToGCS(req.file.buffer, filename, "application/x-pkcs12");
```

## Estructura de Carpetas en GCS

```
bucket/
├── avatars/{userId}/              # Fotos de perfil
├── documentos/{employeeId}/       # PDFs generados (TA.2/S, contratos)
├── ocr/{timestamp}/               # Imagenes subidas para OCR
└── certificados/{companyId}/      # Certificados digitales (temporal)
```

## Archivos Grandes (> 5MB)

```javascript
export const uploadLargeBufferToGCS = async (buffer, filename, contentType) => {
  const file = bucket.file(filename);

  await file.save(buffer, {
    metadata: { contentType },
    resumable: true, // true para archivos > 5MB
  });

  const [signedUrl] = await file.getSignedUrl({
    action: "read",
    expires: Date.now() + 7 * 24 * 60 * 60 * 1000,
  });

  return signedUrl;
};
```

## Convenciones

| Concepto | Convencion |
|----------|-----------|
| Signed URLs | 7 dias de validez por defecto |
| Naming | `{categoria}/{ownerId}/{timestamp}_{nombre_original}` |
| Content-Type | Siempre especificar el mimetype correcto |
| Resumable | `false` para < 5MB, `true` para >= 5MB |
| Cleanup | Implementar TTL o lifecycle rules en GCS para temporales |
| Config | `GCS_BUCKET_NAME` y `GOOGLE_CLOUD_PROJECT_ID` en `.env` |
| Errores | Loguear con `logger.error` y devolver error generico |

## Checklist

- [ ] Buffer y filename correctos
- [ ] Content-Type especificado
- [ ] Resumable apropiado segun tamano
- [ ] Signed URL generada
- [ ] URL guardada en base de datos (usuario, tramite, etc.)
- [ ] Logging de errores
- [ ] Estructura de carpetas correcta en GCS
