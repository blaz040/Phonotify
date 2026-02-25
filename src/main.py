from pystray import Icon, Menu, MenuItem, _appindicator
from PIL import Image, ImageDraw
import threading
import asyncio
import phoneNotificator as pn
from logsUI import LogUI
from logAPI import init_log
import tkinter as tk 
from pathlib import Path

class App:
    App_name = "Phonotify"
    app_icon = Path(__file__).parent.parent / "icons" / "app" / "phonotify_logo_minimalistic.png"

    def __init__(self, root):
        self.root = root
        self.current_status = "Disconnected"
        self.icon_ready = threading.Event()

        thread = threading.Thread(target = self.start)
        thread.daemon = True
        thread.start()
        self.thread = thread
        
        self.pn_init()
    
    def scanning_callback(self, scanning: bool = True):
        status = "Scanning"
        if scanning is False:
            status = "Sleeping"

        self.update_status(status=status) 

    def pn_init(self):
        pn.connection_callback = lambda: self.update_status(status="Connected")
        pn.disconnect_callback = lambda: self.update_status(status="Disconnected")
        pn.scanning_callback = self.scanning_callback
        
        self.icon_ready.wait()

        ble_t = threading.Thread(target = pn.run, daemon=True)
        ble_t.start()

        self.ble_t = ble_t
    
    def create_image(self):

        image = Image.open(self.app_icon)
        if not self.app_icon.exists:
            image = Image.new('RGB', (64, 64), color=(0, 255, 0))
            draw = ImageDraw.Draw(image)
            draw.rectangle((16, 16, 48, 48), fill='white')
        return image

    def on_exit(self, icon, item):
        log.info("Exiting application")
        print("Exiting application")

        pn.end()
        self.ble_t.join()        
        log.info("BLE ended...")
        print("BLE ending")
        
        log.info("Hiding log UI....")
        print("Hiding log UI....")
        logUI.end()

        self.icon.stop()
        
    def disconnect(self, icon, item):
        pn.disconnect()

    def scan(self, icon, item):
        pn.start_scan()

    def show_logs(icon, item):
        logUI.show_window()

    def get_status_text(self, item):
        return f"Status: {self.current_status}"

    def update_status(self, status:str):
        self.current_status = status
        self.icon.update_menu()

    def start(self):
        # MENU
        self.icon = Icon(self.App_name, self.create_image(), self.App_name, tray = _appindicator, menu = Menu(
            MenuItem(self.get_status_text, action=None, enabled=False),
            MenuItem("Disconnect", self.disconnect),
            MenuItem("Scan", self.scan),
            MenuItem("Logs" ,self.show_logs, default = True),
            MenuItem("Exit", self.on_exit),
        ))
        self.icon_ready.set()
        
        self.icon.run()

def main():
    global logUI
    global log

    log = init_log("MAIN")

    logUI = LogUI()

    app = App(logUI.root)
    
    logUI.start()


if __name__ == "__main__":
    main()