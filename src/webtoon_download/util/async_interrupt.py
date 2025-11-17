import asyncio
import signal


def create_interrupt_future(
    loop: asyncio.AbstractEventLoop | None = None,
    signals: list[signal.Signals] | None = None,
) -> asyncio.Future[None]:
    if loop is None:
        loop = asyncio.get_running_loop()
    if signals is None:
        signals = [signal.SIGINT, signal.SIGTERM]

    interrupted = loop.create_future()

    def on_interrupt(signal_index: int):
        if interrupted.done():
            return
        interrupted.set_result(None)

    signal.signal(signal.SIGINT, signal.SIG_IGN)

    for signal_index in signals:
        loop.add_signal_handler(signal_index, on_interrupt, signal_index)
    return interrupted


__all__ = ("create_interrupt_future",)
