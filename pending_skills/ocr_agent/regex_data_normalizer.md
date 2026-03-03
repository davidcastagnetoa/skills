---
name: regex_data_normalizer
description: Normalizar fechas, nombres y números de documento a formato estándar
type: Algorithm
priority: Esencial
mode: Self-hosted
---

# regex_data_normalizer

Módulo de normalización que transforma los datos crudos extraídos por OCR a formatos estándar consistentes. Normaliza fechas (ISO 8601), nombres (capitalización), y números de documento (sin espacios/guiones) para su validación posterior.

## When to use

Usar en el `ocr_agent` inmediatamente después de la extracción OCR y antes de la validación cruzada con MRZ. Todos los campos extraídos deben pasar por normalización.

## Instructions

1. Fechas: detectar formato con regex y convertir a ISO 8601 (`YYYY-MM-DD`).
   - Patrones: `DD/MM/YYYY`, `DD-MM-YYYY`, `DD.MM.YYYY`, `YYYYMMDD` (MRZ).
2. Nombres: eliminar caracteres no alfabéticos, normalizar acentos, capitalizar.
   - `re.sub(r'[^A-Za-záéíóúñÁÉÍÓÚÑ\s]', '', name).strip().title()`.
3. Número de documento: eliminar espacios, guiones y puntos.
   - `re.sub(r'[\s\-\.]', '', doc_number).upper()`.
4. Nacionalidad: mapear a código ISO 3166-1 alpha-3.
5. Sexo: normalizar a `M`/`F` independientemente del idioma del documento.
6. Validar que la fecha de nacimiento sea anterior a hoy y posterior a 1900.
7. Validar que la fecha de expiración no esté en el pasado.

## Notes

- Los documentos españoles usan formato `DD MM YYYY` con espacios; contemplar este patrón.
- La normalización debe ser idempotente: aplicar dos veces produce el mismo resultado.
- Registrar las transformaciones aplicadas en el log de auditoría para trazabilidad.
