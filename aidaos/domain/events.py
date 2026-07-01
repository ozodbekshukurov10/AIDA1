"""Domain events — decoupled event system for cross-component communication."""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable
from enum import Enum, auto


class DomainEventType(Enum):
    AGENT_STARTED = auto()
    AGENT_COMPLETED = auto()
    AGENT_FAILED = auto()
    TOOL_EXECUTED = auto()
    MESSAGE_SENT = auto()
    MEMORY_STORED = auto()
    MEMORY_RETRIEVED = auto()
    PROVIDER_CHANGED = auto()
    WORKFLOW_STARTED = auto()
    WORKFLOW_COMPLETED = auto()
    WORKFLOW_FAILED = auto()
    PROPOSAL_CREATED = auto()
    PROPOSAL_APPROVED = auto()
    PROPOSAL_REJECTED = auto()
    PROPOSAL_APPLIED = auto()
    ERROR_LOGGED = auto()
    METRICS_UPDATED = auto()
    CODE_INDEXED = auto()
    CODE_GENERATED = auto()


@dataclass
class DomainEvent:
    event_type: DomainEventType
    source: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0
    correlation_id: str = ""

    def to_dict(self) -> dict:
        return {
            "event_type": self.event_type.name,
            "source": self.source,
            "data": {k: str(v)[:100] for k, v in self.data.items()},
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id,
        }


EventHandler = Callable[[DomainEvent], None]


class EventBus:
    """Simple in-process event bus. Can be swapped for Redis/RabbitMQ later."""

    def __init__(self):
        self._handlers: dict[DomainEventType, list[EventHandler]] = {}
        self._history: list[DomainEvent] = []
        self._max_history = 500

    def subscribe(self, event_type: DomainEventType, handler: EventHandler):
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: DomainEventType, handler: EventHandler):
        if event_type in self._handlers:
            self._handlers[event_type] = [h for h in self._handlers[event_type] if h is not handler]

    def publish(self, event: DomainEvent):
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
        for handler in self._handlers.get(event.event_type, []):
            try:
                handler(event)
            except Exception:
                import logging
                logging.getLogger("aidaos.domain.events").exception("Event handler failed")

    def get_history(self, event_type: DomainEventType | None = None, limit: int = 50) -> list[DomainEvent]:
        events = self._history
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events[-limit:]

    def clear(self):
        self._handlers.clear()
        self._history.clear()
