# Install MQTT broker.
As already mentionned, I opted for Mosquitto as MQTT broker.  Here are the steps to get it up and running.
## Install the software.
Install the software on the computer :

    sudo apt install -y mosquitto mosquitto-clients

Enable the service :

    sudo systemctl enable mosquitto.service
Check if service is running :

    mosquitto -v
## Configure the broker.
Update the configuration file :

    sudo nano /etc/mosquitto/mosquitto.conf
That configuration file must look like this :

    per_listener_settings true
    pid_file /run/mosquitto/mosquitto.pid  
    persistence true  
    persistence_location /var/lib/mosquitto/  
    log_dest file /var/log/mosquitto/mosquitto.log  
    include_dir /etc/mosquitto/conf.d  
    listener 1883  
    allow_anonymous false  
    password_file /etc/mosquitto/passwdcode
Then create a user and a password to access the broker  (it must also be mentionned into the LOWI its configuration page so that it can access the broker) :

    sudo mosquitto_passwd -c /etc/mosquitto/passwd YOUR_USERNAME
And, finally, restart the service :

    sudo systemctl restart mosquitto
There it is.  It is up and running.

# LOWI parameters.
In the LOWI configuration page, modify the following parameters:
- Allow LOWI to be published by MQTT (MQTT ENABLE checked)
- In MQTT Broker, mention the IP address of your broker.  Your broker should read port 1883 (which is the default port for MQTT).
- In MQTT token, mention the user on the broker and in MQTT Pass, its password.

The LOWI will publish its data every minute. If you activate the "P1 FLASH PUBLISH", it will publish every 10 seconds... as long as you have an MQTT broker to receive them.

# Topics.
Topics are published under the serial number of your LOWI. I therefore recommend installing [MQTT Explorer](http://mqtt-explorer.com/) (free Windows program) to see the topics published by your LOWI.
The LOWI will publish on several channels, those that you will have configured in the administration screen. However, it still publishes the CH0 topic with the counter status.
## Data present in all topics.
|Field| Description |
|--|--|
| ident | LOWI serial number |
| device_CH | Channel number configured on the LOWI |
| Name | Dataset name |
| Type | Source of data |
| Units | Data units (kWh, W, A, Various) |
| U | Voltage |
| I | Intensity in 1/100th of an Ampere |
| T | Rate (0=night, 1=day) |
## Specific to topic CH0.
|Field| Description |
|--|--|
| PI | Power Import (W) |
| PE | Power Export (W) |
| CIH | Import counter high rate hours |
| CIL | Import counter low rate hours |
| CEH | Export counter high rate hours |
| CEL | Export counter low rate hours |
| CG | Gaz counter |
| CW | Water counter |
## Specific to other topics.
|Field| Description |
|--|--|
| P | Power (W) |
| HC | Consumption / production of current hour (Wh) |
| DC | Current day consumption / production (Wh) |
| MC | Current month consumption / production (Wh) |
| CH | Value of high rate period counter (Wh) |
| CL | Value of low rate period counter (Wh) |

# Install MariaDB.
Let's first install the software and let it start as a service.

    sudo apt update &&  sudo apt upgrade
    sudo apt install mariadb-server mariadb-client -y
    sudo systemctl start mariadb
    sudo systemctl enable mariadb
Then create a database named P1.

    sudo mysql
    create database P1;
    GRANT ALL PRIVILEGES ON P1.* TO 'pi'@'192.168.1.%' IDENTIFIED BY '<password>';
    FLUSH PRIVILEGES;
    exit
No need to create the tables.  The software will do it by itself.

# Install python modules.
The program will read the MQTT topic CH0 and store the information into a MariaDB database.  For that, some additional python modules must be installed.  So, refer to the requirements file into the root folder.

    pip install -r requirements.txt
If, when running Compteur.py, you get the message telling numpy is not of the correct version (message like : libf77blas.so.3: cannot open shared object file: No such file or directory) :

    sudo apt-get install libatlas-base-dev

# Create a service reading the MQTT topics.

    cd /lib/systemd/system/
    sudo nano P1.service
Then add following lines into the service description:

    [Unit]
    Description=Read digital meter
    After=multi-user.target
    
    [Service]
    Type=simple
    ExecStart=/usr/bin/python /home/pi/python/Compteur.py
    Restart=on-abort
    
    [Install]
    WantedBy=multi-user.target
    enter code here
    
Assuming you placed the code into the /hom/pi/python/ folder.  If not, change that line into the service description.
Then, do the following :

    sudo chmod 644 /lib/systemd/system/P1.service
    chmod +x /home/pi/python/Compteur.py
    sudo systemctl daemon-reload
    sudo systemctl enable P1.service
    sudo systemctl start P1.service
As from now, every time you will start your Raspberry pi, it will read the smart meter and store the information into the database.
## Consumption table.
A table will be created into the database with the consumption of the house by 15 minutes:

    MariaDB [P1]> select * from Conso limit 10;

| DtTm | In_D |In_N    | OUT_D  | OUT_N | Soutire | Injecte |
|--|--|--|--|--|--|--|
| 2023-01-04 14:15:00 | 130.838 | 137.096 | 10.976 | 3.381 |   0.021 |       0 |
| 2023-01-04 14:30:00 | 130.922 | 137.096 | 10.976 | 3.381 |   0.084 |       0 |
| 2023-01-04 14:45:00 | 130.994 | 137.096 | 10.976 | 3.381 |   0.072 |       0 |
| 2023-01-04 15:00:00 | 131.079 | 137.096 | 10.976 | 3.381 |   0.085 |       0 |
| 2023-01-04 15:15:00 |  131.18 | 137.096 | 10.976 | 3.381 |   0.101 |       0 |
| 2023-01-04 15:30:00 | 131.378 | 137.096 | 10.976 | 3.381 |   0.198 |       0 |
| 2023-01-04 15:45:00 | 131.547 | 137.096 | 10.976 | 3.381 |   0.169 |       0 |
| 2023-01-04 16:00:00 | 131.711 | 137.096 | 10.976 | 3.381 |   0.164 |       0 |
| 2023-01-04 16:15:00 | 131.886 | 137.096 | 10.976 | 3.381 |   0.175 |       0 |
| 2023-01-04 16:30:00 | 132.036 | 137.096 | 10.976 | 3.381 |    0.15 |       0 |

This shows, into the 15 minutes after DtTm, the figures of the smart meter (the 4 indexes) and how much, during the 15 minutes had been taken from the network and how much had been injected on the network.
## Electricity price.
A second table is created and populated.  It is about the price of the electricity into the context of a dynamic contract at Engie.

    MariaDB [P1]> select * from PxElectr limit 10;

| DtTm                | price | Buy     | Sell  |
|--|--|--|--|
| 2019-12-31 23:00:00 | 41.88 | 4.65552 | 4.188 |
| 2020-01-01 00:00:00 |  38.6 | 4.30784 |  3.86 |
| 2020-01-01 01:00:00 | 36.55 | 4.09054 | 3.655 |
| 2020-01-01 02:00:00 | 32.32 | 3.64216 | 3.232 |
| 2020-01-01 03:00:00 | 30.85 | 3.48634 | 3.085 |
| 2020-01-01 04:00:00 | 30.14 | 3.41108 | 3.014 |
| 2020-01-01 05:00:00 | 30.17 | 3.41426 | 3.017 |
| 2020-01-01 06:00:00 |    30 | 3.39624 |     3 |
| 2020-01-01 07:00:00 | 30.65 | 3.46514 | 3.065 |
| 2020-01-01 08:00:00 | 30.65 | 3.46514 | 3.065 |

- price it the price on the financial markets (EPEX BE day-ahead)
- Buy is how much you would had bought your electricity at that time,
- Sell is how much you would had been paid for your solar production.

DtTm is always (into both table) expressed in UTC time.