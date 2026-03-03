---
name: pii_anonymizer_presidio
description: Detectar y enmascarar automáticamente datos personales en logs para cumplimiento GDPR
type: Library
priority: Esencial
mode: Self-hosted
---

# pii_anonymizer_presidio

Microsoft Presidio analiza texto en busca de PII (nombres, DNIs, fechas de nacimiento, IBANs, emails) y los reemplaza por tokens antes de que lleguen a los logs o a cualquier sistema de almacenamiento secundario.

## When to use

Usar como middleware de logging y antes de cualquier export de datos a sistemas externos (Loki, Jaeger, Grafana). Aplicar también sobre los campos textuales extraídos por OCR antes de persistirlos en auditoría.

## Instructions

1. Instalar: `pip install presidio-analyzer presidio-anonymizer`
2. Descargar modelo spaCy: `python -m spacy download es_core_news_lg` (español) y `en_core_web_lg` (inglés).
3. Inicializar en `backend/core/privacy.py`:
   ```python
   from presidio_analyzer import AnalyzerEngine
   from presidio_anonymizer import AnonymizerEngine
   analyzer = AnalyzerEngine()
   anonymizer = AnonymizerEngine()
   ```
4. Función de enmascarado:
   ```python
   def anonymize_text(text: str, language: str = "es") -> str:
       results = analyzer.analyze(text=text, language=language)
       return anonymizer.anonymize(text=text, analyzer_results=results).text
   ```
5. Añadir processor personalizado en structlog que aplique `anonymize_text()` al campo `message` de cada log entry.
6. Configurar entidades a detectar: `PERSON`, `ID_NUMBER`, `DATE_TIME`, `IBAN_CODE`, `EMAIL_ADDRESS`, `PHONE_NUMBER`.
7. Para campos de OCR (nombre, DOB, número de documento), aplicar antes de INSERT en PostgreSQL.

## Notes

- Presidio opera completamente offline — no envía datos a ningún servicio externo.
- El modelo spaCy es el más preciso para español; para rendimiento en producción usar `es_core_news_sm`.
- Los campos MRZ y embeddings NO deben llegar nunca a los logs — filtrarlos antes de la capa de anonimización.