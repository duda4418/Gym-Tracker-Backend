from __future__ import annotations

from threading import Lock

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased

from app.core.config import Settings
from app.db.database import engine

_telemetry_lock = Lock()
_telemetry_configured = False


def configure_telemetry(app: FastAPI, settings: Settings) -> None:
    """Configure application tracing and export spans to the OTel collector."""
    global _telemetry_configured

    if not settings.OTEL_ENABLED:
        return

    with _telemetry_lock:
        if _telemetry_configured:
            return

        resource = Resource.create(
            {
                SERVICE_NAME: settings.OTEL_SERVICE_NAME,
                SERVICE_VERSION: settings.OTEL_SERVICE_VERSION,
                "deployment.environment": settings.OTEL_ENVIRONMENT,
            }
        )
        provider = TracerProvider(
            resource=resource,
            sampler=ParentBased(TraceIdRatioBased(settings.OTEL_TRACES_SAMPLER_RATIO)),
        )
        provider.add_span_processor(
            BatchSpanProcessor(
                OTLPSpanExporter(
                    endpoint=settings.OTEL_EXPORTER_OTLP_TRACES_ENDPOINT,
                    timeout=settings.OTEL_EXPORTER_TIMEOUT_SECONDS,
                )
            )
        )
        trace.set_tracer_provider(provider)

        FastAPIInstrumentor.instrument_app(
            app,
            tracer_provider=provider,
            excluded_urls="/metrics,/docs,/openapi.json,/redoc",
        )
        SQLAlchemyInstrumentor().instrument(engine=engine, tracer_provider=provider)
        RequestsInstrumentor().instrument(tracer_provider=provider)
        app.add_event_handler("shutdown", provider.shutdown)

        _telemetry_configured = True


