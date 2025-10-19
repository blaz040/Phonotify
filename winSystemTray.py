from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw
import threading
import time
import sys

import phoneNotificator as pn

import logsUI as logUI

import logging as logAPI

App_name = "Phonotify"
def create_image():
    image = Image.new('RGB', (64, 64), color=(0, 255, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((16, 16, 48, 48), fill='white')
    return image

def on_exit(icon, item):
    logUI.end()
    icon.stop()
    

def on_reconnect():
    pn.reconnect()
    
def show_logs():
    logUI.run()
    
def app_icon():
    icon = Icon(App_name, create_image(), App_name, menu=Menu(
        MenuItem("Recconect",on_reconnect),
        MenuItem("Logs",show_logs),
        MenuItem("Exit", on_exit)
    ))
    icon.run()

def main():
    t = threading.Thread(target=lambda: [
            pn.run()
        ])
    t.daemon = True
    t.start()
    app_icon()
    
if __name__ == "__main__":
    main()
