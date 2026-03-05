"""Triton Inference Server gRPC client with ONNX Runtime fallback.

When Triton is available, inference is routed via gRPC for maximum
performance and dynamic batching.  If Triton is unreachable the client
transparently falls back to local ONNX Runtime inference.
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import structlog

logger = structlog.get_logger()

_TRITON_URL = os.getenv("TRITON_GRPC_URL", "triton:8001")
_MODELS_DIR = Path(os.getenv("MODELS_DIR", "./models"))


class TritonInferenceClient:
    """Unified inference client — Triton gRPC primary, ONNX Runtime fallback."""

    def __init__(self) -> None:
        self._grpc_client = None
        self._ort_sessions: dict[str, object] = {}
        self._triton_available = False
        self._connect_triton()

    # ------------------------------------------------------------------
    # Connection helpers
    # ------------------------------------------------------------------

    def _connect_triton(self) -> None:
        """Try to establish a gRPC connection to Triton."""
        try:
            import tritonclient.grpc as grpcclient

            client = grpcclient.InferenceServerClient(url=_TRITON_URL)
            if client.is_server_live():
                self._grpc_client = client
                self._triton_available = True
                logger.info("triton.connected", url=_TRITON_URL)
            else:
                logger.warning("triton.not_live", url=_TRITON_URL)
        except Exception as exc:
            logger.warning("triton.unavailable", error=str(exc))

    def _get_ort_session(self, model_name: str):
        """Lazy-load an ONNX Runtime session for *model_name*."""
        if model_name in self._ort_sessions:
            return self._ort_sessions[model_name]

        import onnxruntime as ort

        model_path = _MODELS_DIR / f"{model_name}.onnx"
        if not model_path.exists():
            raise FileNotFoundError(f"ONNX model not found: {model_path}")

        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        session = ort.InferenceSession(str(model_path), providers=providers)
        self._ort_sessions[model_name] = session
        logger.info("ort.session_loaded", model=model_name)
        return session

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def infer(
        self,
        model_name: str,
        inputs: dict[str, np.ndarray],
        output_names: list[str] | None = None,
    ) -> dict[str, np.ndarray]:
        """Run inference on *model_name*.

        Args:
            model_name: Registered model name (e.g. ``"arcface"``).
            inputs: Mapping of input name → numpy array.
            output_names: Requested output tensor names.  ``None`` = all.

        Returns:
            Mapping of output name → numpy array.
        """
        if self._triton_available:
            try:
                return self._infer_triton(model_name, inputs, output_names)
            except Exception as exc:
                logger.warning(
                    "triton.infer_failed",
                    model=model_name,
                    error=str(exc),
                )
                # Fall through to ONNX Runtime

        return self._infer_ort(model_name, inputs, output_names)

    # ------------------------------------------------------------------
    # Triton gRPC inference
    # ------------------------------------------------------------------

    def _infer_triton(
        self,
        model_name: str,
        inputs: dict[str, np.ndarray],
        output_names: list[str] | None,
    ) -> dict[str, np.ndarray]:
        import tritonclient.grpc as grpcclient

        triton_inputs = []
        for name, data in inputs.items():
            inp = grpcclient.InferInput(
                name, list(data.shape), grpcclient.np_to_triton_dtype(data.dtype)
            )
            inp.set_data_from_numpy(data)
            triton_inputs.append(inp)

        triton_outputs = None
        if output_names:
            triton_outputs = [
                grpcclient.InferRequestedOutput(n) for n in output_names
            ]

        response = self._grpc_client.infer(
            model_name=model_name,
            inputs=triton_inputs,
            outputs=triton_outputs,
        )

        result: dict[str, np.ndarray] = {}
        names = output_names or [
            response.get_output(i).name
            for i in range(len(response.get_response().outputs))
        ]
        for name in names:
            result[name] = response.as_numpy(name)

        logger.debug("triton.infer_ok", model=model_name)
        return result

    # ------------------------------------------------------------------
    # ONNX Runtime fallback
    # ------------------------------------------------------------------

    def _infer_ort(
        self,
        model_name: str,
        inputs: dict[str, np.ndarray],
        output_names: list[str] | None,
    ) -> dict[str, np.ndarray]:
        session = self._get_ort_session(model_name)
        ort_outputs = session.run(output_names, inputs)

        if output_names:
            return dict(zip(output_names, ort_outputs))

        return {
            out.name: arr
            for out, arr in zip(session.get_outputs(), ort_outputs)
        }

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    @property
    def is_triton_available(self) -> bool:
        return self._triton_available

    def health_check(self) -> dict[str, bool]:
        """Return health status of inference backends."""
        triton_ok = False
        if self._grpc_client:
            try:
                triton_ok = self._grpc_client.is_server_live()
            except Exception:
                pass

        return {
            "triton": triton_ok,
            "ort_fallback": True,
        }
