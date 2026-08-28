"""
AIDA Enterprise API — SSE Streaming

Server-Sent Events — AI javoblari uchun real-time streaming.
"""
from __future__ import annotations
import json
import time
from typing import AsyncIterator, Generator
from django.http import StreamingHttpResponse


class SSEEvent:
    """SSE event yaratish."""

    def __init__(self, event: str = "message", data: str = "", id: str = ""):
        self.event = event
        self.data = data
        self.id = id

    def to_string(self) -> str:
        """SSE formatiga aylantirish."""
        lines = []
        if self.id:
            lines.append(f"id: {self.id}")
        if self.event:
            lines.append(f"event: {self.event}")
        for line in self.data.split("\n"):
            lines.append(f"data: {line}")
        lines.append("")
        lines.append("")
        return "\n".join(lines)


def create_sse_response(
    generator: Generator | AsyncIterator,
    content_type: str = "text/event-stream",
) -> StreamingHttpResponse:
    """SSE response yaratish."""
    def stream():
        for event in generator:
            if isinstance(event, SSEEvent):
                yield event.to_string()
            else:
                yield f"data: {json.dumps(event)}\n\n"

    response = StreamingHttpResponse(stream(), content_type=content_type)
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    response["Connection"] = "keep-alive"
    return response


def text_stream(text: str, chunk_size: int = 10) -> Generator[SSEEvent, None, None]:
    """Matnni bo'laklarga bo'lib stream qilish."""
    words = text.split()
    current_chunk = []
    for word in words:
        current_chunk.append(word)
        if len(current_chunk) >= chunk_size:
            yield SSEEvent(
                event="text",
                data=json.dumps({"content": " ".join(current_chunk) + " "}),
            )
            current_chunk = []
    if current_chunk:
        yield SSEEvent(
            event="text",
            data=json.dumps({"content": " ".join(current_chunk)}),
        )
    yield SSEEvent(event="done", data=json.dumps({"done": True}))


def token_stream(tokens: list[str]) -> Generator[SSEEvent, None, None]:
    """Tokenlarni ketma-ket stream qilish."""
    for i, token in enumerate(tokens):
        yield SSEEvent(
            event="token",
            data=json.dumps({
                "content": token,
                "index": i,
                "total": len(tokens),
            }),
        )
    yield SSEEvent(event="done", data=json.dumps({"done": True}))


def progress_stream(steps: list[dict]) -> Generator[SSEEvent, None, None]:
    """Jarayon yangiliklarini stream qilish."""
    total = len(steps)
    for i, step in enumerate(steps):
        yield SSEEvent(
            event="progress",
            data=json.dumps({
                "step": step.get("name", f"Step {i+1}"),
                "status": step.get("status", "running"),
                "progress": int((i + 1) / total * 100),
                "detail": step.get("detail", ""),
            }),
        )
    yield SSEEvent(event="done", data=json.dumps({"done": True}))
