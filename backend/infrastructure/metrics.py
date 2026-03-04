"""Prometheus metrics instrumentation for VerifID.

Exposes HTTP metrics, pipeline metrics, and ML model metrics.
"""

from prometheus_client import Counter, Gauge, Histogram, Info

# ── Application info ───────────────────────────────────────────────
APP_INFO = Info("verifid", "VerifID application info")
APP_INFO.info({"version": "0.1.0", "service": "verifid-api"})

# ── HTTP request metrics ───────────────────────────────────────────
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint", "status"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 8.0, 15.0],
)

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests currently being processed",
    ["method", "endpoint"],
)

# ── Verification pipeline metrics ──────────────────────────────────
VERIFICATION_TOTAL = Counter(
    "verification_total",
    "Total verification sessions by final status",
    ["status"],  # VERIFIED, REJECTED, MANUAL_REVIEW, ERROR
)

VERIFICATION_SCORE = Histogram(
    "verification_score",
    "Confidence score distribution by module",
    ["module"],
    buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
)

VERIFICATION_DURATION = Histogram(
    "verification_duration_seconds",
    "End-to-end pipeline duration in seconds",
    buckets=[0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 10.0, 15.0],
)

ACTIVE_SESSIONS = Gauge(
    "active_sessions",
    "Number of verification sessions currently processing",
)

# ── Per-module ML metrics ──────────────────────────────────────────
ML_INFERENCE_LATENCY = Histogram(
    "ml_inference_duration_seconds",
    "ML model inference latency in seconds",
    ["model"],  # arcface, anti_spoof, retinaface, xceptionnet, etc.
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0],
)

ML_INFERENCE_TOTAL = Counter(
    "ml_inference_total",
    "Total ML model inferences",
    ["model", "status"],  # status: success, error
)

ML_THROUGHPUT = Counter(
    "ml_inferences_per_second",
    "ML model inference throughput",
    ["model"],
)

# ── Pipeline phase metrics ─────────────────────────────────────────
PHASE_DURATION = Histogram(
    "pipeline_phase_duration_seconds",
    "Duration of each pipeline phase",
    ["phase"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 8.0],
)

PHASE_ERROR_TOTAL = Counter(
    "pipeline_phase_errors_total",
    "Pipeline phase errors",
    ["phase"],
)

# ── Antifraud metrics ──────────────────────────────────────────────
FRAUD_SCORE = Histogram(
    "antifraud_score",
    "Fraud score distribution",
    buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
)

FRAUD_FLAG_TOTAL = Counter(
    "antifraud_flags_total",
    "Antifraud risk flags triggered",
    ["flag_code"],
)

# ── Audit metrics (FAR/FRR tracking) ──────────────────────────────
FALSE_ACCEPTANCE_TOTAL = Counter(
    "far_false_acceptance_total",
    "Known impostors incorrectly accepted (for FAR calculation)",
)

FALSE_REJECTION_TOTAL = Counter(
    "frr_false_rejection_total",
    "Known legitimate users incorrectly rejected (for FRR calculation)",
)

# ── Infrastructure metrics ─────────────────────────────────────────
RATE_LIMIT_HITS = Counter(
    "rate_limit_hits_total",
    "Requests rejected by rate limiting",
    ["endpoint"],
)

CIRCUIT_BREAKER_STATE = Gauge(
    "circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=half_open, 2=open)",
    ["dependency"],
)
