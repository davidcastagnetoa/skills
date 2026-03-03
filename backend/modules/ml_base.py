"""Base class for all ML model wrappers in the KYC pipeline."""

import time
from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np
import structlog

logger = structlog.get_logger()


class BaseMLModel(ABC):
    """Base class for ML models served via ONNX Runtime.

    Handles model loading, warmup, and inference timing.
    Subclasses implement `preprocess` and `postprocess`.
    """

    def __init__(self, model_path: str | Path, providers: list[str] | None = None) -> None:
        self.model_path = Path(model_path)
        self.model_name = self.model_path.stem
        self._session = None
        self._providers = providers or ["CPUExecutionProvider"]
        self._load()
        self._warmup()

    def _load(self) -> None:
        """Load the ONNX model into an inference session."""
        import onnxruntime as ort

        if not self.model_path.exists():
            logger.warning("model.not_found", model=self.model_name, path=str(self.model_path))
            return

        self._session = ort.InferenceSession(
            str(self.model_path),
            providers=self._providers,
        )
        input_info = self._session.get_inputs()
        output_info = self._session.get_outputs()
        logger.info(
            "model.loaded",
            model=self.model_name,
            inputs=[i.name for i in input_info],
            outputs=[o.name for o in output_info],
        )

    def _warmup(self) -> None:
        """Run a dummy inference to pre-allocate memory and JIT compile."""
        if self._session is None:
            return

        try:
            dummy_input = self._create_dummy_input()
            self._session.run(None, dummy_input)
            logger.info("model.warmup_complete", model=self.model_name)
        except Exception as e:
            logger.warning("model.warmup_failed", model=self.model_name, error=str(e))

    @abstractmethod
    def _create_dummy_input(self) -> dict[str, np.ndarray]:
        """Create a dummy input for warmup. Must match model's expected input shape."""
        ...

    @abstractmethod
    def preprocess(self, raw_input: object) -> dict[str, np.ndarray]:
        """Transform raw input into model-ready numpy arrays."""
        ...

    @abstractmethod
    def postprocess(self, raw_output: list[np.ndarray]) -> object:
        """Transform model output into a structured result."""
        ...

    def predict(self, raw_input: object) -> object:
        """Run full inference pipeline: preprocess → infer → postprocess."""
        if self._session is None:
            raise RuntimeError(f"Model '{self.model_name}' is not loaded")

        start = time.perf_counter()
        model_input = self.preprocess(raw_input)
        raw_output = self._session.run(None, model_input)
        result = self.postprocess(raw_output)
        elapsed_ms = (time.perf_counter() - start) * 1000

        logger.debug(
            "model.inference",
            model=self.model_name,
            elapsed_ms=round(elapsed_ms, 2),
        )
        return result

    @property
    def is_loaded(self) -> bool:
        return self._session is not None

    @property
    def input_shapes(self) -> dict[str, list[int | str]]:
        """Return the expected input shapes of the model."""
        if self._session is None:
            return {}
        return {inp.name: inp.shape for inp in self._session.get_inputs()}
