# About the repository.
L'objectif de ce repository est de décrire comment je compte gérer l'énergie électrique de ma maison.
Dans ce repository, je vais expliquer comment j'optimise ma consommation électrique de façon globale.  Je publierai aussi les outils que j'utilise pour ce faire.
 
# Context.
First of all, I must explain what I have in terms of electrical appliances, electricity supply contract, ... in short, the context in which this small project is located.
## Electrical appliances.
I have the following electrical appliances:
- Photovoltaic panels for a power of 10 kW peak coupled with an 8 kW inverter and a 10 kWh domestic battery;
- An electric car charging station (Alfen EVE Single pro-line);
- A Daikin brand air-conditioning system;
- Classic household appliances (hobs, dishwashers, washing machine, dryer, ovens, heated towel rails, fridges and freezers, lighting in the garden, etc.).
## Monitoring devices.
To manage power consumption, I have various devices such as:
- A LOWI from 2-Wire.be connected to port P1 of the smart meter;
- A Raspberry PI 3B+
For information, the LOWI is not necessary since I have photovoltaic panels and these have an energy measurement system on which I can (and I may do so) connect via ModBus TCP. The project is still in its infancy, so the hardware configuration could change over time.
 
# The objective pursued.
The main objective is to minimize the electricity bill, but as you read my publications, you will realize that reducing bills can easily go hand in hand with sustainability.
Indeed, I am going to base myself on somewhat atypical electricity supply contracts, namely dynamic contracts. To put it simply, these contracts have the particularity that the price of electricity varies from hour to hour according to fluctuations in the wholesale markets (in Belgium, according to the EPEX Day-ahead index). The next day's prices are determined daily at 2 p.m. and can be viewed on various [websites](https://transparency.entsoe.eu/transmission-domain/r2/dayAheadPrices/show?name=&defaultValue=false&viewType=TABLE&areaType=BZN&atch=false&dateTime.dateTime=02.11.2022%2000:00%7CCET%7CDAY&biddingZone.values=CTY%7C10YBE----------2!BZN%7C10YBE----------2&resolution.values=PT60M&dateTime.timezone=CET_CEST&dateTime.timezone_input=CET%20%28UTC%201%29%20/%20CEST%20%28UTC%202%29).
 
I start from the premise that the cheaper electricity is on the markets, the more sustainable it is. The reason is that at times when electricity is cheap, it is produced from a nuclear, wind or photovoltaic source. That is to say the means of production used to cover the consumption base. On the other hand, when electricity is expensive, it is necessary to implement production units able to respond quickly to peaks in demand. Admittedly, hydroelectric production is one of these means and is sustainable, but, at least in Belgium, the capacity is very limited. Most, if not almost all, of the consumption peaks are covered by gas-steam power plants, which are not sustainable.
 
In addition, the price for using the distribution network depends on the power consumed (measured over the quarter-hour of greatest consumption during the month). The more the electricity consumption is spread out over the day and the lower this peak will be, the lower the bill for using the network will be. From a sustainability point of view, if all consumers spread their consumption over the day and therefore smooth out the peaks, at least gas-fired power plants will have to be used to produce electricity and therefore the greener the electricity produced. PS: Thank you for not criticizing me when I put nuclear in green energies. My definition of green here is "without greenhouse gas emissions".
 
# The main challenges.
The biggest consumers of electrical energy in my house are clearly the car and the air conditioning system. It is therefore to these two consumptions that I will focus first.
## The car.
Ideally, an electric car should be recharged from the production of photovoltaic panels. However, solar panels produce discontinuously from season to season as well as from day to day and hour to hour. They produce much less in winter than in summer, months (or not) the days of rain and, during the same day, the cloud cover varies the production from minute to minute. Also, it is uncertain whether the car is present at the garage when the panels produce.
It is therefore necessary to be able to modulate the power injected into the car according to what the photovoltaic installation produces at time T and according to what the other electrical appliances in the house consume.
 
At least in winter, the car will have to be charged from the network. We will therefore make sure to do it at times when electricity is the least expensive (usually between 2 and 6 am). However, if we know that the car will be in the garage when the photovoltaic panels produce more than necessary to cover the needs of the house, it may be in our interest to charge the car at that time.
I said "maybe" because if I charge my car between 2am and 6am in the morning with electricity from the grid which costs me say, 7 cents/kWh and I resell the excess solar panels at 12 cents / kWh the next day, it is financially more attractive not to use self-generated energy. Is it less green for the cause? I do not believe that. At night, we used green energy (from the production base) and, during the day, we discharged green energy into the grid that should not have been produced by a gas-fired power plant. So, and because it's easier to quantify, we'll only focus on the cost.
## Air conditioning.
Air conditioning is more complex than the car. In summer, it is used to cool the house. In spring and autumn, it is used for heating. Its air freshening function is simple. If it is hot in the house, it is because the sun heats the walls and, if it heats the walls, it also produces electricity through the photovoltaic panels. So, you can simply decide to run the air conditioning when you feel the need. If you want to go further, you can control the air conditioning using a home automation solution when the temperature requires it and when the photovoltaic panels produce more than necessary. If we look at the consumption of the house as a whole, I believe that this option should be retained, especially in the context of charging an electric car.
 
For the heating function, there is interaction between the air conditioning system and the boiler. When I use the air conditioning to heat the house, I don't need to turn on the boiler and therefore I don't use fuel oil. It's a more sustainable way to heat the house. Therefore, when the outside temperature allows it and when the photovoltaic production allows it, it is necessary to heat with the air conditioning. The problem is that the need for heat appears in the morning, to heat the house after a night without heating, and in the evening when it is cooler. At these hours, photovoltaic production is zero. It is therefore clearly necessary to have another solution for heating outside the sunny hours.
## Cooking.
As we cook entirely with electricity (hobs, ovens, etc.), cooking represents a significant electricity consumption. Admittedly, we change our habits to consume less electricity for cooking, but that's not my responsibility. This is my wife's area of expertise and I have no say in it. So I won't talk about it here either. However, and don't tell her that I put the idea here, if you cook for hot meals at noon rather than in the evening, you increase the self-consumption of electricity.
## Wash the dishes.
Washing the dishes should ideally be done when the sun is shining. So definitely no longer in the evenings as we do now. However, the dishwasher is in the kitchen and cannot be controlled by WiFi (at least not mine). So I don't have access to it.
## To do the laundry.
There too, these are devices to which I do not have access and, there too, it is better to make them work when the energy is produced to supply them. In fact, the ideal set-up would be to start the laundry between 10:30 a.m. and 11 a.m., to start the dishwasher around 1 p.m. and the dryer around 2 or 2:30 p.m. As I cannot automate the starting of these devices, I can only plead with the hostess who, moreover, will not listen to me.
 
# My starting set-up.
## Lowi.
I have a LOWI bought from 2-wire.be which, every 10 seconds, publishes the state of the electricity meters (and other information in addition) on MQTT queues. [See my LOWI configuration in the page dedicated to it](./LOWI/README.md).
What I do first is collect data and store it in a database.
## Raspberry pi.
The purpose of the Raspberry pi in its first functions is to serve as an MQTT broker to distribute the LOWI data and on the other hand, to host the service which reads the MQTT messages to store them in the database.
I chose [Mosquitto](https://mosquitto.org/) as the MQTT broker because it is light and fast so, in my opinion, perfectly suited to a small machine like my Raspberry Pi 3b+.
The database is a [MariaDB](https://mariadb.org/) database because it is an excellent database and because, if I implement a web server, it will be a Wordpress which relies on a MySQL/MariaDB DB.
