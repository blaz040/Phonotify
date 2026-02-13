from pystray import Icon, Menu, MenuItem, _appindicator
from PIL import Image, ImageDraw
import threading
import asyncio
import phoneNotificator as pn
from logsUI import LogUI
from logAPI import log
import tkinter as tk 


class App:
    App_name = "Phonotify"
    
    def __init__(self, root):
        self.root = root

        thread = threading.Thread(target = self.start)
        thread.daemon = True
        thread.start()
        
        ble_t = threading.Thread(target = pn.run, daemon=True)
        ble_t.start()
    
        self.thread = thread
        self.ble_t = ble_t

    def create_image(self):
        image = Image.new('RGB', (64, 64), color=(0, 255, 0))
        draw = ImageDraw.Draw(image)
        draw.rectangle((16, 16, 48, 48), fill='white')
        return image

    def on_exit(self, icon, item):
        print("Exiting application")
        pn.end()
        self.ble_t.join()        
        print("BLE ending...")
        
        print("Hiding log UI....")
        logUI.end()

        icon.stop()
        
    def on_reconnect(icon, item):
        pn.disconnect()
        
    def show_logs(icon, item):
        logUI.show_window()
        
    def start(self):
        # MENU
        icon = Icon(self.App_name, self.create_image(), self.App_name, tray = _appindicator, menu = Menu(
            MenuItem("Recconect", self.on_reconnect),
            MenuItem("Logs" ,self.show_logs, default = True),
            MenuItem("Exit", self.on_exit)
        ))
        
        icon.run()

def main():
    global logUI
        
    logUI = LogUI()

    app = App(logUI.root)
    
    logUI.start()


if __name__ == "__main__":
    main()