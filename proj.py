from machine import Pin, I2C, UART
import time
import _thread
from ssd1306 import SSD1306_I2C
import math

# ==============================
# CONSTANTS
# ==============================
earthRadius = 6371000

# ==============================
# OLED SETUP
# ==============================
i2c2 = I2C(1, sda=Pin(2), scl=Pin(3), freq=400000)
dsp = SSD1306_I2C(128, 64, i2c2)

# ==============================
# STATES
# ==============================
sysState = 0
screenState = 0

# ==============================
# THREAD + UART
# ==============================
dataLock = _thread.allocate_lock()

GPS = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))

GPS.write(b"$PMTK314,0,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0*28\r\n")

NMEAdata = {'GNGGA': "", 'GNRMC': ""}
NMEAmain = {'GNGGA': "", 'GNRMC': ""}

GPSdata = {
'latDD':0,
'lonDD':0,
'heading':0,
'fix':False,
'alt':0,
'sats':0,
'knots':0
}

latitude1=0
longitude1=0
latitude2=0
longitude2=0

distance=0
heading12=0

# ==============================
# HAVERSINE
# ==============================

def calculateDistance(lat1,lon1,lat2,lon2):

lat1=math.radians(lat1)
lon1=math.radians(lon1)
lat2=math.radians(lat2)
lon2=math.radians(lon2)

theta = 2*math.asin(math.sqrt(
math.sin((lat2-lat1)/2)**2+
math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2))

return earthRadius*theta

def calculateHeading(lat1,lon1,lat2,lon2):

lat1=math.radians(lat1)
lon1=math.radians(lon1)
lat2=math.radians(lat2)
lon2=math.radians(lon2)

deltaLon=lon2-lon1

x=math.sin(deltaLon)*math.cos(lat2)

y=(math.cos(lat1)*math.sin(lat2)-
math.sin(lat1)*math.cos(lat2)*math.cos(deltaLon))

return math.degrees(math.atan2(x,y))

# ==============================
# GPS THREAD
# ==============================

def gpsThread():

global NMEAdata

buffer=""

while True:

if GPS.any():

char = GPS.read(1).decode()
buffer += char

if char == '\n':

line = buffer.strip()

if line.startswith("$GNGGA"):
GNGGA = line

if line.startswith("$GNRMC"):
GNRMC = line

dataLock.acquire()
NMEAdata={'GNGGA':GNGGA,'GNRMC':GNRMC}
dataLock.release()

buffer=""

# ==============================
# PARSE GPS
# ==============================

def parseGPS():

global GPSdata

try:

readFix=int(NMEAmain['GNGGA'].split(',')[6])

if readFix==0:
GPSdata['fix']=False
return

GPSdata['fix']=True

latRAW=NMEAmain['GNGGA'].split(',')[2]
latDD=int(latRAW[0:2])+float(latRAW[2:])/60

if NMEAmain['GNGGA'].split(',')[3]=='S':
latDD=-latDD

GPSdata['latDD']=latDD

lonRAW=NMEAmain['GNGGA'].split(',')[4]
lonDD=int(lonRAW[0:3])+float(lonRAW[3:])/60

if NMEAmain['GNGGA'].split(',')[5]=='W':
lonDD=-lonDD

GPSdata['lonDD']=lonDD

GPSdata['heading']=float(NMEAmain['GNRMC'].split(',')[8])
GPSdata['knots']=float(NMEAmain['GNRMC'].split(',')[7])
GPSdata['sats']=int(NMEAmain['GNGGA'].split(',')[7])
GPSdata['alt']=float(NMEAmain['GNGGA'].split(',')[9])

except:
GPSdata['fix']=False

# ==============================
# DISPLAY
# ==============================

def dispOLED():

dsp.fill(0)

if not GPSdata['fix']:

dsp.text("Waiting Fix",0,0)

else:

if screenState==0:

dsp.text("LIVE GPS",0,0)
dsp.text("LAT:"+str(round(GPSdata['latDD'],6)),0,15)
dsp.text("LON:"+str(round(GPSdata['lonDD'],6)),0,25)
dsp.text("SATS:"+str(GPSdata['sats']),0,40)
dsp.text("SPD:"+str(round(GPSdata['knots'],1)),0,50)

else:

dsp.text("MEASURE",0,0)

if sysState==0:
dsp.text("Press Btn1 P1",0,20)

elif sysState==1:
dsp.text("P1 Stored",0,20)
dsp.text("Go P2",0,30)

elif sysState==2:
dsp.text("Dist:"+str(round(distance,2))+"m",0,20)
dsp.text("Head:"+str(round(heading12,2)),0,30)

dsp.text("Alt:"+str(round(GPSdata['alt'],1)),0,50)

dsp.show()

# ==============================
# BUTTONS
# ==============================

butMeasure = Pin(12,Pin.IN,Pin.PULL_UP)
butScreen = Pin(13,Pin.IN,Pin.PULL_UP)

def measureIRQ(pin):

global sysState,latitude1,longitude1,latitude2,longitude2,distance,heading12

time.sleep_ms(200)

if sysState==0 and GPSdata['fix']:

latitude1=GPSdata['latDD']
longitude1=GPSdata['lonDD']
sysState=1

elif sysState==1 and GPSdata['fix']:

latitude2=GPSdata['latDD']
longitude2=GPSdata['lonDD']

distance=calculateDistance(latitude1,longitude1,latitude2,longitude2)
heading12=calculateHeading(latitude1,longitude1,latitude2,longitude2)

sysState=2

elif sysState==2:

sysState=0

def screenIRQ(pin):

global screenState
time.sleep_ms(200)
screenState=1-screenState

butMeasure.irq(trigger=Pin.IRQ_FALLING,handler=measureIRQ)
butScreen.irq(trigger=Pin.IRQ_FALLING,handler=screenIRQ)

# ==============================
# START THREAD
# ==============================

_thread.start_new_thread(gpsThread,())

time.sleep(3)

# ==============================
# MAIN LOOP
# ==============================

while True:

dataLock.acquire()
NMEAmain=NMEAdata.copy()
dataLock.release()

if NMEAmain['GNGGA']!="":
parseGPS()

dispOLED()

time.sleep(1)