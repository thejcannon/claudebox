from claudomation.frontends.tui.widgets.spinner_title import WithSpinner

SPARK_FRAMES = ["·", "✢", "✳", "∗", "✻", "✽", "✲"]  # noqa: RUF001


class ClaudeMessageBox(WithSpinner):
    DEFAULT_CSS = """
        ClaudeMessageBox {
            width: 100%;
            height: auto;
            border: solid #da7756;
        }
    """

    def render(self):
        # @TODO: Make this height 0?
        return ""

    def on_mount(self) -> None:
        def animate_border_title(spark: str) -> None:
            self.border_title = f"{spark} Claude {spark}"

        self.animate_spinner(animate_border_title, frames=SPARK_FRAMES)
