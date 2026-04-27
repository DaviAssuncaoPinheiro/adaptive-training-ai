from __future__ import annotations

import hashlib
import json
import os
import threading
from pathlib import Path
from typing import Any


class ReferenceCache:
    """Persistent JSON cache for LLM-generated justifications.

    Why a file and not Redis: the deployment target is a single-user local
    box (Ollama + ChromaDB already run locally); adding a service just to
    dedupe a handful of prompt hits would be overkill.

    Writes are atomic: we serialize the whole dict to a sibling .tmp file and
    then os.replace() it onto the target. This means a concurrent reader can
    never observe a half-written file, so reads don't need the lock.
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.Lock()

    def make_key(self, query: dict[str, Any]) -> str:
        canonical = json.dumps(query, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def get(self, key: str) -> dict[str, Any] | None:
        data = self._load()
        return data.get(key)

    def set(self, key: str, value: dict[str, Any]) -> None:
        with self._lock:
            data = self._load()
            data[key] = value
            self._path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._path.with_suffix(self._path.suffix + ".tmp")
            tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            os.replace(tmp, self._path)

    def _load(self) -> dict[str, Any]:
        if not self._path.exists():
            return {}
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            # A JSON decode error now can only come from a hand-edited file
            # (our own writes are atomic) — treat as empty and overwrite.
            return {}
