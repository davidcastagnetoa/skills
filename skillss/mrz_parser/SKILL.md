---
name: mrz_parser
description: Parsear y validar la Machine Readable Zone (MRZ) de pasaportes y DNIs según estándar ICAO 9303
---

# mrz_parser

Parsea y valida la MRZ (Machine Readable Zone) de documentos de viaje según el estándar ICAO Doc 9303. Extrae campos estructurados y valida checksums matemáticos para verificar integridad.

## When to use

Usar sobre la región MRZ detectada por YOLOv8 en pasaportes (TD3) y DNIs (TD1/TD2).

## Instructions

1. Instalar la librería `mrz`: `pip install mrz`.
2. Pasar las líneas de texto de la MRZ al parser: `from mrz.checker.td1 import TD1CodeChecker; td1 = TD1CodeChecker(mrz_line1 + mrz_line2 + mrz_line3)`.
3. Verificar validez: `is_valid = bool(td1)`.
4. Extraer campos: `td1.country`, `td1.name`, `td1.document_number`, `td1.birth_date`, `td1.expiry_date`, `td1.sex`.
5. Verificar todos los checksums individualmente: `td1.check_digit_document_number`, etc.
6. Si algún checksum falla: incrementar flag de documento alterado.
7. Comparar campos MRZ con campos OCR de la zona visual del documento (cross-check).

## Notes

- Repositorio `mrz`: https://github.com/joaomlourenco/mrz
- Alternativa: `passporteye` — `pip install passporteye`.
- Un checksum MRZ fallido no siempre es fraude (puede ser error OCR); analizar en contexto con score global.