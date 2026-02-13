from pathlib import Path


BASE_DIR = Path(__file__).parent.parent
ICON_FOLDER_DIR = BASE_DIR / "icons"

APP_ICON_PATH = ICON_FOLDER_DIR / "recentApp_icon.png"
NOT_FOUND_ICON_PATH = ICON_FOLDER_DIR / "NotFound_icon.png"
CHECK_ICON_PATH = ICON_FOLDER_DIR / "check.png"
CROSS_ICON_PATH = ICON_FOLDER_DIR / "cross.png"
print(ICON_FOLDER_DIR)