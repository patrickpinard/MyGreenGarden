#!/usr/bin/env python3

# Auteur    : Patrick Pinard
# Date      : 27.8.2023
# Objet     : gestion des LOG pour application MyApp
# Source    : myLOGLib.py
# Version   : 1 
# Statut    : ok

# -*- coding: utf-8 -*-
#   Clavier MAC :      
#  {} = "alt/option" + "(" ou ")"
#  [] = "alt/option" + "5" ou "6"
#   ~  = "alt/option" + n    
#   \  = Alt + Maj + /  

import logging
import datetime


DEBUG       = True                           # sauvegarde tous les événements dans fichier de log
VERBOSE     = False                         # print tous les événements sur la console
PATH        = ""                            # même répertoire 
LOGFILENAME = PATH + "mygreengarden.log"    # fichier de LOG par defaut
LOGLEVEL    = DEBUG 
FILEMODE    = 'w'
RELEASE     = "V1"
eventlog = []
id = 0
MAXSIZE = 1000

# LOG LEVEL = Critical, Error, Warning, Info, Debug, Not Set

logging.basicConfig(filename=LOGFILENAME, filemode=FILEMODE, level=LOGLEVEL, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info('---      LOGFILE      ------')
logging.info('---- { start logging } -----')


def LogEvent(message):

    """
     Ecriture de message dans fichier de LOG sur disque.
     Si VERBOSE est activé, copie sur console.
    """
    global id

    now = datetime.datetime.now()
    d = now.strftime("%d.%m ")
    t = now.strftime("%H:%M:%S")
    id = id + 1
    event = { "id" : id , "date" : d, "time" : t, "event" : message}
    #event = { "id" : id , "date" : d, "event" : message}
    eventlog.insert(0,event)

    l = len(eventlog)
    if l > MAXSIZE-1:
        eventlog.pop(l-1)
        
    if DEBUG: 
        logging.info(message)
    if VERBOSE :
        print(message)
    return

if __name__ == "__main__":

    LogEvent("test de LogEvent " + RELEASE)



