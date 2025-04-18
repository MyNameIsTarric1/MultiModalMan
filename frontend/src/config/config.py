from flet import Colors, ButtonStyle, TextStyle

COLOR_PALETTE = {
    "primary": Colors.BLUE_800,
    "secondary": Colors.GREY_600,
    "success": Colors.GREEN_700,
    "error": Colors.RED_700,
    "background": Colors.WHITE
}

BUTTON_STYLE = ButtonStyle(
    color=Colors.WHITE,
    bgcolor=Colors.BLUE_500,
    padding=20
)

TITLE_STYLE = TextStyle(
    size=40,
    weight="bold",
    color=COLOR_PALETTE["primary"]
)

SUBTITLE_STYLE = TextStyle(
    size=24,
    weight="bold",
    color=COLOR_PALETTE["primary"]
)

STATUS_STYLE = TextStyle(
    size=18,
    color=COLOR_PALETTE["secondary"]
)
