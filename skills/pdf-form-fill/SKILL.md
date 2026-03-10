---
name: pdf-form-fill
description: Rellena formularios PDF oficiales (TA.2/S, Modelo 145, Carta de Baja) usando pdf-lib. Usar para completar la generacion de documentos oficiales espanoles.
origin: ocralis
---

# PDF Form Fill Skill

Rellena formularios PDF oficiales (TA.2/S, Modelo 145) usando pdf-lib.

## When to Activate

- Generar formulario TA.2/S para alta/baja de trabajador
- Rellenar Modelo 145 IRPF
- Generar carta de baja voluntaria
- Cualquier operacion de generacion de documentos PDF oficiales

## Patron Base con pdf-lib

```javascript
import { PDFDocument } from "pdf-lib";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export const rellenarFormularioPDF = async (datos) => {
  // 1. Cargar plantilla PDF
  const templatePath = path.join(__dirname, "../resources/Modelo_TA2S.pdf");
  const templateBytes = fs.readFileSync(templatePath);
  const pdfDoc = await PDFDocument.load(templateBytes);

  // 2. Obtener formulario interactivo
  const form = pdfDoc.getForm();

  // 3. Listar campos disponibles (debug)
  const fields = form.getFields();
  fields.forEach(field => {
    console.log(`Campo: ${field.getName()} - Tipo: ${field.constructor.name}`);
  });

  // 4. Rellenar campos de texto
  form.getTextField("nombre").setText(datos.nombre);
  form.getTextField("apellido1").setText(datos.primer_apellido);
  form.getTextField("apellido2").setText(datos.segundo_apellido);
  form.getTextField("dni").setText(datos.dni);
  form.getTextField("nss").setText(datos.nss);
  form.getTextField("fecha_nacimiento").setText(datos.fecha_nacimiento);
  // ... mas campos segun el formulario

  // 5. Marcar checkboxes
  if (datos.tipo === "ALTA") {
    form.getCheckBox("tipo_alta").check();
  } else {
    form.getCheckBox("tipo_baja").check();
  }

  // 6. Aplanar formulario (no editable)
  form.flatten();

  // 7. Guardar y devolver Buffer
  const pdfBytes = await pdfDoc.save();
  return Buffer.from(pdfBytes);
};
```

## Plantillas Disponibles en `resources/`

| Archivo | Descripcion | Uso |
|---------|-------------|-----|
| `Modelo_TA2S.pdf` | Formulario TA.2/S | Alta/baja trabajador Seguridad Social |
| `Modelo_145.pdf` | Modelo 145 IRPF | Retencion IRPF del trabajador |
| `Carta_Baja_Voluntaria_sin_Preaviso.pdf` | Carta de baja voluntaria | Baja voluntaria sin preaviso |

## Integracion con Controller

```javascript
// pdf.controller.js
import { rellenarFormularioPDF } from "../services/pdf.service.js";
import { prisma } from "../prismaClient.js";
import logger from "../utils/logger.js";

export const generarTA2S = async (req, res) => {
  try {
    const { employeeId } = req.body;

    // 1. Obtener datos del empleado + empresa + establecimiento
    const employee = await prisma.employee.findUnique({
      where: { id: parseInt(employeeId) },
      include: {
        establishment: {
          include: { company: true },
        },
      },
    });

    if (!employee) {
      return res.status(404).json({ success: false, error: "Empleado no encontrado" });
    }

    // 2. Mapear datos al formulario
    const pdfBuffer = await rellenarFormularioPDF({
      nombre: employee.nombre,
      primer_apellido: employee.primer_apellido,
      segundo_apellido: employee.segundo_apellido,
      dni: employee.numero_documento,
      nss: employee.nss,
      fecha_nacimiento: employee.fecha_nacimiento,
      tipo: "ALTA",
      // empresa
      nombre_empresa: employee.establishment.company.nombre,
      cif: employee.establishment.company.cif,
      ccc: employee.establishment.company.ccc,
    });

    // 3. Enviar como descarga
    const fecha = new Date().toISOString().split("T")[0];
    res.setHeader("Content-Type", "application/pdf");
    res.setHeader("Content-Disposition",
      `attachment; filename=TA2S_${employee.numero_documento}_${fecha}.pdf`);
    res.send(pdfBuffer);
  } catch (error) {
    logger.error(error, "Error generando PDF TA.2/S");
    res.status(500).json({ success: false, error: "Error al generar PDF" });
  }
};
```

## Subir PDF Generado a GCS (Opcional)

```javascript
import { uploadBufferToGCS } from "../services/storage.service.js";

// Despues de generar el PDF buffer:
const fecha = new Date().toISOString().split("T")[0];
const filename = `documentos/${employeeId}/TA2S_${dni}_${fecha}.pdf`;
const signedUrl = await uploadBufferToGCS(pdfBuffer, filename, "application/pdf");

// Guardar URL en el tramite
await prisma.tramite.update({
  where: { id: tramiteId },
  data: { resolucion_pdf_url: signedUrl },
});
```

## Convenciones

| Concepto | Convencion |
|----------|-----------|
| Plantillas | En `resources/`, nunca modificar los originales |
| Buffer | Devolver `Buffer.from(pdfBytes)` para enviar o subir |
| Flatten | Aplanar formulario despues de rellenar (documento final no editable) |
| Naming | `TA2S_{dni}_{fecha}.pdf` para archivos generados |
| Storage | Opcionalmente subir a GCS y guardar URL en `Tramite.resolucion_pdf_url` |
| Debug | Listar campos con `form.getFields()` para mapear nombres correctos |

## Checklist

- [ ] Plantilla PDF cargada desde `resources/`
- [ ] Campos listados y mapeados correctamente
- [ ] Campos de texto rellenados con `setText()`
- [ ] Checkboxes marcados con `check()`
- [ ] Formulario aplanado con `form.flatten()`
- [ ] Buffer devuelto para response o upload
- [ ] Headers Content-Type y Content-Disposition configurados
- [ ] Opcionalmente subido a GCS con URL en Tramite
