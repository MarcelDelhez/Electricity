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
