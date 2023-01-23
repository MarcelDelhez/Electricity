import cvxpy as cp
import numpy as np
import pandas as pd
import mariadb
import sys
from datetime import date, datetime, timezone, timedelta
from math import floor

# --- arguments : Target  Date
if len(sys.argv) < 2:
    Target = 22
else:
    Target = float(sys.argv[1])
if len(sys.argv) == 3:
	HrDepart = datetime.strptime(sys.argv[2]+" 08:10:00", "%Y-%m-%d %H:%M:%S")
else:
	HrDepart = datetime.strptime("2022-08-30 08:10:00", "%Y-%m-%d %H:%M:%S")

HrCharge = (HrDepart - timedelta(days=1)).replace(hour=12, minute=50)
if Target > 40:
	HrCharge = HrCharge - timedelta(hours=10)

print(f" ---- Heure de branchement de la voiture : {HrCharge}")
print(f"      Heure prévue pour le départ        : {HrDepart}")
print(f"      Energie nécessaire                 : {Target} kWh")

HrCharge = HrCharge.replace(microsecond=0, second=0, minute=0) + timedelta(hours=1)
HrDepart = HrDepart.replace(microsecond=0, second=0, minute=0)
print(f"-- Début de charge {HrCharge}   -   Fin de charge {HrDepart}")
Heures = int(divmod((HrDepart-HrCharge).total_seconds(),3600)[0])
print(f"   Heures de charge : {Heures}")

# --- Récupérer le prix de l'éléctricité, consommation et pic
conn = mariadb.connect(user="pi", password="aaa", host="localhost", port=3306, database="P1")
cur=conn.cursor()
UTC_OFFSET = pd.Timedelta(datetime.utcnow() - datetime.now()).round(freq='s')
HrChargeUTC = HrCharge + UTC_OFFSET
cur.execute("SELECT DtTm, Buy, Sell FROM PxElectr WHERE DtTm>= ? order by DtTm LIMIT 60;", (HrChargeUTC,))
dfPrix = pd.DataFrame(cur.fetchall(), columns = ['DtTm', 'Buy', 'Sell'])
if cur.rowcount < Heures:
	cur.execute("SELECT DATE_ADD(DtTm, INTERVAL 7 DAY), Buy, Sell FROM PxElectr WHERE DtTm>DATE_SUB(?, INTERVAL 7 DAY) order by DtTm LIMIT 60;", (dfPrix['DtTm'].iloc[-1].to_pydatetime(),))
	dfPrix = pd.concat([dfPrix, pd.DataFrame(cur.fetchall(), columns = ['DtTm', 'Buy', 'Sell'])], axis=0)

# Lire la conso par heure
cur.execute("SELECT hour(DtTm), max(I) FROM v_ConsoHr group by hour(DtTm);")
dfConso = pd.DataFrame(cur.fetchall(), columns=['Hr', 'Conso'])

# Lire le pic de consommation
cur.execute("SELECT 4*max(Soutire) FROM Conso;")
PicMois = cur.fetchone()[0]
print(f"Pic de consommation : {PicMois:.1f}")
cur.close()
conn.close()
# ---

dfPrix['Hr'] = dfPrix['DtTm'].dt.hour
dfOptim = dfPrix.merge(dfConso, on='Hr').sort_values(by=['DtTm'], ascending=True).iloc[:Heures]
dfOptim['Dispo'] = 11

# Récupérer le disponible solaire (ce qui sera injecté sur le réseau)
dfSolar = pd.DataFrame([[11, 0.8], [12, 1.7], [13, 1.5], [14, 1.3], [15, 0.9], [16, 0.4], [17, 0.2]], columns=['Hr', 'DispoS']) 
dfOptim = dfOptim.merge(dfSolar, on='Hr', how='left').fillna(0)
#dfOptim['DispoS'] = 0

# --- Optimisation de la charge
kW = cp.Variable(Heures)
kWS = cp.Variable(Heures)
constraints = [(cp.sum(kW) + cp.sum(kWS)) >= Target, kW >= 0.1, kWS >= 0, kW <= dfOptim['Dispo'], kWS <= dfOptim['DispoS']]
objective = cp.Minimize(cp.sum(cp.multiply(kW, dfOptim['Buy'])) + cp.sum(cp.multiply(kWS, dfOptim['Sell'])) + (cp.maximum(cp.max(kW + dfOptim['Conso']), PicMois) - PicMois)*350)
problem = cp.Problem(objective, constraints)
problem.solve()

if problem.status == 'optimal':
	print(f" --- Coût = {(problem.value/100).round(2):4.2f} €")
	dfOptim['kW'] = kW.value.round(decimals=2)
	dfOptim['kWS'] = kWS.value.round(decimals=2)
	print(dfOptim)
else:
	print(problem.status)
