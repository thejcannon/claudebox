import asyncio

from anthropic.types.tool_use_block import ToolUseBlock
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widget import Widget
from textual.widgets import Button, Pretty

from claudomation.frontends.tui.widgets.spinner_title import WithSpinner

TOOL_RUNNING_FRAMES = [" □", " ▯", " □", " ▭", " ▱", " ◻"]


class ToolOutputBlock(Pretty, WithSpinner):
    DEFAULT_CSS = """
        ToolOutputBlock {
            height: auto;
        }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(TOOL_RUNNING_FRAMES[0], **kwargs)

    def on_mount(self) -> None:
        self.animate_spinner(lambda spark: self.update(spark), frames=TOOL_RUNNING_FRAMES)


# @TODO: Maybe we want to use a collapseable for this (since the input/outputs can get big?)
class ToolUseBox(Widget):
    # @TODO: Need to use a grid to display __summary__

    DEFAULT_CSS = """
        ToolUseBox {
            layout: horizontal;
            width: 100%;
            height: auto;
            border: ascii gray;
            margin: 0 2;
            background: $background;

            &.success {
                border: solid $success !important;
            }

            &.error {
                border: solid $error !important;
            }

            &.denied {
                tint: $surface-darken-1 30% !important;
                background-tint: $surface-lighten-1 40% !important;
            }
        }
        .tool-input-block {
            width: 1fr;
            border: solid gray;
        }
        .tool-output-block {
            width: 1fr;
            border: solid gray;
        }
        .confirmation-buttons {
            width: 1fr;
            height: auto;
            align: right middle;
        }
        #approve {
            margin: 0 1;
        }
    """

    def __init__(self, tool_use_block: ToolUseBlock, summary: str, requires_approval: bool = True) -> None:
        super().__init__()
        self.tool_use_block = tool_use_block
        self.requires_approval = requires_approval
        self.decision = asyncio.Future()
        if not requires_approval:
            self.decision.set_result(True)

        assert isinstance(tool_use_block.input, dict)
        summary = tool_use_block.input.pop(summary, None)

        # @TODO: It'd be DOPE AS HELL if the title was a clickable link to the source
        # (OMG it works: `[link=...][white]...[/white][/link]`)
        self.border_title = Text.from_markup(f"[#5ebcdc]{summary}[/#5ebcdc] [white]{tool_use_block.name}[/white]")

        self.border_subtitle = tool_use_block.id
        self.input_block = Pretty(tool_use_block.input, classes="tool-input-block")
        self.input_block.border_title = "Input"
        self.output_block = ToolOutputBlock(classes="tool-output-block")
        self.output_block.border_title = "Output"

    def compose(self) -> ComposeResult:
        yield self.input_block
        if self.requires_approval:
            with Horizontal(classes="confirmation-buttons", id="confirmation-buttons"):
                yield Button("Deny", variant="error", id="deny")
                yield Button("Approve", variant="success", id="approve")
        else:
            yield self.output_block

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        approved = event.button.id == "approve"
        self.decision.set_result(approved)
        self.get_child_by_id("confirmation-buttons").remove()
        if not approved:
            self.add_class("denied")
        else:
            self.mount(self.output_block)

    async def set_tool_result(self, result: object) -> None:
        await self.output_block.stop_spinning()
        self.output_block.update(result)
