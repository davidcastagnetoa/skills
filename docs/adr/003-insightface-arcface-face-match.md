# ADR-003: InsightFace (ArcFace) como modelo de reconocimiento facial

- **Estado**: accepted
- **Fecha**: 2026-03-03
- **Autores**: software-architecture-agent

## Contexto

El modulo de face match necesita comparar el rostro de la selfie en vivo con la foto del documento de identidad. Esto requiere un modelo que genere embeddings faciales de alta calidad, capaz de tolerar diferencias de iluminacion, angulo, resolucion y envejecimiento entre la foto del documento y la selfie. El sistema debe alcanzar FAR < 0.1% y FRR < 5%.

## Opciones Evaluadas

### Opcion A: InsightFace (ArcFace R100)
- Pros: estado del arte en precision (99.83% en LFW), loss function ArcFace con margen angular aditivo, embeddings de 512 dimensiones muy discriminativos, modelos pre-entrenados disponibles en ONNX, soporte activo, deteccion + alineacion + reconocimiento integrados.
- Contras: modelo R100 es grande (~250MB), requiere GPU para inferencia rapida, API Python menos documentada que alternativas.

### Opcion B: DeepFace (wrapper)
- Pros: wrapper que integra multiples backends (VGG-Face, FaceNet, ArcFace, etc.), API simple, permite comparar modelos facilmente.
- Contras: es un wrapper, no un modelo — agrega overhead, menor control sobre la inferencia, dependencia de multiples sub-librerias.

### Opcion C: FaceNet (Google)
- Pros: bien documentado, embeddings de 128 dimensiones (mas ligero), amplia adopcion.
- Contras: precision inferior a ArcFace en benchmarks recientes, no se mantiene activamente, modelos pre-entrenados de calidad variable.

### Opcion D: dlib
- Pros: facil de usar, no requiere GPU, incluye deteccion + landmarks + reconocimiento.
- Contras: precision significativamente menor que ArcFace (99.38% vs 99.83% en LFW), no es estado del arte, mas lento en batches grandes.

## Decision

**InsightFace con modelo ArcFace R100** como modelo principal de reconocimiento facial. **FaceNet como fallback** si InsightFace no esta disponible.

ArcFace es el estado del arte en reconocimiento facial con la mayor precision demostrada en benchmarks publicos. La diferencia de precision entre ArcFace y las alternativas es critica cuando el objetivo es FAR < 0.1%: cada decima de porcentaje reduce drasticamente los falsos positivos.

El pipeline de face match sera:
1. RetinaFace (deteccion) → 2. Alineacion por 5 landmarks → 3. ArcFace R100 (embedding 512-d) → 4. Similitud coseno.

## Consecuencias

- El modelo R100 requiere GPU para inferencia en < 500ms; sin GPU, se usara el modelo R50 (mas ligero, ligeramente menos preciso).
- Los modelos se exportan a ONNX para servir via Triton Inference Server o ONNX Runtime.
- Se necesita super-resolucion (ESRGAN) para fotos de documentos de baja calidad antes de generar el embedding.
- Los embeddings son vectores de 512 floats (~2KB) que se almacenan temporalmente en Redis (TTL 15 min) y nunca de forma permanente (GDPR).
- Si se requiere soporte offline o en dispositivo, se evaluara un modelo mas ligero (MobileFaceNet).
