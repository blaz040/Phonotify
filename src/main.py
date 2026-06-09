from pystray import Icon, Menu, MenuItem, _appindicator
from PIL import Image, ImageDraw
import threading
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication
import phoneNotificator as pn
from log.logsUI import LogUI
from log.logAPI import init_log
from config import IS_LINUX, app_icon


class App:
    App_name = "Phonotify"

    def __init__(self):
        self.current_status = "Disconnected"
        self.icon_ready = threading.Event()

        thread = threading.Thread(target=self.start, daemon=True)
        thread.start()
        self.thread = thread

        self.pn_init()

    # ------------------------------------------------------------------ #
    # phoneNotificator wiring                                              #
    # ------------------------------------------------------------------ #

    def scanning_callback(self, scanning: bool = True):
        self.update_status("Scanning" if scanning else "Sleeping")

    def pn_init(self):
        pn.connection_callback = lambda: self.update_status("Connected")
        pn.disconnect_callback = lambda: self.update_status("Disconnected")
        pn.scanning_callback = self.scanning_callback

        self.icon_ready.wait()

        ble_t = threading.Thread(target=pn.run, daemon=True)
        ble_t.start()
        self.ble_t = ble_t

    # ------------------------------------------------------------------ #
    # Tray icon helpers                                                    #
    # ------------------------------------------------------------------ #

    def create_image(self):
        try:
            if not app_icon.exists():
                raise FileNotFoundError("app icon not found")
            return Image.open(app_icon)
        except Exception:
            image = Image.new("RGB", (64, 64), color=(0, 255, 0))
            draw = ImageDraw.Draw(image)
            draw.rectangle((16, 16, 48, 48), fill="white")
            return image

    def update_status(self, status: str):
        self.current_status = status
        self.icon.title = f"{self.App_name} — {status}"

    # ------------------------------------------------------------------ #
    # Tray menu actions                                                    #
    # ------------------------------------------------------------------ #

    def on_exit(self, icon, item):
        log.info("Exiting application")
        pn.end()
        self.ble_t.join()
        log.info("BLE ended")

        # Schedule logUI teardown on the Qt main thread, then quit the app
        QTimer.singleShot(0, logUI.end)
        QTimer.singleShot(50, QApplication.instance().quit)

        self.icon.stop()

    def disconnect(self, icon, item):
        pn.disconnect()

    def scan(self, icon, item):
        pn.start_scan()

    def show_logs(self, icon, item):
        # Qt GUI must be touched from the main thread — use QTimer.singleShot
        QTimer.singleShot(0, logUI.show_window)

    # ------------------------------------------------------------------ #
    # Tray icon run loop (runs in its own daemon thread)                  #
    # ------------------------------------------------------------------ #

    def start(self):
        menu = Menu(
            MenuItem("Disconnect", self.disconnect),
            MenuItem("Scan", self.scan),
            MenuItem("Logs", self.show_logs, default=True),
            MenuItem("Exit", self.on_exit),
        )

        if IS_LINUX:
            self.icon = Icon(
                self.App_name, self.create_image(), self.App_name,
                tray=_appindicator, menu=menu,
            )
        else:
            self.icon = Icon(
                self.App_name, self.create_image(), self.App_name,
                menu=menu,
            )

        self.icon_ready.set()
        self.icon.run()


# --------------------------------------------------------------------------- #
# Entry point                                                                  #
# --------------------------------------------------------------------------- #

def main():
    global logUI
    global log
    log = init_log("MAIN")

    logUI = LogUI()   # creates QApplication internally if needed
    App()             # no longer needs a root reference

    logUI.start()     # calls app.exec_() — blocks here until quit


if __name__ == "__main__":
    main()