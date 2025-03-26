import asyncio

from textual.widget import Widget
from textual.widgets import Input, Static


class UserMessageBox(Widget):
    DEFAULT_CSS = """
        UserMessageBox {
            height: auto;
            Static {
                border: dashed blue;
            }
        }
    """

    def __init__(self, *args, reason: str | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        # @TODO: This doesn't do newlines
        self.input = Input(placeholder="Enter your response")
        self.reason = reason
        if reason:
            self.input.border_title = reason
        self.submission = asyncio.Future[str]()

    def compose(self):
        yield self.input

    def on_mount(self) -> None:
        self.input.focus()

    async def on_input_submitted(self, event: Input.Changed) -> None:
        self.submission.set_result(event.value)
        self.input.remove()
        text_box = Static(event.value)
        text_box.border_title = self.reason or "User"
        self.mount(text_box)
