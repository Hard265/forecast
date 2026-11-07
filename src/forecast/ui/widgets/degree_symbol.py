from textual.widget import Widget


class DegreeSymbol(Widget):
    """A two-line degree symbol, aligned to the top of the digits."""

    DEFAULT_CSS = """
    DegreeSymbol {
        width: 3;
        height: 2;
        margin-left: 1;
    }
    """

    def render(self) -> str:
        return "┌─┐\n└─┘"
