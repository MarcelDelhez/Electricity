import cvxpy as cp
import numpy as np
import pandas as pd
import mariadb
import sys
from datetime import date, datetime, timezone, timedelta
from math import floor

# --- arguments : Target PicMois
if len(sys.argv) < 2:
    Target = 22
else:
    Target = float(sys.argv[1])
#PicMois = float(sys.argv[2])
#Target = 39
#PicMois = 3.15

HrCharge = datetime.strptime("2022-08-29 10:17:16", "%Y-%m-%d %H:%M:%S")
HrDepart = datetime.strptime("2022-08-30 09:38:22", "%Y-%m-%d %H:%M:%S")
print(f" ---- Heure de branchement de la voiture : {HrCharge}")
print(f"      Heure prévue pour le départ        : {HrDepart}")
print(f"      Energie nécessaire                 : {Target} kWh")

HrCharge = HrCharge.replace(microsecond=0, second=0, minute=0) + timedelta(hours=1)
HrDepart = HrDepart.replace(microsecond=0, second=0, minute=0)
print(f"-- Début de charge {HrCharge}   -   Fin de charge {HrDepart}")
Heures = floor((HrDepart - HrCharge).seconds/3600)
print(f"   Heures de charge : {Heures}")

# --- Récupérer le prix de l'éléctricité, consommation et pic
conn = mariadb.connect(user="pi", password="aaa", host="localhost", port=3306, database="P1")
cur=conn.cursor()
UTC_OFFSET = pd.Timedelta(datetime.utcnow() - datetime.now()).round(freq='s')
HrChargeUTC = HrCharge + UTC_OFFSET
cur.execute("SELECT DtTm, Buy FROM PxElectr WHERE DtTm>= ? order by DtTm LIMIT 60;", (HrChargeUTC,))
dfPrix = pd.DataFrame(cur.fetchall(), columns = ['DtTm', 'Buy'])
#Prix = aujourdhui['Buy'].to_numpy()
if cur.rowcount < Heures:
	cur.execute("SELECT DATE_ADD(DtTm, INTERVAL 7 DAY), Buy FROM PxElectr WHERE DtTm>DATE_SUB(?, INTERVAL 7 DAY) order by DtTm LIMIT 60;", (dfPrix['DtTm'].iloc[-1].to_pydatetime(),))
	dfPrix = pd.concat([dfPrix, pd.DataFrame(cur.fetchall(), columns = ['DtTm', 'Buy'])], axis=0)

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
dfOptim = pd.merge(dfPrix, dfConso, on='Hr').sort_values(by=['DtTm'], ascending=True).iloc[:Heures]
dfOptim['Dispo'] = 11

# --- Optimisation de la charge
kW = cp.Variable(Heures)
constraints = [cp.sum(kW) >= Target, kW >= 0.1, kW <= dfOptim['Dispo']]
objective = cp.Minimize(cp.sum(cp.multiply(kW, dfOptim['Buy'])) + (cp.maximum(cp.max(kW + dfOptim['Conso']), PicMois) - PicMois)*400)
problem = cp.Problem(objective, constraints)
problem.solve()

if problem.status == 'optimal':
	print(f" --- Coût = {(problem.value/100).round(2):4.2f} €")
	dfOptim['kW']=kW.value
	print(dfOptim)
else:
	print(problem.status)
