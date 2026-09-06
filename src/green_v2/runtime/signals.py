from __future__ import annotations

import asyncio
import signal
import threading


def install_async_stop(event: asyncio.Event) -> None:
    loop = asyncio.get_running_loop()
    for signal_name in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(signal_name, event.set)


def install_thread_stop(event: threading.Event) -> None:
    def stop(_signum: int, _frame: object) -> None:
        event.set()

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
