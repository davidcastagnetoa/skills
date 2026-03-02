---
name: pytest_asyncio
description: Framework de testing con soporte completo para código async, fixtures y parametrización
---

# pytest_asyncio

pytest es el framework de testing principal del sistema KYC. `pytest-asyncio` añade soporte para tests de funciones `async def`, indispensable dado que todos los agentes son async. `pytest-cov` mide la cobertura de tests.

## When to use

Usar para todos los tests: unitarios, de integración y de regresión. Ningún código nuevo debe llegar a main sin tests que cubran el happy path y los edge cases críticos.

## Instructions

1. Instalar: `pip install pytest pytest-asyncio pytest-cov httpx`
2. Configurar en `pyproject.toml`:
   ```toml
   [tool.pytest.ini_options]
   asyncio_mode = "auto"
   testpaths = ["backend/tests"]
   addopts = "--cov=backend --cov-report=xml --cov-fail-under=80"
   ```
3. Estructura de tests:
   ```
   backend/tests/
   ├── unit/
   │   ├── test_liveness_agent.py
   │   ├── test_ocr_agent.py
   │   └── test_face_match_agent.py
   ├── integration/
   │   ├── test_pipeline_e2e.py
   │   └── test_api_endpoints.py
   └── conftest.py
   ```
4. Test async example:
   ```python
   import pytest
   from httpx import AsyncClient
   from backend.main import app
   @pytest.mark.asyncio
   async def test_verify_endpoint_returns_200():
       async with AsyncClient(app=app, base_url="http://test") as client:
           response = await client.post("/v1/verify", json={"session_id": "test-123"})
       assert response.status_code == 200
   ```
5. Fixtures en `conftest.py`: mock de modelos ML (devolver scores fijos), conexión a Redis de test, factory de sesiones.
6. Tests críticos obligatorios: threshold de liveness, threshold de face match, rechazo de documento expirado, rate limiting.

## Notes

- `asyncio_mode = "auto"` hace que todos los tests async se ejecuten sin `@pytest.mark.asyncio` en cada función.
- Mockear los modelos ML con `pytest-mock` o `unittest.mock` para tests unitarios rápidos — los tests con modelos reales van en tests de integración.
- `httpx.AsyncClient` permite testear endpoints FastAPI sin levantar un servidor real.