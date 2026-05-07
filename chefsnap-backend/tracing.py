"""
tracing.py — OpenTelemetry setup for ChefSnap FastAPI backend.

Call configure_tracing(app) once at startup. Tracing is opt-in:
set OTEL_ENABLED=true and OTEL_EXPORTER_OTLP_ENDPOINT to activate.

Usage in agent/vision code:
    from tracing import llm_span
    with llm_span("recipe_agent.suggest", model=AGENT_MODEL) as span:
        result = ...
        span.set_attribute("recipe.count", len(result.recipes))
"""

import os
import logging
from contextlib import contextmanager
from typing import Generator

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

logger = logging.getLogger(__name__)

# Module-level tracer — safe to import before configure_tracing is called;
# will use the no-op provider until configure_tracing sets the real one.
tracer: trace.Tracer = trace.get_tracer("chefsnap")


def configure_tracing(app) -> None:
    """Instrument the FastAPI app. Called once in main.py at startup."""
    if os.getenv("OTEL_ENABLED", "false").lower() != "true":
        logger.info("OTel tracing disabled — set OTEL_ENABLED=true to enable")
        return

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    try:
        provider = TracerProvider()
        exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)

        global tracer
        tracer = trace.get_tracer("chefsnap")

        FastAPIInstrumentor.instrument_app(app)
        logger.info("OTel tracing enabled → %s", endpoint)
    except Exception as exc:
        logger.warning("OTel setup failed (tracing disabled): %s", exc)


@contextmanager
def llm_span(name: str, **attributes) -> Generator[trace.Span, None, None]:
    """Context manager that wraps an LLM call in an OTel span."""
    with tracer.start_as_current_span(name) as span:
        for k, v in attributes.items():
            span.set_attribute(k, str(v))
        yield span
