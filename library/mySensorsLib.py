# Auteur  : Patrick Pinard 
# Date    : 27.8.2023
# Objet   : sondes de température, humidité et anémomètre.
# Source  : mySensorsLib.py
# Version : 1  (
# Changes : -

# -*- coding: utf-8 -*-

#   Clavier MAC :      
#  {} = "alt/option" + "(" ou ")"
#  [] = "alt/option" + "5" ou "6"
#   ~  = "alt/option" + n    
#   \  = Alt + Maj + / 

VERBOSE = False     # affichage de tous des log 
SIMULATE = True     # mode simulation

if not SIMULATE : from adc       import ADC
from myLOGLib  import LogEvent
if not SIMULATE : import glob
import random


def mapRange(value, inMin, inMax, outMin, outMax):
    return outMin + (((value - inMin) / (inMax - inMin)) * (outMax - outMin))


class Humidity(object):

    """
    Classe definissant un capteur d'humidité de l'air caracterisés par les méthodes : 
        - read : retourne la taux d'humidité en %HR  
        
    """

    def __init__(self, channelID):
        """
        Constructeur de la classe  : 

        - name  : nom du capteur d'Humidité de l'air
        - id : identifiant  
        - unit : l'unité de mesure 
        - type : type de sonde 
        - unit : unité de valeur mesurée
        - adc_channel : n+ du canal sur ADC
        - value: retourne la mesure en %HR
        https://learn.sparkfun.com/tutorials/hih-4030-humidity-sensor-hookup-guide?_ga=2.262327566.340503846.1650249449-1295637178.1650249449

        """

        
        self.id = 1
        self.name = "Humidité de l'air"                                                    
        self.type = "Sparkfun HIH-4030" 
        self.unit = '%HR'
        self.value = 0.0
        
        if not SIMULATE :  self.adc = ADC()
        self.adc_channel = channelID

        LogEvent("Création de la sonde d'humidité de l'air intérieur." )
        
    def __repr__(self):

        """
        Méthode permettant d'afficher les paramètres principaux du capteur.
        """

        return "\nSensor Information : \n name   : {}\n type   : {}\n   id   : {}\n unit   : {} \n value  : {} ".format(self.name, self.type, self.id, self.unit, self.value)

    def read(self, T):

        """
        Méthode retournant le niveau d'humidité 'H'
        Ajustement nécessaire si température différente de 25°C avec la formule suivante : 
        Vout = (supply_voltage) x (0.0062 (sensor RH) +0.16), typical at 25°C
        True RH = (Sensor RH) / (1.0546-0.00216T), T in  °C
        T = Température actuelle en °C pour ajuster le calcul de TrueRH
        """
        supply_voltage = 5  
        if not SIMULATE :  
            vout = ADC.read_voltage(self.adc, self.adc_channel) * supply_voltage/1023
            RH = ((vout) / (0.0062 * supply_voltage) - 25.81)
            TrueRH = RH / (1.0546 - (0.00216 * T))
            H = round(TrueRH,2)
        else:
            H = random.ranint(0,100)
        self.value = H
        return H


class Anemometer(object):

    """
    Classe definissant un anénomètre caracterisés par les méthodes : 
        - read : retourne la vitesse du vent en m/s  
        
    """

    def __init__(self, channelID):
        """
        Constructeur de la classe  : 

        - name  : nom de la sonde 
        - id : identifiant de la sonde 
        - unit : l'unité de mesure 
        - type : type de sonde (
        - unit : unité de valeur mesurée
        - adc_channel : n+ du canal sur ADC
        - value: retourne la mesure en km/h
        """

        
        self.id = 1
        self.name = "anémomètre"                                                    
        self.type = "QS-FS01" 
        self.unit = 'km/h'
        self.value = ""
        
        if not SIMULATE :  self.adc = ADC()
        self.adc_channel = channelID
        
        LogEvent("Création de l'anénomètre." )
        
    def __repr__(self):

        """
        Méthode permettant d'afficher les paramètres principaux d'une sonde de température.
        """

        return "\nSensor Information : \n name   : {}\n type   : {}\n   id   : {}\n unit   : {} \n value  : {} ".format(self.name, self.type, self.id, self.unit, self.value)

    def read(self):

        """
        Méthode retournant la vitesse du vent en km/h.
        1 m/s = 3.6 km/h
        """
        
        if not SIMULATE :  
            anemometer_voltage = ADC.read_voltage(self.adc, self.adc_channel)/1000
            if anemometer_voltage > 0.4:
                windspeed = ((anemometer_voltage -0.4) / 2.0 * 32.4) * 3.6
            else:
                windspeed = 0.00
            windspeed = round(windspeed,2)
        else: 
            windspeed= random.randint(0,50)
            
        self.value = windspeed
        return windspeed
        


class Temperatures(object):

    """
    Classe pour les deux sondes de températures caracterisés par les méthodes : 
        - read : retourne les valeurs de températures intérieure et extérieure  
    Emplacement des fichiers : /sys/bus/w1/devices/28*/w1_slave
    """

    def __init__(self):
        """
        Constructeur de la classe sonde de températures : 

        - name  : nom de la sonde 
        - id : identifiant de la sonde (0 : interne ou 1:externe)
        - unit : l'unité de mesure (string, par defaut °Celsius)
        - type : type de sonde (i.e : DS18B20)
        
        """
                
        LogEvent("Création des sondes de températures intérieure & extérieure." )

        self.id   = 1
        self.name = "sondes de température de l'air"                                                 
        self.type = "DS18B20" 
        self.unit = '°Celsius'
        self.value = []

                                                     
                                         
    def __repr__(self):

        """
        Méthode permettant d'afficher les paramètres principaux d'une sonde de température.
        """

        return "\nSensor Information : \n name   : {}\n type   : {}\n   id   : {}\n unit   : {} \n value  : {} ".format(self.name, self.type, self.id, self.unit, self.value)
    
    def read(self):

        """
        Méthode permettant de lire les températures : intérieure et extérieure.
        Retourne une liste avec les valeures de températures au format float.
        """
        t = []
        if not SIMULATE :  
            routes_capteurs = glob.glob("/sys/bus/w1/devices/28*/w1_slave")
       

            # les sondes sont crées avec identifiant unique de type 28-3c01d0750cbe 
            # -> ../../../devices/w1_bus_master1/28-3c01d0750cbe
            # et l'autre identifiant : 28-3c01e0763559 
            # glob permet de retourner la liste des répertoires avec le prefix demandé 

            if len(routes_capteurs) > 0 :
                c = 1  #nombre de routes = nombre de capteurs
                for capteur in routes_capteurs :

                    # fichier w1_slave contient le relevé de température

                    try:
                        file = open(capteur)
                        content = file.read()
                        file.close()
                    except : 
                        raise LogEvent("ERREUR : lecture du fichier températures : " + (capteur))

                    # contenu texte du fichier du type : 
                    # 6c 01 55 05 7f a5 81 66 56 : crc=56 YES
                    # 6c 01 55 05 7f a5 81 66 56 t=22750

                    try:
                        line = content.split("\n")[1]
                        temperature = line.split(" ")[9]
                    except : 
                        raise LogEvent("ERREUR : lecture du contenu fichier de températures : " + (content)) 
                    temperature = float(temperature[2:]) / 1000
                    t.append(round(temperature,2))
                    c += 1
            else :
                LogEvent("ERREUR : Aucune sonde détectée. Vérifier les branchements.")
        else:
            t.append(random.randint(0,40))  #Tint
            t.append(random.randint(0,40))  #Tout
            
        self.value = t
        return t
        

class Moisture(object):

    """
    Classe definissant une sonde d'humidité au sol caracterisé par les méthodes suivantes : 
        - read : retourne la valeur du sonde actuelle et stocke celle-ci dans records au format JSON.
    """

    def __init__(self, id, name, adc_channel ):
        """
        Constructeur de la classe sonde d'humidité: 

        - name  : nom de la sonde 
        - id : identifiant de la sonde 
        - unit : l'unité de mesure (par defaut %HR)
        - type : type de sonde 
        - value : valeur mesurée de la tension sur la sonde
        - text : contient en texte la dernière mesure effectuée : 
                 Sec, Humide, Mouillé ou erreur si lecture erronée
        - adc_channel : n° du port analogique de lecture (0..7)sur module adc
        
        """

        LogEvent("Création de la sonde d'humidité au sol " + name)

        self.id = id
        self.name = name                                                
        self.type = "SoilWatch 10." 
        self.unit = "%HR"

        if not SIMULATE: self.adc = ADC()    
        self.value = ""    
        self.text = ""
        self.adc_channel = adc_channel                    
                                 
    def __repr__(self):

        """
        Méthode permettant d'afficher les paramètres principaux d'une sonde .
        """

        return "\nSensor Information : \n name   : {}\n type   : {}\n   id   : {}\n unit   : {} \n value  : {}".format(self.name, self.type, self.id, self.unit, self.value)

    def read(self):

        """
        Méthode retournant le niveau d'humidité mesuré dans le sol par la sonde.
        Valeurs comprises entre 0 et 600 selon datasheet du SoilWatch 10.
        https://pino-tech.eu/product/soilwatch-10/
        Voltage: 3.1 – 5.0V (absolute maximum 5.5V)
        Output: 0 – 3.0V (approximately)
        
                    Min    Max  
        rawValue    0      3000    (0 .. 3V)  
        HR%         0      5        sonde dans l'air
        HR%         5      30       sol sec
        HR%         30     45       sol humide
        HR%         45     70       sol mouillé
        HR%         70     95       sol trempé
        HR%         95     100      sonde dans l'eau
        """
        
        rawValue = 0 
        minVoltage = 0
        maxVoltage = 3000
        vwcValue = 0

        try: 
            if not SIMULATE: 
                rawValue = int(ADC.read_voltage(self.adc, self.adc_channel))
            else: 
                rawValue = random.randint(0,3000)
        except Exception as error:
            LogEvent("Erreur de lecture de la sonde " + self.name + " : " + str(error))
            return 0
        
        #LogEvent("rawValue (0-3000 mV): " + str(rawValue))
        vwcValue = int(mapRange(rawValue, minVoltage, maxVoltage, 0, 100))
        #LogEvent("vwcValue (0-100 %HR)= " + str(vwcValue))
       
      
        self.value = vwcValue

        if (self.value < 5) : 
            self.text = "(sonde dans l'air)"
        elif (5 <= self.value and self.value < 30):
            self.text = '(sol sec)'
        elif (30 <= self.value and self.value < 45):
            self.text = '(sol humide)'
        elif (45 <= self.value and self.value < 70):
            self.text = '(sol mouillé)'
        elif (70 <= self.value and self.value < 90):
            self.text = '(sol trempé)'
        elif (90 <= self.value and self.value < 100):
            self.text = "(sonde dans l'eau)"
        else:
            self.text = '(erreur lecture sonde)'
       
        return self.value
   
   
if __name__ == "__main__":

    print(" ---- début tests de mySensorsLib   -----")
    print()
    T = Temperatures()
    t= T.read()
    H1 = Moisture(1,"ZONE1", 0)
    H2 = Moisture(2,"ZONE2", 1)
    WindSpeedSensor = Anemometer(1)
    Tint = t[0]
    Text = t[1]
    windspeed  = WindSpeedSensor.read()
    print('Vitesse du vent        [km/h] : ' ,'{:3.2f}'.format(windspeed))
    print("Température intérieure [°C]   : ", Tint)
    print("Température extérieure [°C]   : ", Text)
    print("Humidité sol zone 1    [%HR]  : ", H1.read())
    print("Humidité sol zone 2    [%HR]  : ", H2.read())
    print()
    print(T)
    print(H1)
    print(H2)
    print(WindSpeedSensor)
    print()
    print(" ---- fin des tests de mySensorsLib   -----")






