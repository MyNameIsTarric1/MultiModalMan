from flet import colors, ButtonStyle, TextStyle

COLOR_PALETTE = {
    "primary": colors.BLUE_800,
    "secondary": colors.GREY_600,
    "success": colors.GREEN_700,
    "error": colors.RED_700
}

BUTTON_STYLE = ButtonStyle(
    color=COLOR_PALETTE["primary"],
    bgcolor=colors.BLUE_200,
    padding=20
)

TITLE_STYLE = TextStyle(
    size=40,
    weight="bold",
    color=COLOR_PALETTE["primary"]
)

STATUS_STYLE = TextStyle(
    size=18,
    color=COLOR_PALETTE["error"]
)
