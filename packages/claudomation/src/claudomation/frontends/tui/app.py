from collections.abc import Awaitable, Callable
from typing import ClassVar

from rich.theme import Theme
from textual import work
from textual.app import App
from textual.containers import VerticalScroll

# @TODO: I think this is dead code?
STYLES = {
    "claude": "#da7756",
    "claude.primary": "#da7756",
    "claude.secondary": "#e5a18a",
    "claude.dim": "#9d6958",
    "tool.name": "#5ebcdc",
    "tool.result": "#80dc61",
    # @TODO: agent color(s)?
    "agent.name": "#ffd4c2",
    "agent.response": "#ffd4c2",
    # @TODO: Human prompt color
}


# @TODO: Add header with some context?
# @TODO: Add footer with some key bindings?
# @TODO: Add screen(s) for MCP servers/debugging
class ClaudomationTUIApp(App):
    BINDINGS: ClassVar = [
        ("ctrl+c", "quit"),
    ]

    # @TODO: Dead code?
    CSS = """
    .color--claude {
        color: #da7756;
    }
    """

    chat_log: VerticalScroll

    worker_run: Callable[[VerticalScroll], Awaitable]

    def __init__(self, *args, worker_run: Callable[[VerticalScroll], Awaitable], **kwargs):
        super().__init__(*args, **kwargs)
        self.console.push_theme(Theme(STYLES))
        self.worker_run = worker_run
        self.chat_log = VerticalScroll()

    @work(exclusive=True)
    async def _run_worker(self) -> None:
        await self.worker_run(self.chat_log)

    def on_mount(self) -> None:
        self.mount(self.chat_log)
        self._run_worker()
