from __future__ import annotations
import json
import logging
import time
from typing import Any

from .base import MemoryItem, MemoryType, MemoryImportance, MemoryQuery, MemoryResult, BaseMemory
from .storage import SQLiteMemoryBackend

logger = logging.getLogger("webapp.memory.compression")


class MemoryCompression:
    def __init__(self, backend: SQLiteMemoryBackend | None = None):
        self._backend = backend or SQLiteMemoryBackend()

    async def compress_old_memories(self, days_old: int = 7,
                                      max_items: int = 100) -> int:
        cutoff = time.time() - (days_old * 86400)
        query = MemoryQuery(query="", limit=max_items, sort_by="timestamp")
        result = await self._backend.search(query)
        old_items = [i for i in result.items if i.timestamp < cutoff and not i.compressed]

        compressed_count = 0
        for item in old_items:
            summary = self._summarize(item.content)
            item.content = summary
            item.compressed = True
            item.metadata["original_length"] = len(item.content)
            item.metadata["compressed_at"] = time.time()
            await self._backend.update(item)
            compressed_count += 1

        logger.info(f"Compressed {compressed_count} old memories")
        return compressed_count

    async def compress_by_importance(self, min_importance: MemoryImportance = MemoryImportance.LOW) -> int:
        query = MemoryQuery(query="", min_importance=min_importance, limit=1000)
        result = await self._backend.search(query)
        compressible = [i for i in result.items if not i.compressed]

        count = 0
        for item in compressible:
            if len(item.content) > 300:
                summary = self._summarize(item.content)
                item.content = summary
                item.compressed = True
                item.metadata["compressed_at"] = time.time()
                await self._backend.update(item)
                count += 1

        return count

    async def decompress(self, item_id: str) -> MemoryItem | None:
        item = await self._backend.get(item_id)
        if item and item.compressed and "original_content" in item.metadata:
            item.content = item.metadata["original_content"]
            item.compressed = False
            await self._backend.update(item)
        return item

    def _summarize(self, text: str, max_length: int = 200) -> str:
        if len(text) <= max_length:
            return text
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        summary = ""
        for s in sentences:
            if len(summary) + len(s) <= max_length:
                summary += s + " "
            else:
                break
        return summary.strip() if summary else text[:max_length] + "..."

    async def get_stats(self) -> dict:
        result = await self._backend.search(MemoryQuery(query="", limit=10000))
        total = len(result.items)
        compressed = sum(1 for i in result.items if i.compressed)
        total_size = sum(len(i.content) for i in result.items)
        return {
            "total_items": total,
            "compressed_items": compressed,
            "total_size_chars": total_size,
            "avg_size_chars": total_size // max(total, 1),
            "compression_ratio": compressed / max(total, 1),
        }
