---
name: yolov8_documents
description: Clasificar tipo de documento y localizar regiones (foto, MRZ, campos de texto) con YOLOv8 fine-tuned
---

# yolov8_documents

YOLOv8 fine-tuned en documentos de identidad detecta y clasifica el tipo de documento (DNI, pasaporte, permiso de conducir) y localiza las regiones de interés (foto, MRZ, número de documento).

## When to use

Usar como paso de clasificación y segmentación del documento, antes de OCR y face extraction.

## Instructions

1. Instalar: `pip install ultralytics`.
2. Partir de YOLOv8n o YOLOv8s (nano/small) para balance velocidad/precisión.
3. Fine-tuning con dataset de documentos de identidad (MIDV-500, MIDV-2020).
4. Clases a detectar: `['DNI_ES', 'PASSPORT', 'DRIVING_LICENSE', 'region_photo', 'region_mrz', 'region_name', 'region_dob', 'region_docnum']`.
5. Entrenar: `yolo train data=documents.yaml model=yolov8s.pt epochs=100 imgsz=640`.
6. Exportar a ONNX: `yolo export model=best.pt format=onnx`.
7. Cargar en Triton y servir via gRPC.
8. Post-procesar: extraer crops de cada región detectada para procesamiento específico.

## Notes

- Dataset MIDV-500: https://arxiv.org/abs/1807.05786 (500 tipos de documentos de 75 países).
- Si el tipo de documento no se reconoce con confianza > 0.7, rechazar o pedir nueva captura.