import asyncio
from bleak import BleakClient, BleakScanner, BleakGATTCharacteristic, BLEDevice
from winotify import Notification
import requests
from google_play_scraper import app
import logging

Notification_Name = "Notification from Phone"

AppIconFoundPath = "C:\\Users\\Blaz\\Documents\\faks\\Phonotify\\icons\\recentApp_icon.png"
AppIconNotFoundPath = "C:\\Users\\Blaz\\Documents\\faks\\Phonotify\\icons\\NotFound_icon.png"
notificationServiceUUID = "91d76000-ac7b-4d70-ab3a-8b87a357239e"

titleCharacteristicUUID = "91d76001-ac7b-4d70-ab3a-8b87a357239e"
contextCharacteristicUUID = "91d76002-ac7b-4d70-ab3a-8b87a357239e"
packageCharacteristicUUID = "91d76003-ac7b-4d70-ab3a-8b87a357239e"

notifyCompleteCharacteristicUUID = "91d76004-ac7b-4d70-ab3a-8b87a357239e"

characteristics = {
    titleCharacteristicUUID: "title",
    contextCharacteristicUUID: "context",
    packageCharacteristicUUID: "package",
    notifyCompleteCharacteristicUUID: "Notifier"
}

logging.basicConfig(
    filename="myLogs.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
    )
phone_name = "Redmi"   
connected = True
    
def reconnect():
    global connected
    connected = False
    
async def main():   
    async def notification_handler(sender: BleakGATTCharacteristic, data):
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
            logging.info(f"{icon.status_code} {icon.encoding}")
            #print(icon)
            icon_path = AppIconFoundPath
        except Exception as e:
            logging.error(f"Icon err: {e}")
        toast = Notification(app_id = Notification_Name,
                            title = title,
                            msg = context,
                            icon = icon_path,
                            duration = "short")
        toast.show()
        logging.info(f"Notification from {name}: {package}")
    
    async def scan()->BLEDevice:  
        logging.info("\n============================================\n")
        device:BLEDevice = None    
        # Scan for devices
        i = 1
        while device == None:
            logging.info(f"{i}: Scanning for name {phone_name}")
            devices = await BleakScanner.discover(timeout=4)
            for d in devices:
                if d.name != None :logging.info(f"  {d}")
                if d.name == phone_name: 
                    device = d
                    logging.info(f"Found {phone_name}:{d.address}")
                    return d
                    break
            i+=1
        return device
    
    def disconnected_callback(client: BleakClient): 
        logging.info("\n============================================\n")
        global connected 
        connected = False
        logging.warning(f"Disconnected from {client.name}:{client.address}")
        logging.info("\n============================================\n")
    
    async def printServices(client:BleakClient):
        logging.info("\n============================================\n")
            
        logging.info(f"Printing Services and Characteristics")
        for s in client.services:
            logging.info(f"Services {s}")
            for c in s.characteristics:
                logging.info(f"     Characteristic {c}")
        
        logging.info("\n============================================\n")
        
    async def subscribing_to_notifications(client:BleakClient):
        logging.info("Subscribing for notifications:")
            
        try:
            name = characteristics[notifyCompleteCharacteristicUUID]
            await client.start_notify(notifyCompleteCharacteristicUUID, notification_handler)
            logging.info(f"  {name}: Notificiation enabled")
        except Exception as e:
            logging.error(f"  Couldn't subscribe to {name} {notifyCompleteCharacteristicUUID}: {e}")
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
        logging.info(f"Reading from {titleCharacteristicUUID}")
        value = await client.read_gatt_char(titleCharacteristicUUID)
        logging.info(f"Read value: {str(value,'utf-8')}")
        
        logging.info("\n============================================\n")
        
        return value
             
    # Connecting....
    async def connect(client:BleakClient, device:BLEDevice)->bool:
        address = device.address
        logging.info("\n============================================\n")
        #print(f"Found {phone_name}:{address}")
        logging.info(f"Connecting... to {phone_name}:{address}")
        try:
            await client.connect()
        except Exception as e:
            logging.error(f"Connection Error {e}")
            return False
        logging.info(f"Connected: {address} : {client.is_connected}")
        return True
    
    
    while True:
        global connected
        device = await scan()
        client = BleakClient(device,disconnected_callback)
        
        connected = await connect(client,device)
        if connected :
            await printServices(client)
            await subscribing_to_notifications(client)
        
            logging.info("Listening....")
            while connected: 
                await asyncio.sleep(1)
        #await asyncio.sleep(999)
    
    #await connect(device)
    
            
def run():     
    asyncio.run(main())