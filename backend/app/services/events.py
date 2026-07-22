import asyncio
from collections import defaultdict
from typing import Any

_queues: dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)

_SENTINEL = {"event": "__close__"}


def get_queue(key: str) -> asyncio.Queue:
    return _queues[key]


async def publish(key: str, event: dict[str, Any]) -> None:
    await _queues[key].put(event)


async def close(key: str) -> None:
    await _queues[key].put(_SENTINEL)


async def stream(key: str):
    """Async generator yielding events for `key` until close() is called."""
    queue = get_queue(key)
    try:
        while True:
            event = await queue.get()
            if event is _SENTINEL or event == _SENTINEL:
                break
            yield event
    finally:
        _queues.pop(key, None)
