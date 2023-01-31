# Interface with FusionSolar.
FusionSolar from Huawei provides an API interface to retrieve information about solar plats.
This module access those APIs.
## Retrieve major information at 5 min interval.
Imports :

    from datetime import datetime, date, timedelta
    from FusionSolar import northbound

Login:

    user = 'MyUser'
    password = 'MyPassword'
    station_code = 'MyPlantCode'
    
    # Create an instance of the FusionSolar class
    FS = northbound.PandasFS(user_name=user, system_code=password, base_url="https://eu5.fusionsolar.huawei.com/thirdData", station_code=station_code)
Retrieve data:

    try:
        ElectrStatus=FS.get_5min_data(dateFrom=date.today())
    except:
        print("It seems that the maximum number of calls per day has been exceeded.")
Result:
  ![Output DataFrame](https://github.com/MarcelDelhez/Electricity/blob/main/FusionSolar/ElectrStatus.PNG)  