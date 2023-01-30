import logging
from functools import wraps
import time
from time import sleep, mktime
from typing import Dict

import pandas as pd
from datetime import datetime, date, timedelta
import requests

class HTTPError(Exception):
    pass

class HTTPError407(HTTPError):
    pass

class HTTPError305(HTTPError):
    pass

class HTTPError306(HTTPError):
    pass

class HTTPError307(HTTPError):
    pass

class HTTPError401(HTTPError):
    pass

def authenticated(func):
    """
    Decorator to check if token has expired.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        self = args[0]
        if self.token_expiration_time <= pd.Timestamp.utcnow().timestamp():
            self.login()
        return func(*args, **kwargs)

    return wrapper


def throttle_retry(func):
    """
    Decorator to retry when throttleError is received.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        self = args[0]
        try:
            return func(*args, **kwargs)
        except HTTPError407 as e:
            for i in range(1, self.max_retry + 1):
                delay = i * 3
                logging.debug(f'Sleeping {delay} seconds')
                sleep(delay)
                try:
                    return func(*args, **kwargs)
                except HTTPError407:
                    pass
            else:
                raise e
        except (HTTPError305, HTTPError306, HTTPError307) as e:
            # Token as expired or we aren't logged in.. Refresh it.
            logging.debug("Got login error. Logging back in and retrying")
            self.login()
            return func(*args, **kwargs)

    return wrapper

 
class FusionSolar:
    def __init__(
            self,
            user_name: str,
            system_code: str,
            max_retry: int = 10,
            base_url: str = "https://intl.fusionsolar.huawei.com/thirdData"
    ):
        self.user_name = user_name
        self.system_code = system_code
        self.max_retry = max_retry
        self.base_url = base_url

        self.session = requests.session()
        self.session.headers.update(
            {'Connection': 'keep-alive', 'Content-Type': 'application/json'})

        self.token_expiration_time = 0

    def __enter__(self):
        self.login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def _date_to_timestamp(self, from_date):
        return time.mktime(from_date.timetuple())

    def login(self):
        url = f'{self.base_url}/login'
        body = {
            'userName': self.user_name,
            'systemCode': self.system_code
        }
        self.session.cookies.clear()
        r = self.session.post(url=url, json=body)
        self._validate_response(response=r)
        self.session.headers.update(
            {'XSRF-TOKEN': r.cookies.get(name='XSRF-TOKEN')})
        self.token_expiration_time = pd.Timestamp.utcnow().timestamp() + 1200

    @staticmethod
    def _validate_response(response: requests.Response) -> bool:
        response.raise_for_status()
        body = response.json()
        success = body.get('success', False)
        if not success:
            if body.get('failCode') == 407:
                logging.debug('Error 407')
                raise HTTPError407(body)
            elif body.get('failCode') == 305:
                logging.debug('Error 305')
                raise HTTPError306(body)
            elif body.get('failCode') == 306:
                logging.debug('Error 306')
                raise HTTPError306(body)
            elif body.get('failCode') == 307:
                logging.debug('Error 307')
                raise HTTPError306(body)
            elif body.get('failCode') == 401:
                logging.debug('Error 401')
                raise HTTPError401
            else:
                raise HTTPError(body)
        else:
            return True

    @throttle_retry
    @authenticated
    def _request(self, function: str, data=None) -> Dict:
        if data is None:
            data = {}
        url = f'{self.base_url}/{function}'
        r = self.session.post(url=url, json=data)
        self._validate_response(r)
        return r.json()

    def get_station_list(self) -> Dict:
        return self._request("getStationList")

    def get_station_kpi_real(self, station_code: str) -> Dict:
        return self._request("getStationRealKpi",
                             {'stationCodes': station_code})

    def get_station_kpi_hour(self, station_code: str,
                             date: pd.Timestamp) -> Dict:
        time = int(date.timestamp()) * 1000
        return self._request("getKpiStationHour", {'stationCodes': station_code,
                                                   'collectTime': time})

    def get_station_kpi_day(self, station_code: str,
                            date: pd.Timestamp) -> Dict:
        time = int(date.timestamp()) * 1000
        return self._request("getKpiStationDay", {'stationCodes': station_code,
                                                  'collectTime': time})

    def get_station_kpi_month(self, station_code: str,
                              date: pd.Timestamp) -> Dict:
        time = int(date.timestamp()) * 1000
        return self._request("getKpiStationMonth",
                             {'stationCodes': station_code,
                              'collectTime': time})

    def get_station_kpi_year(self, station_code: str,
                             date: pd.Timestamp) -> Dict:
        time = int(date.timestamp()) * 1000
        return self._request("getKpiStationYear", {'stationCodes': station_code,
                                                   'collectTime': time})

    def get_dev_list(self, station_code) -> Dict:
        return self._request("getDevList", {'stationCodes': station_code})

    def get_dev_kpi_real(self, dev_id: str, dev_type_id: int) -> Dict:
        return self._request("getDevRealKpi",
                             {'devIds': dev_id, 'devTypeId': dev_type_id})

    def get_dev_kpi_fivemin(self, dev_id: str, dev_type_id: int, date: date) -> Dict:
        start_time = int(self._date_to_timestamp(date)) * 1000
        end_time = int(self._date_to_timestamp(date + timedelta(days=3))) * 1000
        return self._request("getDevHistoryKpi",
                             {'devIds': dev_id, 'devTypeId': dev_type_id,
                              'startTime': start_time, 'endTime': end_time})

    def get_dev_kpi_hour(self, dev_id: str, dev_type_id: int,
                         date: pd.Timestamp) -> Dict:
        time = int(date.timestamp()) * 1000
        return self._request("getDevKpiHour",
                             {'devIds': dev_id, 'devTypeId': dev_type_id,
                              'collectTime': time})

    def get_dev_kpi_day(self, dev_id: str, dev_type_id: int,
                        date: pd.Timestamp) -> Dict:
        time = int(date.timestamp()) * 1000
        return self._request("getDevKpiDay",
                             {'devIds': dev_id, 'devTypeId': dev_type_id,
                              'collectTime': time})

    def get_dev_kpi_month(self, dev_id: str, dev_type_id: int,
                          date: pd.Timestamp) -> Dict:
        time = int(date.timestamp()) * 1000
        return self._request("getDevKpiMonth",
                             {'devIds': dev_id, 'devTypeId': dev_type_id,
                              'collectTime': time})

    def get_dev_kpi_year(self, dev_id: str, dev_type_id: int,
                         date: pd.Timestamp) -> Dict:
        time = int(date.timestamp()) * 1000
        return self._request("getDevKpiYear",
                             {'devIds': dev_id, 'devTypeId': dev_type_id,
                              'collectTime': time})

    def dev_on_off(self, dev_id: str, dev_type_id: int,
                   control_type: int) -> Dict:
        # control_type
        # 1: power-on
        # 2: power-off
        return self._request("devOnOff",
                             {'devIds': dev_id, 'devTypeId': dev_type_id,
                              'controlType': control_type})

    def dev_upgrade(self, dev_id: str, dev_type_id: int) -> Dict:
        return self._request("devUpgrade",
                             {'devIds': dev_id, 'devTypeId': dev_type_id})

    def get_dev_upgradeinfo(self, dev_id: str, dev_type_id: int) -> Dict:
        return self._request("getDevUpgradeInfo",
                             {'devIds': dev_id, 'devTypeId': dev_type_id})


class PandasFS(FusionSolar):

    def __init__(
            self,
            station_code: str,
            user_name: str,
            system_code: str,
            max_retry: int = 10,
            base_url: str = "https://intl.fusionsolar.huawei.com/thirdData"
            ):

        FusionSolar.__init__(self, user_name=user_name, system_code=system_code, max_retry=max_retry, base_url=base_url)
        self.station_code = station_code

        for device in super(PandasFS, self).get_dev_list(station_code = station_code)['data']:
            if device['devTypeId'] == 1:
                self.OnduleurId=device['id']
            elif device['devTypeId'] == 39:
                self.BatterieId=device['id']
            elif device['devTypeId'] == 47:
                self.MeterId=device['id']
    
    # --- Internal functions.
    def _flatten_data(self, j):
        for point in j['data']:
            line = {'DtTm': point['collectTime']}
            line.update(point['dataItemMap'])
            yield line

    def _build_df(self, data):
        df = pd.DataFrame(self._flatten_data(data))
        df['DtTm'] = pd.to_datetime(df['DtTm'], unit='ms', utc=True)
        df.set_index('DtTm', inplace=True)
        df = df.astype(float)
        return df

    # --- Methods.
    def get_kpi_day(self, date: pd.Timestamp) -> pd.DataFrame:
        data = super(PandasFS, self).get_station_kpi_day(station_code=self.station_code, date=date)
        if len(data['data']) == 0:
            return pd.DataFrame()

        return self._build_df(data)

    # --- Retrieve a 3 days summary of major data per 5 minutes interval.
    def get_5min_data(self, dateFrom: date) -> pd.DataFrame:       
        resp = super(PandasFS, self).get_dev_kpi_fivemin(dev_id=self.OnduleurId, dev_type_id=1, date=dateFrom)
        if len(resp['data']) == 0:
            return pd.DataFrame()
        else:
            dfO = self._build_df(resp)[list({'mppt_power', 'day_cap', 'temperature'})].rename(columns = {'mppt_power': 'PV_power', 'day_cap': 'PV_dayCap'}, inplace = False)
            dfO['PV_power']=(1000*dfO['PV_power']).astype(int)
            resp = super(PandasFS, self).get_dev_kpi_fivemin(dev_id=self.MeterId, dev_type_id=47, date=dateFrom)
            dfM = self._build_df(resp)[list({'active_power',})].rename(columns = {'active_power': 'NET_power',}, inplace = False)
            dfM['NET_power']=dfM['NET_power'].astype(int)
            resp = super(PandasFS, self).get_dev_kpi_fivemin(dev_id=self.BatterieId, dev_type_id=39, date=dateFrom)
            dfB = self._build_df(resp)[list({'discharge_cap', 'ch_discharge_power', 'battery_soc', 'charge_cap'})].rename(columns = {'discharge_cap': 'BAT_disCap', 'ch_discharge_power': 'BAT_power', 'battery_soc': 'BAT_SoC', 'charge_cap': 'BAT_chCap'}, inplace = False)
            dfB['BAT_disCap']=(1000*dfB['BAT_disCap']).astype(int)
            dfB['BAT_chCap']=(1000*dfB['BAT_chCap']).astype(int)
            dfB['BAT_power']=(dfB['BAT_power']).astype(int)
            dfB['BAT_SoC']=(dfB['BAT_SoC']).astype(int)
            ElectrStatus=pd.merge(left=pd.merge(left=dfO, right=dfM, how='left', left_index=True, right_index=True), right=dfB, how='left', left_index=True, right_index=True)
            ElectrStatus['Consumed'] = 0-ElectrStatus['NET_power']+ElectrStatus['PV_power']-ElectrStatus['BAT_power']
            return ElectrStatus
