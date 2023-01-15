import paho.mqtt.client as mqtt
import requests
import pandas as pd
import json
import time
import mariadb
import sys
from datetime import date, datetime, timezone, timedelta
 
# ------------------------------------------------------------------
# -- Charge les données du compteur digital dans une database
# -- Les données (les 4 compteurs et les kWhs soutirés et injectés
# -- sont chargées toutes les 15 minutes depuis le serveur MQTT
# -- lequel est alimenté par le Lowi.
# -- Une DB mySQL nommée P1 doit préalablement exister.
# -- Pour récupérer la consommation par heure :
# --    select str_to_date(date_format(DtTm, '%Y-%m-%d %H:00:00'), '%Y-%m-%d %T') Dt, 
# --        round(sum(Soutire),3), round(sum(Injecte),3) 
# --        from Conso group by Dt;
# ------------------------------------------------------------------
 
MQTT_BROKER = "192.168.1.223"
MQTT_PORT = 1883
MQTT_TOPIC = "4c75252e8c51"
 
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to broker")
        global Connected                #Use global variable
        Connected = True                #Signal connection
    else:
        print("Connection failed")
 
def write_conso():
    # Calcul de ce qui a été soutiré et injecté sur le quart d'heure
    Soutire = Cptr_In_D + Cptr_In_N - O_Cptr_In_D - O_Cptr_In_N
    Injecte = Cptr_Out_D + Cptr_Out_N - O_Cptr_Out_D - O_Cptr_Out_N
 
    # Mémoriser le quart d'heure en DB
    if O_Cptr_In_D != 0:
        sql_isrt = f"INSERT INTO Conso (DtTm, In_D, In_N, Out_D, Out_N, Soutire, Injecte) VALUES (?, ?, ?, ?, ?, ?, ?);"
        cur.execute(sql_isrt, (O_DtTm, Cptr_In_D, Cptr_In_N, Cptr_Out_D, Cptr_Out_N, Soutire, Injecte))
        _mois = O_DtTm.date()-timedelta(days=O_DtTm.day-1)
        cur.execute("SELECT kW FROM Pics WHERE Mois = ?;", (_mois,))
        res = cur.fetchone()
        if res:
            kW = res[0]
            if kW < 4*Soutire:
                cur.execute ("UPDATE Pics set kW = ? WHERE Mois = ?;", (4*Soutire, _mois))
        else:
            cur.execute("INSERT INTO Pics (Mois, DtTm, kW) VALUES (?, ?, ?);", (_mois, o_DtTm, 4*Soutire))
        conn.commit()
 
def on_message(client, userdata, message):
    global DtTm, Power_In, Power_Out, Cptr_In_D, Cptr_In_N, Cptr_Out_D, Cptr_Out_N
    global O_DtTm, O_Cptr_In_D, O_Cptr_In_N, O_Cptr_Out_D, O_Cptr_Out_N
    global Soutire, Injecte, DtLuPxElectr
 
    DtTm = datetime.now(timezone.utc)
    # La fréquence des records est de 15 minutes.  Donc floor du timestamp sur cette periode de 15 min.
    DtTm = DtTm - timedelta(minutes=DtTm.minute % 15, seconds=DtTm.second, microseconds=DtTm.microsecond)
 
    if DtTm != O_DtTm:
        # Nouveau quart d'heure.
        msg_dict = json.loads(str(message.payload.decode("utf-8")))
        if message.topic == (MQTT_TOPIC + "/PUB/CH0") :
            # Parsing du message MQTT
            Power_In = float(msg_dict['PI'])
            Power_Out = float(msg_dict['PE'])
            Cptr_In_D = float(msg_dict['CIH'])/1000.
            Cptr_In_N = float(msg_dict['CIL'])/1000.
            Cptr_Out_D = float(msg_dict['CEH'])/1000.
            Cptr_Out_N = float(msg_dict['CEL'])/1000.
 
        write_conso()
        if DtTm.hour >= 16 and DtLuPxElectr < date.today():
            if majPxElectr() == True:
                DtLuPxElectr = date.today()
 
        O_DtTm = DtTm
        O_Cptr_In_D = Cptr_In_D
        O_Cptr_In_N = Cptr_In_N
        O_Cptr_Out_D = Cptr_Out_D
        O_Cptr_Out_N = Cptr_Out_N
 
def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)
 
def majPxElectr():
    # ----- -- Lire la dernière date pour laquelle on a des prix
    cur.execute("SELECT MAX(DtTm) FROM PxElectr;")
    Dt=cur.fetchall()[0][0]
    if  Dt is None :
        print("No date found.  Consider 1/1/2022.")
        Dt = date.fromisoformat('2021-12-31')
    else :
        Dt = Dt.date()
        print(Dt)
 
    start_date = Dt + timedelta(days=1)
    # -- Les prix pour le lendemain sont connus à 14h mais, je laisse du temps à Elia pour les publier
    if  datetime.now().hour >= 16 :
        end_date = date.today() + timedelta(days=2)
    else :
        end_date = date.today() + timedelta(days=1)

    for single_date in daterange(start_date, end_date):
        url=f"https://griddata.elia.be/eliabecontrols.prod/interface/Interconnections/daily/auctionresults/{single_date.strftime('%Y-%m-%d')}"
        rsp = requests.get(url)
        print (f"     Retrieving {single_date}.")
        if rsp.status_code == 200:
            cur.execute("SELECT BuyFormula, SellFormula FROM FormPxElectr WHERE FromDt = (SELECT MAX(FromDt) FROM FormPxElectr WHERE FromDt <= ?());", (single_date, ))
            res = fetchone()
            if res:
                _BuyFormula = res[0]
                _SellFormula = res[1]
            else:
                cur.execute("INSERT IGNORE INTO FormPxElectr (FromDt, BuyFormula, SellFormula) VALUES('2020-01-01', 'price / 10 + 0.204', 'price / 10');"
                _BuyFormula = 'price / 10 + 0.204'
                _SellFormula = 'price / 10'
                conn.commit()
            df = pd.DataFrame.from_dict(rsp.json())
            df = df.loc[df['isVisible'] == True]
            df['dateTime'] = pd.to_datetime(df['dateTime'], format="%Y-%m-%dT%H:%M:%S")
            df['Buy'] = eval(_BuyFormula.replace("price", "df['price']"))
            df['Sell']= eval(_SellFormula.replace("price", "df['price']"))
            df.rename(columns = {'dateTime':'DtTm'}, inplace = True)
            sql_isrt = "INSERT INTO PxElectr (DtTm, price, Buy, Sell) VALUES (?, ?, ?, ?);"
            for index, r in df.iterrows():
                cur.execute(sql_isrt, (r['DtTm'].strftime('%Y-%m-%d %H:%M:%S'), r['price'], r['Buy'], r['Sell']))
            conn.commit()
            rc = True 
        else:
            rc = False
            break
 
# ----- ----- -----

# -----
# -- Se connecter au serveur MQTT
Connected = False
client = mqtt.Client("Conso")
client.username_pw_set("pi", "your_password")
client.on_connect = on_connect
client.on_message=on_message
client.connect(MQTT_BROKER, MQTT_PORT)

# -----
# -- Se connecter à la database
try:
    conn = mariadb.connect(user="pi", password="your_password", host="localhost", port=3306, database="P1")
except mariadb.Error as e:
    print(f"Error connecting to MariaDB : {e}")
    sys.exit(1)
# -- Ouvrir un curseur
cur = conn.cursor()
# -- Créer les tables si elles n'existent pas déjà
cur.execute("CREATE TABLE IF NOT EXISTS Conso (DtTm DATETIME PRIMARY KEY, In_D FLOAT, In_N FLOAT, OUT_D FLOAT, OUT_N FLOAT, Soutire FLOAT, Injecte FLOAT)")
cur.execute("CREATE TABLE IF NOT EXISTS PxElectr (DtTm DATETIME PRIMARY KEY, price FLOAT, Buy FLOAT, Sell FLOAT)")
cur.execute("CREATE TABLE IF NOT EXISTS Pics (Mois DATE PRIMARY KEY, DtTm DATETIME, kW FLOAT)")
cur.execute("CREATE TABLE IF NOT EXISTS FormPxElectr (FromDt DATE PRIMARY KEY, BuyFormula char(50), SellFormula char(50))")
cur.execute("INSERT IGNORE INTO FormPxElectr (FromDt, BuyFormula, SellFormula) VALUES('2020-01-01', 'price / 10 + 0.204', 'price / 10');"
conn.commit()

# -----
# -- Init variables
DtTm = datetime.now(timezone.utc)
DtTm = DtTm - timedelta(minutes=DtTm.minute % 30, seconds=DtTm.second, microseconds=DtTm.microsecond)
O_DtTm = DtTm
Power_In = 0.
Power_Out = 0.
Cptr_In_D = 0.
Cptr_In_N = 0.
Cptr_Out_D = 0.
Cptr_Out_N = 0.
O_Cptr_In_D = 0.
O_Cptr_In_N = 0.
O_Cptr_Out_D = 0.
O_Cptr_Out_N = 0.
DtLuPxElectr = date.today() - timedelta(days=1)
 
Soutire = Cptr_In_D + Cptr_In_N - O_Cptr_In_D - O_Cptr_In_N
Injecte = Cptr_Out_D + Cptr_Out_N - O_Cptr_Out_D - O_Cptr_Out_N
 
client.loop_start()
while  Connected != True:
    time.sleep(1)
 
client.subscribe([(MQTT_TOPIC + "/PUB/CH0",0)])
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Exiting !")
    DtTm = datetime.now(timezone.utc)
    DtTm = DtTm - timedelta(microseconds=DtTm.microsecond)
    write_conso()
    cur.close()
    conn.close()
    client.disconnect()
    client.loop_stop()
