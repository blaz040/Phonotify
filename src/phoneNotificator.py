import asyncio
from bleak import BleakClient, BleakScanner, BleakGATTCharacteristic, BLEDevice
from bleak.exc import BleakError
import contextlib
from plyer import notification
import requests
from google_play_scraper import app
from logAPI import log
from pathlib import Path
from pystray import Icon
from PIL import Image
import functools
import time

# =============================== Main variables ================================================= 
NOTIFICATION_NAME = "Notification from Phone"
PHONE_NAME = "phServer"

running = True  
connected = True 
client:BleakClient = None 
scan_counter = 0

 
HEALTH_CHECK_INTERVAL = 15 # seconds 
SCAN_DURATION = 3 #seconds
MAX_SCAN_SLEEP_TIME = 5 * 60
TAG = "BLE THREAD: "

# =============================== Path's ================================================= 
# Get the folder where the script lives
BASE_DIR = Path(__file__).parent.parent 
    
# Construct absolute path to icon
ICON_FOLDER_DIR = BASE_DIR / "icons"

APP_ICON_PATH = ICON_FOLDER_DIR / "recentApp_icon.png"
NOT_FOUND_ICON_PATH = ICON_FOLDER_DIR / "NotFound_icon.png"
CHECK_ICON_PATH = ICON_FOLDER_DIR / "check.png"
CROSS_ICON_PATH = ICON_FOLDER_DIR / "cross.png"

# =============================== UUID'S ================================================= 
NOTIFICATION_SERVICE_UUID               = "91d76000-ac7b-4d70-ab3a-8b87a357239e"

TITLE_CHARACTERISTIC_UUID               = "91d76001-ac7b-4d70-ab3a-8b87a357239e"
CONTEXT_CHARACTERISTIC_UUID             = "91d76002-ac7b-4d70-ab3a-8b87a357239e"
PACKAGE_CHARACTERISTIC_UUID             = "91d76003-ac7b-4d70-ab3a-8b87a357239e"
NOTIFY_COMPLETE_CHARACTERISTIC_UUID     = "91d76004-ac7b-4d70-ab3a-8b87a357239e"
DISCONNECT_CHARACTERISTIC_UUID          = "91d76005-ac7b-4d70-ab3a-8b87a357239e"
HEALTH_CHECK_CHARACTERISTIC_UUID        = "91d76006-ac7b-4d70-ab3a-8b87a357239e"

# =============================== Characteristics ================================================= 
# UUID to characteristic name 
characteristics = {
    TITLE_CHARACTERISTIC_UUID: "title",
    CONTEXT_CHARACTERISTIC_UUID: "text context",
    PACKAGE_CHARACTERISTIC_UUID: "package name",
    NOTIFY_COMPLETE_CHARACTERISTIC_UUID: "notifier",
    DISCONNECT_CHARACTERISTIC_UUID: "disconnect",
    HEALTH_CHECK_CHARACTERISTIC_UUID: "health check"
}
#======================================= Intercptor ==========================================================
def intercept_ble_call(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        MAX_LOG_TEXT_SIZE = 50
        text = f"{TAG}=== Running {func.__name__} "
        log.info(f"{text:=<{MAX_LOG_TEXT_SIZE}}")
        start_time = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            log.info(f"{TAG}Intercepted error in {func.__name__}: {e}")
            raise
        finally:
            end_time = time.perf_counter()

            text = f"{TAG}=== Finished {func.__name__} in {end_time - start_time:.4f}s "
            log.info(f"{text:=<{MAX_LOG_TEXT_SIZE}}")
    return wrapper
# =============================== Help funcitions =================================================
def showNotification(title:str, context:str, icon_path:str, duration:str="short"):
    notification.notify(
        title=title,
        message=context,
        app_name="Phonotify",
        app_icon=str(icon_path),  
        timeout=2  # seconds
    )

# =============================== Notify Handle functions =================================================
@intercept_ble_call
async def notification_handler(sender: BleakGATTCharacteristic, data):
    global client
    icon_path = NOT_FOUND_ICON_PATH
    name = characteristics[sender.uuid]

    if(client is not None):
        title   = str(await client.read_gatt_char(TITLE_CHARACTERISTIC_UUID),'utf-8')
        context = str(await client.read_gatt_char(CONTEXT_CHARACTERISTIC_UUID),'utf-8')
        package = str(await client.read_gatt_char(PACKAGE_CHARACTERISTIC_UUID),'utf-8')
    
    try:
        res = app(package)
        icon = requests.get(res["icon"])

        with open(APP_ICON_PATH, "wb") as f:
            f.write(icon.content)
        icon_path = APP_ICON_PATH
    except Exception as e:
        log.info(f"{TAG}Icon err: {e}")
    
    showNotification(title, context, icon_path)
    log.info(f"{TAG}Notification from {name}: {package}")

@intercept_ble_call
async def disconnect_notify_callback(sender: BleakGATTCharacteristic, data): 
    global client
    
    log.info(f"{TAG}Sending disconect acknowledge message")
    await client.write_gatt_char(sender, bytearray("ACK",'utf-8'),response=False)
    
    await client.disconnect()

async def readChar(UUID: str) -> bytearray:
    global client

    characteristic_name = characteristics[UUID]
    value = await client.read_gatt_char(UUID)

    log.info(f"{TAG} Read {characteristic_name}: {str(value,'utf-8')}")
    
    return value
            
# =============================== Subscribing =================================================   
@intercept_ble_call
async def subscribing_to_notifications(client:BleakClient):
    
    log.info(f"{TAG}Subscribing for notifications:")
    try:
        # Subscription for notification
        name = characteristics[NOTIFY_COMPLETE_CHARACTERISTIC_UUID]
        await client.start_notify(NOTIFY_COMPLETE_CHARACTERISTIC_UUID, notification_handler)
        log.info(f"\t{name}: Notificiation enabled")
        
        # Subscription for disconnect characteristic
        name = characteristics[DISCONNECT_CHARACTERISTIC_UUID]
        await client.start_notify(DISCONNECT_CHARACTERISTIC_UUID, disconnect_notify_callback)
        log.info(f"\t{name}: Notificiation enabled")
        
    except Exception as e:
        log.info(f"{TAG}\tCouldn't subscribe to {name} {NOTIFY_COMPLETE_CHARACTERISTIC_UUID}: {e}")
    
    
    """
        for UUID in characteristics.keys():
            name = characteristics[UUID]
            try:
                await client.start_notify(UUID, notification_handler)
                print(f"  {name}: Notificiation enabled")
            except NameError:
                print(f"  Couldn't subscribe to {name} {UUID}: {NameError}")
        print("============================================\n")
        """
# =============================== Scan ================================================= 
@intercept_ble_call
async def scan() -> BLEDevice:  
    global scan_counter
    
    
    log.info(f" {TAG}Scanning for Service UUID: {NOTIFICATION_SERVICE_UUID}")
    
    # find_device_by_filter works on both OSs
    device = await BleakScanner.find_device_by_filter(
        lambda d, ad: NOTIFICATION_SERVICE_UUID in ad.service_uuids,
        timeout=10.0
    )
    
    if device:
        # On Windows, device.name might be None here, and that's okay!
        log.info(f" {TAG}Device found at {device.address}")
        return device
    return None
    
    device: BLEDevice = None    
    # Scan for devices
    devices = await BleakScanner(
        detection_callback=detection_callback,
        service_uuids=[NOTIFICATION_SERVICE_UUID]
    )
    #devices = await BleakScanner.discover(timeout=4)
    log.info(f"{scan_counter}: Scanning for name {PHONE_NAME}")
    for d in devices:
        if d.name != None :log.info(f"\t{d}")
        if d.name == PHONE_NAME: 
            device = d
            log.info(f"Found {PHONE_NAME}:{d.address}")
            break
    
    return device

@intercept_ble_call
async def printServices(client:BleakClient):
    
    log.info(f"{TAG}Printing Services and Characteristics")
    for s in client.services:
        log.info(f"Services {s}")
        for c in s.characteristics:
            log.info(f"\tCharacteristic {c}")

# =============================== Connection ================================================= 
@intercept_ble_call
def disconnected_callback(client: BleakClient): 
    global connected 
    
    connected = False
    log.warning(f"{TAG}Disconnected from {client.name}:{client.address}")
    showNotification("Disconnected ",f"Disconnected from {client.name}:{client.address}", CROSS_ICON_PATH)
    
# Connecting....
@intercept_ble_call
async def connect(client:BleakClient, device:BLEDevice) -> bool:
    address = device.address
    
    log.info(f"{TAG}Connecting... to {PHONE_NAME}:{address}")
    try:
        await client.connect()
    except Exception as e:
        log.info(f"{TAG}Connection Error {e}")
        return False
    log.info(f"{TAG}Connected: {address} : {client.is_connected}")

    showNotification("Connected ",f"connected to {PHONE_NAME}:{address}", CHECK_ICON_PATH)
    
    return True
# =============================== Health Check ==================================================================
async def health_check(client: BleakClient):
    global HEALTH_CHECK_INTERVAL
    try:
        await asyncio.wait_for( 
            client.write_gatt_char(
                HEALTH_CHECK_CHARACTERISTIC_UUID, 
                bytearray("ACK",'utf-8'),
                response=False
            ), 
            1
        )
        # ret =  await asyncio.wait_for(readChar(HEALTH_CHECK_CHARACTERISTIC_UUID), 1)
        log.info(f"{TAG}Health check: OK")
    except asyncio.TimeoutError:    
        log.info(f"{TAG}Health check: DOWN")
    except BleakError as e: 
        log.info(f"{TAG}Health check: ERROR ")
        disconnect()

async def periodic_task(client: BleakClient):
    loop = asyncio.get_running_loop()
    next_run = loop.time() # seconds
    
    try:
        while True:
            next_run += HEALTH_CHECK_INTERVAL
            await asyncio.sleep(max(0, next_run - loop.time()))
            await health_check(client)
    except asyncio.CancelledError:
        log.info(f"{TAG}Health check task stopped")

# =============================== Main Loop =================================================
@intercept_ble_call
async def main():

    global running
    global client
    global connected
    global scan_counter

    while running:

        # Start Scanning
        device = await scan()
        if device is None: 
            scan_counter += 1
            sleep_time = min(MAX_SCAN_SLEEP_TIME, 2*scan_counter)
            log.info(f"{TAG}Device not found. Sleeping for {sleep_time}s")
            await asyncio.sleep(sleep_time)
            continue
        scan_counter = 0
        
        #Connection
        client = BleakClient(device, disconnected_callback)
        connected = await connect(client, device)
        
        if connected: # When connected
            await printServices(client)
            await subscribing_to_notifications(client)
            
            health_task = asyncio.create_task(periodic_task(client))
            
            log.info(f"{TAG}Listening....")
            try: 
                while connected: 
                    await asyncio.sleep(1)
                if connected is False:
                    # Starting to disconnect
                    if client is not None:
                        log.warning(f"{TAG}client.disconnect()....")
                        await client.disconnect()
            finally:
                log.info(f"{TAG}canceling health check")
                health_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await health_task
    log.warning(f"{TAG}Stopped Running")

# =============================== Control functions ================================================= 
def run():
    asyncio.run(main())

def disconnect():
    global connected
    log.info(f"{TAG}Disconencting set the connected to false")
    connected = False

def end():
    global running 
    log.info(f"{TAG}Stopping the application set the running to false")
    running = False
    disconnect()
