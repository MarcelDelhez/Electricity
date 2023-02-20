import sys
import re
import crcmod.predefined
import binascii
from datetime import datetime

fh = open('C:/Users/AY52FW/OneDrive - ING/Documents/Perso/Maison/Electricité/Data/P1Telegram_param.txt', 'rb')
telegram = bytearray(fh.read())

#Retrieve data from MQTT
P_C3 = 5732
CptInD = 1
CptInN = 2
CptOutD = 3
CptOutN = 4

# Format message to Alfen EVE
contenu=telegram
encoded=f'{CptInD:010.3f}'.encode('ascii')
contenu = contenu.replace(b"#INDAY#", bytearray(encoded))
encoded=f'{CptInN:010.3f}'.encode('ascii')
contenu = contenu.replace(b"#INNIGHT#", bytearray(encoded))
encoded=f'{CptOutD:010.3f}'.encode('ascii')
contenu = contenu.replace(b"#OUTDAY#", bytearray(encoded))
encoded=f'{CptOutN:010.3f}'.encode('ascii')
contenu = contenu.replace(b"#OUTNIGHT#", bytearray(encoded))

encoded=datetime.now().strftime("%y%m%d%H%M%S").encode('ascii')
contenu = contenu.replace(b"#TIMESTAMP#", bytearray(encoded))
W = 22000 - P_C3
encoded=f'{W/1000:06.3f}'.encode('ascii')
contenu = contenu.replace(b"#POWER#", bytearray(encoded))
encoded=f'{W/3000:06.3f}'.encode('ascii')
contenu = contenu.replace(b"#Power#", bytearray(encoded))
encoded=f'{W/690:06.2f}'.encode('ascii')
contenu = contenu.replace(b"#AMPERES#", bytearray(encoded))

MonCRC=crcmod.predefined.mkPredefinedCrcFun('crc16')(contenu)
contenu.extend(hex(MonCRC).encode('ascii')[2:])
contenu.extend(b'\r\n')

# Message must be sent through serial connexion
#   but here, we show the message 
contenu