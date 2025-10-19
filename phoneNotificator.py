import asyncio
from bleak import BleakClient, BleakScanner, BleakGATTCharacteristic, BLEDevice
from winotify import Notification
import requests
from google_play_scraper import app
import logging as log

Notification_Name = "Notification from Phone"

AppIconFoundPath = "C:\\Users\\Blaz\\Documents\\faks\\Phonotify\\icons\\recentApp_icon.png"
AppIconNotFoundPath = "C:\\Users\\Blaz\\Documents\\faks\\Phonotify\\icons\\NotFound_icon.png"
notificationServiceUUID = "91d76000-ac7b-4d70-ab3a-8b87a357239e"

titleCharacteristicUUID = "91d76001-ac7b-4d70-ab3a-8b87a357239e"
contextCharacteristicUUID = "91d76002-ac7b-4d70-ab3a-8b87a357239e"
packageCharacteristicUUID = "91d76003-ac7b-4d70-ab3a-8b87a357239e"

notifyCompleteCharacteristicUUID = "91d76004-ac7b-4d70-ab3a-8b87a357239e"
disconnectCharacteristicUUID = "91d76005-ac7b-4d70-ab3a-8b87a357239e"

characteristics = {
    titleCharacteristicUUID: "title",
    contextCharacteristicUUID: "context",
    packageCharacteristicUUID: "package",
    notifyCompleteCharacteristicUUID: "Notifier",
    disconnectCharacteristicUUID: "disconnect"
}

log.basicConfig(
    filename="myLogs.log",
    level=log.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

phone_name = "Redmi"   
connected = True

client:BleakClient = None

def reconnect():
    global client
    if client != None:
        asyncio.run(client.disconnect())
    
async def main():   
    async def notification_handler(sender: BleakGATTCharacteristic, data):
        global client
        icon_path = AppIconNotFoundPath
        name = characteristics[sender.uuid]
        if(client is not None):
            title = str(await client.read_gatt_char(titleCharacteristicUUID),'utf-8')
            context = str(await client.read_gatt_char(contextCharacteristicUUID),'utf-8')
            package = str(await client.read_gatt_char(packageCharacteristicUUID),'utf-8')
        
        try:
            res = app(package)
            #print(res["icon"])
            icon = requests.get(res["icon"])
            with open(AppIconFoundPath, "wb") as f:
                f.write(icon.content)
            log.info(f"{icon.status_code} {icon.encoding}")
            #print(icon)
            icon_path = AppIconFoundPath
        except Exception as e:
            log.error(f"Icon err: {e}")
        toast = Notification(app_id = Notification_Name,
                            title = title,
                            msg = context,
                            icon = icon_path,
                            duration = "short")
        toast.show()
        log.info(f"Notification from {name}: {package}")
        
    async def disconnect_request_callback(sender: BleakGATTCharacteristic, data): 
        global client
        await client.disconnect()
        
    async def scan()->BLEDevice:  
        log.info("\n============================================\n")
        device:BLEDevice = None    
        # Scan for devices
        i = 1
        while device == None:
            log.info(f"{i}: Scanning for name {phone_name}")
            devices = await BleakScanner.discover(timeout=4)
            for d in devices:
                if d.name != None :log.info(f"  {d}")
                if d.name == phone_name: 
                    device = d
                    log.info(f"Found {phone_name}:{d.address}")
                    return d
            i+=1
        return device
    
    def disconnected_callback(client: BleakClient): 
        log.info("\n============================================\n")
        global connected 
        connected = False
        log.warning(f"Disconnected from {client.name}:{client.address}")
        log.info("\n============================================\n")
    
    async def printServices(client:BleakClient):
        log.info("\n============================================\n")
            
        log.info(f"Printing Services and Characteristics")
        for s in client.services:
            log.info(f"Services {s}")
            for c in s.characteristics:
                log.info(f"     Characteristic {c}")
        
        log.info("\n============================================\n")
        
    async def subscribing_to_notifications(client:BleakClient):
        log.info("Subscribing for notifications:")
            
        try:
            name = characteristics[notifyCompleteCharacteristicUUID]
            await client.start_notify(notifyCompleteCharacteristicUUID, notification_handler)
            log.info(f"  {name}: Notificiation enabled")
            name = characteristics[disconnectCharacteristicUUID]
            await client.start_notify(disconnectCharacteristicUUID,disconnect_request_callback)
            log.info(f"  {name}: Notificiation enabled")
            
        except Exception as e:
            log.error(f"  Couldn't subscribe to {name} {notifyCompleteCharacteristicUUID}: {e}")
        """
            for UUID in characteristics.keys():
                name = characteristics[UUID]
                try:
                    await client.start_notify(UUID, notification_handler)
                    print(f"  {name}: Notificiation enabled")
                except NameError:
                    print(f"  Couldn't subscribe to {name} {UUID}: {NameError}")
            print("\n============================================\n")
            """
    async def readChar(UUID: str)->bytearray:
        titleCharacteristicUUID = UUID
        # Read a characteristic (example UUID)
        log.info(f"Reading from {titleCharacteristicUUID}")
        value = await client.read_gatt_char(titleCharacteristicUUID)
        log.info(f"Read value: {str(value,'utf-8')}")
        
        log.info("\n============================================\n")
        
        return value
             
    # Connecting....
    async def connect(client:BleakClient, device:BLEDevice)->bool:
        address = device.address
        log.info("\n============================================\n")
        #print(f"Found {phone_name}:{address}")
        log.info(f"Connecting... to {phone_name}:{address}")
        try:
            await client.connect()
        except Exception as e:
            log.error(f"Connection Error {e}")
            return False
        log.info(f"Connected: {address} : {client.is_connected}")
        return True
    
    
    while True:
        global client
        global connected
        device = await scan()
        client = BleakClient(device,disconnected_callback)
        
        connected = await connect(client,device)
        if connected :
            await printServices(client)
            await subscribing_to_notifications(client)
        
            log.info("Listening....")
                
            while connected: 
                    await asyncio.sleep(1)
            
def run():     
    asyncio.run(main())
