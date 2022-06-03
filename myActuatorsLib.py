# Auteur  : Patrick Pinard 
# Date    : 17.4.2022
# Objet   : Gestion de relais (Relay) et des objets lucarne (skylight) & vanne eau (watervalve)
# Source  : myActuatorsLib.py
# Version : 1.1 - ajout de l'objet FAN() pour gestion des ventilateurs

# -*- coding: utf-8 -*-

#   Clavier MAC :      
#  {} = "alt/option" + "(" ou ")"
#  [] = "alt/option" + "5" ou "6"
#   ~  = "alt/option" + n    
#   \  = Alt + Maj + / 

VERBOSE                 = False     # affichage de tous les log.     
WINDOW_OPEN_CLOSE_TIME  = 60        # temps nécessaire pour vérin afin d'ouvrir/fermer de la lucarne
                                    # 10mm/s pour 500mm = 50 secondes minimum. A ajuster lors de l'installation

import SequentLib8relay 
from myLOGLib  import LogEvent
from time import sleep

class Relay(object):
    """
    Classe definissant un module de 8 relais caracterisé par les méthodes : 
        - get : permet de lire l'état d'un relai (1..8) et 
                retourne son état sous forme ON = 1; OFF = 0 
        - set : permet de changer l'état d'un relai (1..8) en 
                stipulant son "state" sour forme ON = 1; OFF = 0
    """

    def __init__(self, relayid, name):
        """
        Constructeur de la classe Relay : 

        - name    : nom du relai
        - stack   : identifiant du module dans le stack (0 ..7, par defaut :0)
        - relayid : identifiant du relai ( correspond au n° de relai 1..8, attention les n° sont inversés !!!)
        - unit    : l'unité de mesure (ON : 1 ; OFF: 0)
        - type    : constructeur du relai et type
        - state   : contient l'état actuel du relai (ON : 1;  OFF : 0)
       
        """

        self.relayid = relayid
        self.name = name     
        self.stack = 0                                               
        self.type = "Sequent - 8 Relay Stackable Module" 
        self.unit = '(ON=1; OFF=0)'
        self.state =  0     
                                                      
        
        LogEvent("Création du relai #" + str(self.relayid) + " pour " + self.name )
                                 
    def __repr__(self):

        """
        Méthode permettant d'afficher les paramètres principaux du relai.
        """

        return "\nRelay Information : \n name   : {}\n type   : {}\n   relayid : {}\n unit   : {} \n state  : {}\n stack  : {}".format(self.name, self.type, self.relayid, self.unit, self.state, self.stack)

    def open(self):

        """
        Méthode permettant d'ouvrir le relai (state = 0).

        """

        self.set(0)
        if VERBOSE : LogEvent("Relai #" + str(self.relayid) + " ouvert."  ) 

        return

    def close(self):

        """
        Méthode permettant de fermer le relai (state = 1).

        """

        self.set(1)
        if VERBOSE : LogEvent("Relai #" + str(self.relayid) + " fermé."  ) 

        return

    def set(self, state):

        """
        Méthode permettant de changer l'état du relai.
        - state : 1 = ON (close); 0 = OFF (open)

        """
        if (state==0) or (state==1):
            try:
                SequentLib8relay.set(self.stack, self.relayid, state)
                self.state = state 
            except Exception as e:
                LogEvent("ERREUR : Pas possible de changer l'état du relai #" + str(self.relayid) + " : " + self.name)
                return
            if VERBOSE : LogEvent("Etat du relai #" + str(self.relayid) + " - " + self.name + " :  " + (str(self.state)) + " " + self.unit)
        else:
            LogEvent("ERREUR : Demande de changement d'état du relai impossible. 1 ou 0, pas d'autre paramètre possible.")
        return 
        
    def get(self):

        """
        Méthode permettant de lire l'état du relai.
        Output : 1 = ON (close); 0 = OFF (open)
        """
       
        try:
            state = SequentLib8relay.get(self.stack, self.relayid)
        except Exception as e:
            LogEvent("Erreur de lecture d'état du relai #" + str(self.relayid) + " : " + self.name)
       
        if VERBOSE : LogEvent("Etat du relai #" + str(self.relayid) + " - " + self.name + " :  " + (str(self.state)) + " " + self.unit)

        return state




class SkyLight(object):
    
    """
    Classe definissant la lucarne (SkyLight) commandée par un vérin électrique pour l'ouverture et fermeture  : 
        - open  : ouverture de la lucarne (state = 1)
        - close : fermeture de la lucarne (state = 0)
        - Attention : utilise le relai 1 pour la commande ON/OFF et 
                      les relais 2 et 3 pour le changement de polarité selon câblage pré-établi.
        ... Pas utilisé à ce jour car mécanique d'ouverture et fermeture à construire autour du verin...
    """

    def __init__(self):
        """
        Constructeur de la classe SkyLight : 

        - name  : nom de l'objet (lucarne)
        - id    : identifiant de la lucarne (une seule lucarne #1)
        - unit  : ON : 1  (Ouvert) ; OFF: 0 (Fermé)
        - type  : type de vérin utilisé
        - state : contient l'état actuel de la lucarne (ON : 1 (ouvert);  OFF : 0 (fermé))
        """
        #LogEvent("Création de la lucarne." )

        self.id = 1
        self.name = "lucarne"  
        self.type = "Vérin électrique 12V VEVOR 500mm" 
        self.unit = '(Ouverture=1 (open); Fermeture=0 (close))'
        self.state =  0     

        #self.RelayONOFF = Relay(1,"Commande Ouverture (1) / Fermeture (0) ") 
        #self.RelayReversePolarity2 = Relay(2,"Changement de polarité -/+") 
        #self.RelayReversePolarity3 = Relay(3,"Changement de polarité +/-")    
        #self.RelayONOFF.open()

    def __repr__(self):

        """
        Méthode permettant d'afficher les paramètres principaux du relai.
        """

        return "\nLucarne Information : \n name   : {}\n type   : {}\n   id   : {}\n unit   : {} \n state  : {} ".format(self.name, self.type, self.id, self.unit, self.state)

    def open(self):

        """
        Méthode permettant l'ouverture de la lucarne au travers de 3 relais pour inversion polarité.
        """
        LogEvent("Commande ouverture de la " + self.name )
 
        #self.RelayONOFF.open()
        #sleep(0.1)
        #self.RelayReversePolarity2.close()
        #self.RelayReversePolarity3.close()
        #sleep(0.1)
        #self.RelayONOFF.close()
        
        #en attente de la fermeture complète puis on ouvre le relai de commande
        #sleep(WINDOW_OPEN_CLOSE_TIME)
        #self.RelayONOFF.open()

        self.state = 1
        LogEvent("La " + self.name + " est ouverte.")
        
        return 

    def close(self):

        """
        Méthode permettant la fermeture  de la lucarne au travers de 3 relais.
        """

        LogEvent("Commande fermeture de la " + self.name )
      
        #self.RelayONOFF.open()
        #sleep(0.1)
        #self.RelayReversePolarity2.open()
        #self.RelayReversePolarity3.open()
        #sleep(0.1)
        #self.RelayONOFF.close()
        #en attente de la fermeture puis on ouvre le relai de commande
        #sleep(WINDOW_OPEN_CLOSE_TIME)
        #self.RelayONOFF.open()
        #self.state = 0
        LogEvent("La " + self.name + " est fermée.")
        return 

class Fan(object):
    
    """
    Classe definissant un ventilateur (Fan)  : 
        - on  : activation (state = 1)
        - off : arrêt (state = 0)
        - utilise le relai 7 pour la commande ON/OFF 
    """

    def __init__(self, relayid):
        """
        Constructeur de la classe Fan : 

        - name  : nom de l'objet (Fan)
        - id    : identifiant du relai des ventilateurs
        - unit  : ON : 1  (Ouvert) ; OFF: 0 (Fermé)
        - type  : type de ventilateur utilisé
        - state : contient l'état actuel du ventilateur (ON : 1;  OFF : 0 )
        """
        LogEvent("Création du ventilateur." )

        self.id = relayid
        self.name = "Ventilateur(s)"  
        self.type = "Ventilateur(s) 24V" 
        self.unit = '(1=ON / 0=OFF)'
        self.state =  0  
        self.RelayONOFF = Relay(7,"Ventilateur(s)") 
        self.RelayONOFF.open() 

    def __repr__(self):

        """
        Méthode permettant d'afficher les paramètres principaux du relai d'aération.
        """
        return "\nAération Information : \n name   : {}\n type   : {}\n   id   : {}\n unit   : {} \n state  : {} ".format(self.name, self.type, self.id, self.unit, self.state)

    def on(self):

        """
        Méthode permettant d'activer le(s) ventilateur(s)
        """
              
        self.RelayONOFF.close()
        self.state = 1
        LogEvent("" + self.name + "  enclenché(s) (ON).")
        
        return 

    def off(self):

        """
        Méthode permettant d'arrêter le(s) ventilateur(s).
        """

        self.RelayONOFF.open()
        self.state = 0
        LogEvent("" + self.name + " arrêté(s) (OFF).")
        return 

class WaterValve(object):
    
    """
    Classe definissant une valve d'eau commandée par un relai électrique pour l'ouverture et fermeture  : 
        - open  : ouverture de la vanne d'eau  (state = 1)
        - close : fermeture de la vanne d'eau  (state = 0)
    Utilise la classe Relay (attention car sens inverse du relai : relai open = fermeture de la valve, relai close = ouverture de la valve)
    """

    def __init__(self, id, name):
        """
        Constructeur de la classe Valve : 

        - name  : nom de la valve
        - id    : identifiant de la valve 
        - unit  : ON : 1  (Ouvert) ; OFF: 0 (Fermé)
        - type  : type de valve utilisé
        - state : contient l'état actuel de la valve (ON : 1 (ouvert);  OFF : 0 (fermé))
        """
        LogEvent("Création de " + name)

        self.id = id
        self.name = name  
        self.type = "Valve d'eau GARDENA 24V " 
        self.unit = '(Ouverture=1 (open); Fermeture=0 (close))'
        self.state =  0     
        self.Relay = Relay(id,name)     

    def __repr__(self):

        """
        Méthode permettant d'afficher les paramètres principaux de la valve.
        """

        return "\nValve Information : \n name   : {}\n type   : {}\n   id   : {}\n unit   : {} \n state  : {}".format(self.name, self.type, self.id, self.unit, self.state)

    def open(self):

        """
        Méthode permettant l'ouverture de la valve.
        """

        LogEvent("Ouverture de la " + self.name )

        self.Relay.close()   # fermeture du relai = ouvertue de la valve
        self.state = 1

        return 

    def close(self):

        """
        Méthode permettant la fermeture  de la valve et enregistrement du changement d'état.
        """

        LogEvent("Fermeture de la " + self.name )

        self.Relay.open()   # ouverture du relai = fermeture de la valve
        self.state = 0

        return 

if __name__ == "__main__":

    LogEvent(" ---- test de la librairie MyActuatorsLib   -----")
    print()
    print("Remise à zéro de tous les relais")
    SequentLib8relay.set_all(0, 0)
    sleep(3)
    print()
    print("Création des objets")
    Water_Valve_Zone_1 = WaterValve(4,"Valve d'eau zone 1")
    Water_Valve_Zone_2 = WaterValve(5,"Valve d'eau zone 2")
    Window = SkyLight()
    print(Water_Valve_Zone_1)
    print(Water_Valve_Zone_2)
    print(Window)
    print()
    sleep(5)
    print("test de simulation d'ouverture de la lucarne")
    Window.open()
    sleep(5)
    Window.close()
    print("test de simulation d'ouverture de la vanne 1 (r4) et 2 (r5)")
    Water_Valve_Zone_1.open()
    Water_Valve_Zone_2.open()

    sleep(5)
    
    Water_Valve_Zone_2.close()
    Water_Valve_Zone_1.close()

    SequentLib8relay.set_all(0, 0)
