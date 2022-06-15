# Auteur    : Patrick Pinard
# Date      : 23.12.2019
# Objet     : lecture et écriture de fichier json 
# Version   : 1
# Statut    : 

# -*- coding: utf-8 -*-
#   Clavier MAC :      
#  {} = "alt/option" + "(" ou ")"
#  [] = "alt/option" + "5" ou "6"
#   ~  = "alt/option" + n    
#   \  = Alt + Maj + /  

import json
import io
from myLOGLib import LogEvent

try:
    to_unicode = unicode
except NameError:
    to_unicode = str

filename = 'mydata.json' 

def writeJSONtoFile(filename, data):
    
    """
    Fonction permettant d'écrire une donnée au format JSON sur un fichier.
    Si sauvegarde d'un objet, ajouter json.dumps(<object>.__dict__) pour le convertir au format JSON.
    """

    try:
        
        with io.open(filename, 'w', encoding='utf8') as outfile:
            str_ = json.dumps(data,
                        indent=4, sort_keys=True,
                        separators=(',', ': '), ensure_ascii=False)
            outfile.write(to_unicode(str_))
        
    except IOError as e:    
        LogEvent("Erreur de sauvegarde des données au format JSON : {0}".format(e))
        return False

    return True 


def readJSONfromFile(filename):
    
    """
    Fonction permettant de lire un fichier au format JSON.
    Renvoie True si lecture correcte.
            False si fichier inexistant ou erreur de lecture.
    """
    dataJSON = []
    try:
        with open(filename, 'r') as json_file:
            dataJSON = json.load(json_file)
    except IOError as e:    
        LogEvent("Erreur de lecture du fichier JSON : {0}".format(e))
        return False, dataJSON
    
    return True, dataJSON

if __name__ == "__main__":

        
    json_data = [
    {
            "Date": "06.01.2020",
            "Location": "Atelier",
            "Relays": {
                "Relay1": False,
                "Relay2": True,
                "Relay3": True
            },
            "Time": "18:00:00",
            "Values": {
                "Humidity": 60,
                "Pressure": 850
    }
        },
        {
            "Date": "07.01.2020",
            "Location": "Atelier",
            "Relays": {
                "Relay1": True,
                "Relay2": True,
                "Relay3": False
            },
            "Time": "18:30:00",
            "Values": {
                "Humidity": 65,
                "Pressure": 900
            }
        }
    ]

 
    writeJSONtoFile(filename, json_data)
    data = []
    data = readJSONfromFile(filename)
    print("data format json  : ", data)

