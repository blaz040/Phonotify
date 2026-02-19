import asyncio
from bleak import BleakClient, BleakScanner, BleakGATTCharacteristic, BLEDevice
from bleak.exc import BleakError
import contextlib
from plyer import notification
import requests
from google_play_scraper import app
from logAPI import init_log
from pathlib import Path
from pystray import Icon
from PIL import Image
import functools
import time

# =============================== Main variables ================================================= 
NOTIFICATION_NAME = "Notification from Phone"
# deprecated
PHONE_NAME = "phServer"

running = True  
connected = True 
client:BleakClient = None 
scan_counter = 0

 
HEALTH_CHECK_INTERVAL = 15 # seconds 
SCAN_DURATION = 3 #seconds
MAX_SCAN_SLEEP_TIME = 5 * 60
start_scan_signal = asyncio.Event()

TAG = "BLE THREAD"
log = init_log(tag=TAG)

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
# Service
NOTIFICATION_SERVICE_UUID               = "91d76000-ac7b-4d70-ab3a-8b87a357239e"

# Characteristics
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
#======================================== Status Callback function ====================================================================
connection_callback = lambda: None

disconnect_callback = lambda : None

scanning_callback = lambda scanning: None
#======================================= Intercptor ==========================================================
def intercept_ble_call(func):
    MAX_LOG_TEXT_SIZE = 70

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
       
        text = f"=== Running {func.__name__} "
        log.info(f"{text:=<{MAX_LOG_TEXT_SIZE}}")
        start_time = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            log.info(f"Intercepted error in {func.__name__}: {e}")
            raise
        finally:
            end_time = time.perf_counter()

            text = f"=== Finished {func.__name__} in {end_time - start_time:.4f}s "
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
        log.info(f"Icon err: {e}")
    
    showNotification(title, context, icon_path)
    log.info(f"Notification from {name}: {package}")

@intercept_ble_call
async def disconnect_notify_callback(sender: BleakGATTCharacteristic, data): 
    global client
    
    #log.info(f"Sending disconect acknowledge message")
    #await client.write_gatt_char(sender, bytearray("ACK",'utf-8'),response=False)
    
    await client.disconnect()

async def readChar(UUID: str) -> bytearray:
    global client

    characteristic_name = characteristics[UUID]
    value = await client.read_gatt_char(UUID)

    log.info(f" Read {characteristic_name}: {str(value,'utf-8')}")
    
    return value
            
# =============================== Subscribing =================================================   
@intercept_ble_call
async def subscribing_to_notifications(client:BleakClient):
    
    log.info(f"Subscribing for notifications:")
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
        log.info(f"\tCouldn't subscribe to {name} {NOTIFY_COMPLETE_CHARACTERISTIC_UUID}: {e}")
    
    
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
    
    log.info(f"\t{scan_counter}: Scanning for Service UUID: {NOTIFICATION_SERVICE_UUID}")
    scanning_callback(scanning=True)
    # find_device_by_filter works on both OSs
    device = await BleakScanner.find_device_by_filter(
        lambda d, ad: NOTIFICATION_SERVICE_UUID in ad.service_uuids,
        timeout=SCAN_DURATION
    )
    
    if device:
        # On Windows, device.name might be None here, and that's okay!
        log.info(f"\tDevice found at {device.address}")
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
    
    log.info(f"Printing Services and Characteristics")
    for s in client.services:
        log.info(f"Services {s}")
        for c in s.characteristics:
            log.info(f"\tCharacteristic {c}")

# =============================== Connection ================================================= 
@intercept_ble_call
def disconnected_callback(client: BleakClient): 
    global connected 
    
    connected = False
    log.warning(f"Disconnected from {client.name}:{client.address}")
    disconnect_callback()
    showNotification("Disconnected ",f"Disconnected from {client.name}:{client.address}", CROSS_ICON_PATH)
    
@intercept_ble_call
async def connect(client:BleakClient, device:BLEDevice) -> bool:
    address = device.address
    
    log.info(f"Connecting... to {PHONE_NAME}:{address}")
    try:
        await client.connect()
    except Exception as e:
        log.info(f"Connection Error {e}")
        return False
    log.info(f"Connected: {address} : {client.is_connected}")

    connection_callback()
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
        log.info(f"Health check: OK")
    except asyncio.TimeoutError:    
        log.info(f"Health check: DOWN")
    except BleakError as e: 
        log.info(f"Health check: ERROR ")
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
        log.info(f"Health check task stopped")

# ========================= Smart sleep ====================================================
async def smart_sleep(name, sleep_time, wakeup_event):
    scanning_callback(scanning=False)
    log.info(f"[{name}] Going to sleep for {sleep_time}s...")
    try:
        # Wait for the event to be set, or timeout after sleep_time
        await asyncio.wait_for(wakeup_event.wait(), timeout=sleep_time)
        log.info(f"[{name}] Woke up early on command!")
    except asyncio.TimeoutError:
        log.info(f"[{name}] Slept the full duration.")
    finally:
        wakeup_event.clear() # Reset for next time if needed

# =============================== Main Loop =================================================
@intercept_ble_call
async def main():

    global running
    global client
    global connected
    global scan_counter
    global start_scan_signal

    while running:
        # Start Scanning
        device = await scan()
        if device is None: 
            scan_counter += 1
            sleep_time = min(MAX_SCAN_SLEEP_TIME, 2*scan_counter)
            await smart_sleep("Scan sleep", sleep_time, start_scan_signal)
            continue
        scan_counter = 0
        
        #Connection
        client = BleakClient(device, disconnected_callback)
        connected = await connect(client, device)
        
        if connected: # When connected
            await printServices(client)
            await subscribing_to_notifications(client)
            
            health_task = asyncio.create_task(periodic_task(client))
            
            log.info(f"Listening....")
            try: 
                while connected: 
                    await asyncio.sleep(1)
                if connected is False:
                    # Starting to disconnect
                    if client is not None:
                        log.warning(f"client.disconnect()....")
                        await client.disconnect()
            finally:
                log.info(f"canceling health check")
                health_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await health_task
    log.warning(f"Stopped Running")

# =============================== Control functions ================================================= 
def run():
    asyncio.run(main())

def disconnect():
    global connected
    log.info(f"Disconencting set the connected to false")
    connected = False

def start_scan():
    global start_scan_signal
    log.info("Starting to Scan early if it is sleeping")
    start_scan_signal.set()

def end():
    global running 
    log.info(f"Stopping the application set the running to false")
    running = False
    disconnect()

