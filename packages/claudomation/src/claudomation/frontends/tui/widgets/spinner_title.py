from collections.abc import Callable

from textual.reactive import reactive
from textual.widget import Widget


class WithSpinner(Widget):
    _spinner_index: reactive[float] = reactive(1.0, layout=True)
    __handler: Callable[[str], None]
    __spinner_frames: list[str]

    def animate_spinner(self, handler: Callable[[str], None], frames: list[str]) -> None:
        self.__handler = handler
        self.__spinner_frames = frames
        self.animate("_spinner_index", value=1_000_000, speed=6.0, easing="linear")

    def watch__spinner_index(self, old_index: float, new_index: float) -> None:
        spark = self.__spinner_frames[int(new_index) % len(self.__spinner_frames)]
        self.__handler(spark)

    async def stop_spinning(self) -> None:
        await super().stop_animation("_spinner_index")
