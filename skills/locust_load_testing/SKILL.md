---
name: locust_load_testing
description: Pruebas de carga y rendimiento para validar el SLO de 8 segundos antes de cada release
---

# locust_load_testing

Locust simula múltiples usuarios concurrentes enviando solicitudes de verificación KYC. Las pruebas de carga validan que el sistema cumple el SLO de 8 segundos p95 bajo carga sostenida y descubren cuellos de botella antes de producción.

## When to use

Ejecutar en staging antes de cada release que afecte al pipeline KYC o a la infraestructura. También ejecutar pruebas de capacidad para determinar el número óptimo de workers GPU.

## Instructions

1. Instalar: `pip install locust`
2. Crear `load_tests/locustfile.py`:
   ```python
   from locust import HttpUser, task, between
   import base64, os
   SAMPLE_SELFIE = base64.b64encode(open("tests/fixtures/sample_selfie.jpg", "rb").read()).decode()
   SAMPLE_DOC = base64.b64encode(open("tests/fixtures/sample_passport.jpg", "rb").read()).decode()
   class KYCUser(HttpUser):
       wait_time = between(1, 3)
       @task
       def verify_identity(self):
           response = self.client.post("/v1/verify", json={
               "selfie_b64": SAMPLE_SELFIE,
               "document_b64": SAMPLE_DOC,
               "document_type": "passport",
           }, headers={"Authorization": f"Bearer {os.environ['TEST_JWT']}"})
           assert response.elapsed.total_seconds() < 8, f"SLO violated: {response.elapsed.total_seconds()}s"
   ```
3. Ejecutar: `locust -f load_tests/locustfile.py --host=https://staging.kyc.company.com --users=50 --spawn-rate=5 --run-time=5m --headless`
4. Targets de SLO a validar: p50 < 4s, p95 < 8s, p99 < 15s, error_rate < 0.1%.
5. Guardar el HTML report: `--html=load-test-report.html` y adjuntarlo al release.
6. Si p95 > 8s: escalar workers GPU, optimizar batching o revisar los agentes con mayor latencia (ver Jaeger traces).

## Notes

- Las pruebas de carga deben ejecutarse con imágenes representativas de producción (resolución, formato, calidad).
- Simular también el escenario de liveness activo (challenge-response) que tiene mayor latencia que el pasivo.
- Un test de 50 usuarios concurrentes durante 5 minutos es un buen punto de partida — ajustar según el volumen esperado en producción.