from pathlib import Path
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor, SpanExporter, SpanExportResult)
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from openinference.instrumentation.langchain import LangChainInstrumentor

LOG_DIR = Path("logs")


class JsonlSpanExporter(SpanExporter):
    """Writes every span as one JSON line, so you can read or share the agent logs."""

    def __init__(self, path):
        self.path = path

    def export(self, spans):
        with open(self.path, "a", encoding="utf-8") as f:
            for s in spans:
                f.write(s.to_json(indent=None) + "\n")
        return SpanExportResult.SUCCESS

    def shutdown(self):
        pass


def setup_tracing(endpoint: str = "http://localhost:6006/v1/traces"):
    LOG_DIR.mkdir(exist_ok=True)
    provider = TracerProvider(resource=Resource.create({
        "service.name": "cds-assistant",
        "openinference.project.name": "cds-assistant",
    }))
    # 1) send to the OpenTelemetry tool (Phoenix)
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
    # 2) save a local copy of the agent logs
    provider.add_span_processor(BatchSpanProcessor(JsonlSpanExporter(LOG_DIR / "agent_traces.jsonl")))
    trace.set_tracer_provider(provider)
    LangChainInstrumentor().instrument(tracer_provider=provider)