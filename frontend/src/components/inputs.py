import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config
from flet import Row, ElevatedButton, icons

class GameInputs(Row):
    def __init__(self, on_voice, on_camera):
        super().__init__()
        self.voice_btn = ElevatedButton(
            "Voice Input",
            icon=icons.MIC,
            on_click=on_voice,
            style=config.BUTTON_STYLE
        )
        self.camera_btn = ElevatedButton(
            "Camera Input",
            icon=icons.CAMERA_ALT,
            on_click=on_camera,
            style=config.BUTTON_STYLE
        )
        self.controls = [self.voice_btn, self.camera_btn]
        self.spacing = 20
        self.alignment = "center"
