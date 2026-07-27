import asyncio

_tasks: dict[str, asyncio.Task] = {}


def register(run_id: str, task: asyncio.Task) -> None:
    _tasks[run_id] = task
    task.add_done_callback(lambda _: _tasks.pop(run_id, None))


def cancel(run_id: str) -> bool:
    task = _tasks.get(run_id)
    if task is None or task.done():
        return False
    task.cancel()
    return True
