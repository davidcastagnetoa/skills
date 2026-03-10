/**
 * Client-side image quality checks before sending to backend.
 * These are lightweight heuristics — full analysis happens server-side.
 */

export interface ImageQualityResult {
  acceptable: boolean;
  issues: string[];
}

/**
 * Estimate base64 image size in bytes.
 */
export function estimateBase64Size(base64: string): number {
  return Math.ceil((base64.length * 3) / 4);
}

const MIN_IMAGE_SIZE = 50_000; // ~50KB minimum for usable photo
const MAX_IMAGE_SIZE = 10_000_000; // 10MB max

/**
 * Basic quality gate: checks image size as a proxy for resolution/quality.
 * Real blur/brightness detection requires native processing or backend.
 */
export function checkImageQuality(base64: string): ImageQualityResult {
  const issues: string[] = [];
  const size = estimateBase64Size(base64);

  if (size < MIN_IMAGE_SIZE) {
    issues.push("La imagen es demasiado pequena. Acerca la camara.");
  }
  if (size > MAX_IMAGE_SIZE) {
    issues.push("La imagen es demasiado grande.");
  }

  return { acceptable: issues.length === 0, issues };
}

/**
 * Validate that we have enough frames for liveness analysis.
 */
export function validateFrameSequence(frames: string[]): ImageQualityResult {
  const issues: string[] = [];

  if (frames.length < 10) {
    issues.push("No se capturaron suficientes frames. Intenta de nuevo.");
  }

  const validFrames = frames.filter(
    (f) => estimateBase64Size(f) >= MIN_IMAGE_SIZE
  );
  if (validFrames.length < frames.length * 0.7) {
    issues.push("Demasiados frames de baja calidad. Mejora la iluminacion.");
  }

  return { acceptable: issues.length === 0, issues };
}
