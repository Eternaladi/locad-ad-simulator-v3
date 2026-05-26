from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def retry(fn: Callable[[], T], attempts: int = 3, base_sleep: float = 0.5) -> T:
    last_exc: Exception | None = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as exc:  # pragma: no cover - defensive for external APIs
            last_exc = exc
            if i < attempts - 1:
                time.sleep(base_sleep * (2 ** i))
    assert last_exc is not None
    raise last_exc
