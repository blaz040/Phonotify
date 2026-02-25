import platform
from pathlib import Path

IS_LINUX = platform.system() == "Linux"
IS_WINDOWS = platform.system() == "Windows"
app_icon = Path(__file__).parent.parent / "icons" / "app" / "phonotify_logo_minimalistic.png"

