
#!/usr/bin/env python3
# -*- coding: utf-8 -*- 

# Auteur  : Patrick Pinard 
# Date    : 27.8.2023
# Objet   : Programme simple de gestion automatisée d'une serre avec deux zones d'arrosages
# Source  : app.py
# Version : 5  (mode simulation)

#   Clavier MAC :      
#  {} = "alt/option" + "(" ou ")"
#  [] = "alt/option" + "5" ou "6"
#   ~  = "alt/option" + n    s
#   \  = Alt + Maj + / 

SIMULATE = True 


import sys, os
#sys.path.extend([f'./{name}' for name in os.listdir(".") if os.path.isdir(name)])

from logging import DEBUG
import random
import psutil
from library.myLOGLib import LogEvent, eventlog
from library.myJSONLib import writeJSONtoFile, readJSONfromFile
from time import sleep
from library.mySensorsLib import Temperatures, Moisture, Anemometer, Humidity
from library.myActuatorsLib import WaterValve, SkyLight, Relay, Fan
from flask import Flask, render_template, request, jsonify, make_response, flash, redirect, url_for
from flask_cors import CORS
from flask_pwa import PWA
import os
from threading import Thread
if not SIMULATE: import library.SequentLib8relay
import datetime
import pickle
if not SIMULATE: from gpiozero import CPUTemperature
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from flask_login import LoginManager,login_required, current_user, login_user, logout_user




NAME                           = "MyGreenGarden "
RELEASE                        = "V5-SIMULATE"
AUTHOR                         = "Patrick Pinard © 2023"
PATH                           = ''
DATAFILE                       = PATH + 'mesures.dta'
DEBUG                          = False
USERNAME                       = ""


now = datetime.datetime.now()
date = now.strftime("%-d.%-m")  
time = now.strftime("%H:%M:%S")  
dateandtime = date + " à " + time 
LastRebootTime = dateandtime
LogEvent("Redémarrage le " + str(LastRebootTime))
LogEvent(NAME + RELEASE + AUTHOR)
LogEvent("Création des objets...")
if DEBUG : 
    LogEvent("Mode DEBUG activé.") 
else: 
    LogEvent("Mode DEBUG désactivé.")

# paramètres de configuration de la serre, des capteurs et actionneurs

INTERVAL                        = 900            # 15mn, temps en sec entre deux mesures complètes pour arosage et aération
MAX_RECORD_SIZE                 = 250            # Nombre de mesure gardée en mémoire
LIGHT_RELAY_ID                  = 6     
LIGHT_STATE                     = False   
LIGHT                           = Relay(LIGHT_RELAY_ID ,"Lampe LED")    

TEMP_MAX_THRESHOLD              = 30.0           # limite maximale de température (°C) de la Serre pour déclencher ventilation
TEMP_MIN_THRESHOLD              = 20.0           # limite minimale de température (°C) de la Serre pour stopper la ventilation
TEMPERATURES_SENSOR             = Temperatures() # sonde de mesure sous forme de liste des températures intérieure et extérieure
TEMPERATURE_INSIDE              = 0              # température interieure 
TEMPERATURE_OUTSIDE             = 0              # température exterieure 


HUMIDITY_ADC_CHANNEL            = 2             # ADC Channel 
#HUMIDITY_SENSOR                 = Humidity(HUMIDITY_ADC_CHANNEL)
HUMIDITYLIMIT                   = 80            # niveau d'humidité maximale de l'air
HUMIDITY                        = 0

ANEMOMETER_ADC_CHANNEL_ID       = 4             # ADC channel 
ANEMOMETER                      = Anemometer(ANEMOMETER_ADC_CHANNEL_ID)
WINDSPEED                       = 0.0   
WINDSPEEDLIMIT                  = 40  
WS                              = []      

FAN_RELAY_ID                    = 7
FAN                             = Fan(FAN_RELAY_ID)  # Ventilateur(s) 
FAN_STATE                       = False         # état de la ventilation (on/off)
FAN_ON_VALUE                    = 0             # valeur fictive pour visualisation de la ventilation sur graph temp.
FAN_OFF_VALUE                   = -10           # valeur fictive pour visualisation de la ventilation sur graph temp.
FAN_AUTO_MODE                   = False          # mode automatique d'aération avec ventilateurs

WATER_VALVE_RELAY_ID_ZONE_1     = 4             # n° du relai pour piloter la vanne d'eau dans la zone 1 
WATER_VALVE_RELAY_ID_ZONE_2     = 5             # n° du relai pour piloter la vanne d'eau dans la zone 1 
WATER_VALVE_ZONE_1              = WaterValve(WATER_VALVE_RELAY_ID_ZONE_1,"vanne d'eau zone 1")
WATER_VALVE_ZONE_2              = WaterValve(WATER_VALVE_RELAY_ID_ZONE_2,"vanne d'eau zone 2")
WATERING_ZONE_1                 = False
WATERING_ZONE_2                 = False
WATERING_AUTO_MODE              = False
WATERING_TIME_ZONE_1            = 300           # valeur par défaut de 5mn, temps d'arrosage dans la zone 1
WATERING_TIME_ZONE_2            = 300           # valeur par défaut de 5mn, temps d'arrosage dans la zone 2
WATERING_ON_VALUE               = -10           # valeur fictive pour visualisation vanne ouverte sur graph hum.
WATERING_OFF_VALUE              = -90           # valeur fictive pour visualisation vanne fermée sur graph hum.

MOISTURE_ADC_CHANNEL_ID_ZONE_1  = 0             # n° du canal du module ADC pour lecture humidité zone 1  (H1)
MOISTURE_ADC_CHANNEL_ID_ZONE_2  = 1             # n° du canal du module ADC pour lecture humidité zone 2  (H2)
MOISTURE_SENSOR_ZONE_1          = Moisture(1,"humidité sol zone 1", MOISTURE_ADC_CHANNEL_ID_ZONE_1)
MOISTURE_SENSOR_ZONE_2          = Moisture(2,"humidité sol zone 2", MOISTURE_ADC_CHANNEL_ID_ZONE_2)
MOISTURE_ZONE_1                 = 0             # niveau d'humidité au sol zone 1
MOISTURE_ZONE_2                 = 0             # niveau d'humidité au sol zone 2
MOISTURE_THRESHOLD_ZONE_1       = 55            # valeur par défaut, à ajuster en fonction de la terre en zone 1
MOISTURE_THRESHOLD_ZONE_2       = 55            # valeur par défaut, à ajuster en fonction de la terre en zone 2
MOISTURE_ZONE_1_TEXT            = ""
MOISTURE_ZONE_2_TEXT            = ""

WINDOW                         = SkyLight()     # lucarne de la serre pour aération
WINDOW_AUTO_MODE               = False           # mode automatique d'ouverture et fermeture de la lucarne
WINDOW_STATE                   = False          # état de la lucarne (ouverte : True; fermée : False)
WINDOW_OPEN_VALUE              = 0              # valeur fictive pour visualisation lucarne ouverte sur graph temp.
WINDOW_CLOSE_VALUE             = -10            # valeur fictive pour visualisation lucarne fermée sur graph temp.

CAMERA_STATE                   = False          # état du streaming camera (enclenché : True; arrêté : False)
CONFIG_FILENAME                = PATH + "config.json"  # fichier de sauvegarde des paramètres de configuration

TemplateData                   = {}
bootTime                       = ""

# dictionnaires des valeurs mesurées pour graphiques

LABELS                         = []
H0                             = []             
H1                             = [] 
H2                             = []
T1                             = [] 
T2                             = []
W1                             = []
W2                             = []
L                              = []
F                              = []


####### Création de l'APPLICATION FLASK ###############

app = Flask(__name__)
app.config['SECRET_KEY']='Th1s1ss3cr3t'
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///mygreengarden.db' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True 
CORS(app)
PWA(app)

###### AUTHENTIFICATION ################################

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


####### Création de la base de donnée et modèle ########

db = SQLAlchemy(app)   
LogEvent("Création de la base de données effectuée.")

class Users(db.Model):
    """
    """
    __tablename__ = 'user'

    name = db.Column(db.String, primary_key=True)
    password = db.Column(db.String)
    authenticated = db.Column(db.Boolean, default=False)

    def is_active(self):
        """True, as all users are active."""
        return True

    def get_id(self):
        """Return the username to satisfy Flask-Login's requirements."""
        return self.name

    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return self.authenticated

    def is_anonymous(self):
        """False, as anonymous users aren't supported."""
        return False

#from app import db
with app.app_context():
    db.create_all() 
    
LogEvent("Création du modèle de données utilisateurs (Users).")

@login_manager.user_loader
def user_loader(user_id):
    """
    """
    return Users.query.get(user_id)



@app.route('/signup', methods=['GET','POST'])
def signup():  
    #LogEvent("Demande d'enregistrement d'un utilisateur en cours...")
 
    name = request.form.get("name")
    password = request.form.get("password")

    user = Users.query.filter_by(name=name).first() 

    if user: # contrôle si utilisateur existe déjà 
        LogEvent("Nom d'utilisateur déjà existant !")
        flash("Nom d'utilisateur déjà existant !")
        return render_template('register.html') 

    if not name: # contrôle si nom utilisateur vide
        LogEvent("Nom d'utilisateur incorrect !")
        flash("Nom d'utilisateur est incorrect !")
        return render_template('register.html') 

    if not password: # contrôle si password vide
        LogEvent("Mot de passe incorrect !")
        flash("Mot de passe incorrect ! ")
        return render_template('register.html') 

    hashed_password = generate_password_hash(password, method='sha256')
    
    new_user = Users(name=name, password=hashed_password) 
    db.session.add(new_user)  
    db.session.commit()    

    LogEvent("Création de l'utilisateur : " + str(name))  

    return render_template('login.html') 


@app.route('/login', methods=['GET','POST'])  
def login(): 
    
    """Login de l'utilisateur et mise à jour de la db Users """

    global USERNAME

    name = request.form.get("name")
    password = request.form.get("password")
    flash("")
    if name == None or password == None or name =="" or password == "": 
        return render_template('login.html') 

    user = Users.query.filter_by(name=name).first()   

    if not user: # Si utilisateur n'existe pas -> ERREUR 
        LogEvent("Nom d'utilisateur inexistant ! ")
        flash("Ce nom d'utilisateur n'existe pas ! ")
        return render_template('login.html') 

        
    if check_password_hash(user.password, password):  
        user.authenticated = True
        USERNAME = name
        db.session.add(user)
        db.session.commit()
        login_user(user)
        LogEvent("Login de l'utilisateur : " + str(name))
        templateData = {'AppName'               : NAME, 
                    'Username'                  : USERNAME,
                    'AppRelease'                : RELEASE,
                    'AppAuthor'                 : AUTHOR,
                    'LastRebootTime'            : LastRebootTime,
                    'Window_auto_mode'          : WINDOW_AUTO_MODE,
                    'Window'                    : WINDOW_STATE,
                    'Fan_state'                 : FAN_STATE,
                    'Fan_auto_mode'             : FAN_AUTO_MODE,
                    'Light'                     : LIGHT_STATE,
                    'Watering_zone1'            : WATERING_ZONE_1, 
                    'Watering_zone2'            : WATERING_ZONE_2,
                    'Watering_auto_mode'        : WATERING_AUTO_MODE
                    }

        return render_template('actionneurs.html', **templateData) 

    LogEvent("Echec de l'authentification ! ")  

    return render_template('login.html') 

@app.route("/logout", methods=['GET','POST'])
@login_required
def logout():

    """Logout de l'utilisateur et mise à jour de la db Users """
    
    user = current_user
    user.authenticated = False
    db.session.add(user)
    db.session.commit()
    LogEvent("Logout de l'utilisateur : " + str(user.name))  
    logout_user()
    
    
    return render_template("logout.html")

@app.route('/users', methods=['GET'])
@login_required
def get_all_users():  

   """Liste les utilisateurs enregistrés avec leurs paramètres associés de la db Users """
   
   users = Users.query.all() 

   result = []   

   for user in users:   
       user_data = {}   
       user_data['name'] = user.name 
       user_data['password'] = user.password
       user_data['authenticated'] = user.authenticated
       
       result.append(user_data)   

   return jsonify({'users': result}) 



###### PWA files  #######################################

@app.route("/__service-worker.js", methods=['GET'])
def sw():
        
    return app.send_static_file('__service-worker.js') 

@app.route("/__manifest.json", methods=['GET'])
def man():
        
    return app.send_static_file('__manifest.json') 


####################   API   ############################

@app.route("/", methods=['GET'])
def main():
    '''
    chargement de la page principale. 
    '''
    
    return redirect(url_for('actionneurs'))


@app.route("/register", methods=['GET'])
def register():
    '''
    chargement de la page d'enregistrement utilisateur. 
    '''
    
    return render_template('register.html') 

@app.route("/actionneurs", methods=['GET'])
@login_required
def actionneurs():
    '''
    Ensemble des actionneurs 
    '''
    # Chargement de l'état des switches
    templateData = {'AppName'                   : NAME, 
                    'Username'                  : USERNAME,
                    'AppRelease'                : RELEASE,
                    'AppAuthor'                 : AUTHOR,
                    'LastRebootTime'            : LastRebootTime,
                    'Window_auto_mode'          : WINDOW_AUTO_MODE,
                    'Window'                    : WINDOW_STATE,
                    'Fan_state'                 : FAN_STATE,
                    'Fan_auto_mode'             : FAN_AUTO_MODE,
                    'Light'                     : LIGHT_STATE,
                    'Watering_zone1'            : WATERING_ZONE_1, 
                    'Watering_zone2'            : WATERING_ZONE_2,
                    'Watering_auto_mode'        : WATERING_AUTO_MODE
                    }

    return render_template('actionneurs.html', **templateData) 


@app.route("/parameters", methods=['GET'])
@login_required
def parameters():
    '''
    chargement de la page paramètres de configurations. 
    '''
    templateData = {'AppName'                   : NAME, 
                    'Username'                  : USERNAME,
                    'AppRelease'                : RELEASE,
                    'AppAuthor'                 : AUTHOR,
                    'LastRebootTime'            : LastRebootTime
                    }
    return render_template('parameters.html', **templateData)


@app.route("/shutdown", methods=['POST'])
@login_required
def shutdown():
    '''
    Shutdown Raspberry PI 4.
    '''
    if request.method == "POST":
        LogEvent("Sauvegarde des mesures sur disques en cours...")
        SaveData() 
        LogEvent("Shutdown ...  bye bye !")
        if not SIMULATE : os.system('sudo halt')
    return jsonify('Shutdown en cours...', 204)   
   
@app.route("/reboot", methods=['POST','GET'])
@login_required
def reboot():

    '''
    Reboot Raspberry PI 4
    '''
    if request.method == "POST":
        LogEvent("Sauvegarde des mesures sur disques en cours...")
        SaveData()
        LogEvent("Reboot ... see you soon !")
        if not SIMULATE : os.system('sudo reboot')
    return jsonify('Reboot en cours...', 204)
    
@app.route("/camera", methods=["GET","POST"])
@login_required
def camera():
    '''
        POST : activation/arrêt du streaming de la caméra sur l'interface web. 
        GET  : retourne l'état de CAMERA_STATE 
        True : streaming activé; False : streaming stoppé
        la caméra est sur un autre raspberry pi : picamera.ppdlab.ch
    '''


    global CAMERA_STATE

    if request.method == "POST":
        state = request.form.get('state')
        if state=="true":
            CAMERA_STATE = True
            LogEvent("Caméra activée.")
        elif state=="false":
            CAMERA_STATE = False
            LogEvent("Caméra désactivée.")
        else: 
            LogEvent('Erreur état de caméra.')
        return jsonify('Etat camera = ' + str(CAMERA_STATE), 204)

    if request.method == "GET":
        return render_template("camera.html", Camera = CAMERA_STATE)

@app.route("/light", methods=["GET","POST"])
@login_required
def light():
    '''
    POST : Allumer / Eteindre la lampe.
    Requête API sous forme : 
    http://mygreengarden.ppdlab.ch/light?state=1
    GET  : retourne si lumière allumée ou éteinte LIGHT_STATE
    Requête API sous forme : 
    http://mygreengarden.ppdlab.ch/light

    '''

    global LIGHT_STATE

    if request.method == "POST":
        state = request.form.get('state')
        
        if state=="true":
            LIGHT_STATE = True
            LIGHT.close()    #fermeture du relai pour allumer la lampe
            LogEvent("Lampe allumée.")
        elif state=="false":
            LIGHT_STATE = False
            LIGHT.open()    #ouverture du relai pour allumer la lampe
            LogEvent("Lampe éteinte.")
        else:
            LogEvent("Erreur : état de la lampe indéfini.")
        return jsonify('Etat de la lampe : ' + str(LIGHT_STATE), 204)

    if request.method == "GET":
        data = {'Light':LIGHT_STATE}
        return jsonify(data)

@app.route('/windspeed', methods=['GET'])
@login_required
def windspeed():
    '''
    Retourne la vitesse du vent en km/h
    '''
    global WINDSPEED 

    if request.method == "GET":
        WINDSPEED  = ANEMOMETER .read() 
        data = {'WINDSPEED': WINDSPEED }
        LogEvent('Mesure de la vitesse du vent [km/h] : ' + str(WINDSPEED))
        return jsonify(data)  
    


@app.route("/window/auto", methods=['GET','POST'])
@login_required
def window_auto_mode():
    '''
    POST : Activation de l'aération automatique de la serre.
    GET  : retourne la valeur de WINDOW_AUTO_MODE
    Requête API sous forme : 
    http://mygreengarden.ppdlab.ch/window/auto?state=1
    '''
    
    global WINDOW_AUTO_MODE
   
    if request.method == "POST":
        state = request.form.get('state')       
        if state=="true":
            WINDOW_AUTO_MODE = True
            text = "Ventilation automatique activée."
        elif state=="false":
            WINDOW_AUTO_MODE = False
            text = "Ventilation automatique désactivée."
        else: 
            text= "Erreur : état ventilation automatique indéfini."
        LogEvent(text)
        return jsonify('Etat du mode automatique de la lucarne : ' + str(WINDOW_AUTO_MODE), 204) 

    if request.method == "GET":
        data = {'WINDOW_AUTO_MODE': WINDOW_AUTO_MODE}
        return jsonify(data)

@app.route("/window", methods=["GET","POST"])
@login_required
def window():
    '''
    Ouvrir ou Fermer la lucarne.
    Requête API sous forme : 
    http://mygreengarden.ppdlab.ch/window?state=1
    '''

    global WINDOW_STATE

    if request.method == "POST":
        state = request.form.get('state')
        if state=="true":
            WINDOW_STATE = True
            WINDOW.open()
            SaveState()
        elif state=="false":
            WINDOW_STATE = False
            WINDOW.close()
            SaveState()
        else:
            LogEvent("Erreur : état lucarne indéfini.")
        return jsonify('Etat de la lucarne : ' + str(WINDOW_STATE), 204)

    if request.method == "GET":
        data = {'WINDOW_STATE':WINDOW_STATE}
        return jsonify(data)


@app.route("/fan", methods=["GET","POST"])
@login_required
def fan():
    '''
    Activation ou arrêt de la ventilation.
    Requête API sous forme : 
    http://mygreengarden.ppdlab.ch/fan?state=1
    '''

    global FAN_STATE

    if request.method == "POST":
        state = request.form.get('state')
        if state=="true":
            FAN_STATE = True
            FAN.on()   # activer les ventilateurs
            SaveState()
        elif state=="false":
            FAN_STATE = False
            FAN.off()  # arrêt des ventilateurs 
            SaveState()
        else:
            LogEvent("Erreur : état ventilateurs indéfini.")
        return jsonify('Etat des ventilateurs : ' + str(FAN_STATE), 204)

    if request.method == "GET":
        data = {'FAN_STATE': FAN_STATE}
        return jsonify(data)

@app.route("/fan/auto", methods=['GET','POST'])
@login_required
def fan_auto_mode():
    '''
    POST : Activation de l'aération automatique de la serre via ventilateurs.
    GET  : retourne la valeur de FAN_AUTO_MODE
    Requête API sous forme : 
    http://mygreengarden.ppdlab.ch/fan/auto?state=1
    '''
    
    global FAN_AUTO_MODE
   
    if request.method == "POST":
        state = request.form.get('state')       
        if state=="true":
            FAN_AUTO_MODE = True
            text = "Activation mode automatique des ventilateurs."
        elif state=="false":
            FAN_AUTO_MODE = False
            text = "Mode automatique des ventilateurs désactivé."
        else: 
            text= "Erreur : état du mode des ventilateurs indéfini."
        LogEvent(text)
        return jsonify('Etat du mode automatique des ventilateurs : ' + str(FAN_AUTO_MODE), 204) 

    if request.method == "GET":
        data = {'FAN_AUTO_MODE': FAN_AUTO_MODE}
        return jsonify(data)

@app.route("/watering/auto", methods=["GET","POST"])
@login_required
def watering_auto_mode():
    '''
    POST : Activer ou Désactiver l'arrosage automatique d'une zone
    Requête API sous forme : 
    http://mygreengarden.ppdlab.ch/watering/auto?zone=1&state=1
    GET  : retourne l'état de l'arrosage automatique dans les zones
    Requête API sous forme : 
    http://mygreengarden.ppdlab.ch/watering/auto
    '''

    global WATERING_AUTO_MODE

    if request.method == "POST":
        state = request.form.get('state')
        if state=="true":
            WATERING_AUTO_MODE = True
            LogEvent("Arrosage automatique activé.")
        elif state=="false":
            WATERING_AUTO_MODE = False
            LogEvent("Arrosage automatique désactivé.")
        else:
            LogEvent("Erreur : état arrosage automatique indéfini.")
        return jsonify("Etat du mode automatique de l'arrosage : " + str(WATERING_AUTO_MODE), 204) 

    if request.method == "GET":
        data = {'WATERING_AUTO_MODE': WATERING_AUTO_MODE}
        return jsonify(data)

@app.route("/watering", methods=["GET","POST"])
@login_required
def watering():
    '''
    POST : Activer ou Désactiver l'arrosage automatique d'une zone
    Requête API sous forme : 
    http://mygreengarden.ppdlab.ch/watering/auto?zone=1&state=1
    GET  : retourne l'état de l'arrosage automatique dans les zones
    Requête API sous forme : 
    http://mygreengarden.ppdlab.ch/watering/auto
    '''

    global WATERING_ZONE_1, WATERING_ZONE_2, WATERING_AUTO_MODE

    if not WATERING_AUTO_MODE:

        if request.method == "POST":

            zone = request.form.get('zone')
            state = request.form.get('state')
            if zone == "1":
                if state=="true":
                    WATERING_ZONE_1 = True
                    LogEvent("Arrosage zone 1 activé.")
                    WATER_VALVE_ZONE_1.open()
                    
                else:
                    WATERING_ZONE_1 = False
                    LogEvent("Arrosage zone 1 désactivé.")
                    WATER_VALVE_ZONE_1.close()
                    
            elif zone == "2":
                if state=="true":
                    WATERING_ZONE_2 = True
                    LogEvent("Arrosage zone 2 activé.")
                    WATER_VALVE_ZONE_2.open()
                    
                else:
                    WATERING_ZONE_2 = False
                    LogEvent("Arrosage zone 2 désactivé.")
                    WATER_VALVE_ZONE_2.close()
                    
            SaveState()

            return jsonify("Etat de l'arrosage dans la " + str(zone) + " : " + str(state), 204) 
    else:
        LogEvent("Arrosage automatique activé ! pas d'actions manuelle possible.")
        return ('', 204)
        
    if request.method == "GET":
        data = {'WATERING_ZONE_1': WATERING_ZONE_1,
                'WATERING_ZONE_2' : WATERING_ZONE_2}
        return jsonify(data) 

@app.route("/getallvalues", methods=['GET'])
@login_required
def getallvalues():
    '''
    Retourne les valeurs des mesure des capteurs d'humidité & températures 
    Requête API sous forme : 
    http://mygreengarden.ppdlab.ch/values
    http://mygreengarden.ppdlab.ch:81/manifest.json

    '''
    global HUMIDITY, MOISTURE_ZONE_1, MOISTURE_ZONE_2, TEMPERATURE_OUTSIDE, TEMPERATURE_INSIDE, WINDSPEED, eventlog, INTERVAL

    if request.method == "GET":

        ReadHumidityWindSpeedAndTemperatures()
        now = datetime.datetime.now()
        date = now.strftime("%-d.%-m.%-Y")  
        time = now.strftime("%H:%M:%S")  
        dateandtime = date + "  " + time 
        CPU = CPUTemperature()
        TCPU = round(CPU.temperature,2)
        CPU_usage = psutil.cpu_percent()
       
        data = {
                "Tin"                       : TEMPERATURE_INSIDE, 
                "Tout"                      : TEMPERATURE_OUTSIDE, 
                "H1"                        : MOISTURE_ZONE_1, 
                "H2"                        : MOISTURE_ZONE_2, 
                "H1TEXT"                    : MOISTURE_SENSOR_ZONE_1.text, 
                "H2TEXT"                    : MOISTURE_SENSOR_ZONE_2.text, 
                "TCPU"                      : TCPU,
                "CPU_usage"                 : CPU_usage,
                "WINDSPEED"                 : WINDSPEED,
                "LastRefreshTime"           : dateandtime,
                'LastRebootTime'            : LastRebootTime,
                } 
        
        if DEBUG : LogEvent("DEBUG - Rafraichissement des données pour affichage principal ")

        SaveState()

        return jsonify(data)

@app.route("/graph", methods=['GET'])
@login_required
def graph():
    '''
    Affichage des graphiques des mesures d'humidité, températures et vitesse du vent.
    Requête API sous forme : http://mygreengarden.ppdlab.ch/graph
    '''

    templateData = {'AppName'                   : NAME, 
                    'Username'                  : USERNAME,
                    'AppRelease'                : RELEASE,
                    'AppAuthor'                 : AUTHOR,
                    'LastRebootTime'            : LastRebootTime,
                    'labels'                    : LABELS, 
                    'H0'                        : H0, 
                    'H1'                        : H1, 
                    'H2'                        : H2,
                    'W1'                        : W1, 
                    'W2'                        : W2, 
                    'L'                         : L,
                    'T1'                        : T1,
                    'T2'                        : T2,
                    'WS'                        : WS,
                    'F'                         : F
                    }

    if request.method == "GET":
        return render_template("graph.html", **templateData)


@app.route("/capteurs", methods=['GET'])
@login_required
def capteurs():
    '''
    Affichage des mesures d'humidité, températures.
    Requête API sous forme : http://mygreengarden.ppdlab.ch/capteurs

    '''

    if request.method == "GET":
        
        now = datetime.datetime.now()
        date = now.strftime("%-d.%-m.%-Y")  
        time = now.strftime("%H:%M:%S")  
        LastRefreshTime = date + "  " + time 
        if not SIMULATE : 
            CPU = CPUTemperature()
            TCPU = round(CPU.temperature,2)
            CPU_usage = psutil.cpu_percent()
        else:
            CPU_usage = random.randint(0,30)
            TCPU = random.randint(30,70)
        
        ReadHumidityWindSpeedAndTemperatures()

        templateData = {'AppName'                   : NAME, 
                        'Username'                  : USERNAME,
                        'AppRelease'                : RELEASE,
                        'AppAuthor'                 : AUTHOR,
                        'LastRebootTime'            : LastRebootTime,
                        'LastRefreshTime'           : LastRefreshTime,
                        'Tin'                       : TEMPERATURE_INSIDE,
                        'Tout'                      : TEMPERATURE_OUTSIDE,
                        'Tmax'                      : TEMP_MAX_THRESHOLD,
                        'H1'                        : MOISTURE_ZONE_1,
                        'H2'                        : MOISTURE_ZONE_2,
                        'H1_text'                   : MOISTURE_ZONE_1_TEXT,
                        'H2_text'                   : MOISTURE_ZONE_2_TEXT,
                        'Humidity'                  : HUMIDITY,
                        "TCPU"                      : TCPU,
                        "CPU_usage"                 : CPU_usage,
                        "WINDSPEED"                : WINDSPEED
                        }

        return render_template("capteurs.html", **templateData)

@app.route("/events", methods=['GET'])
@login_required
def events():
    '''
    Affichage de la page des événements enregistrés.
    Requête API sous forme : http://mygreengarden.ppdlab.ch/events

    '''
    global eventlog
    
    if request.method == "GET":   

        templateData = {'AppName'               : NAME, 
                    'Username'                  : USERNAME,
                    'AppRelease'                : RELEASE,
                    'AppAuthor'                 : AUTHOR,
                    'LastRebootTime'            : LastRebootTime,
                    'eventlog'                  : eventlog
                    }
        return render_template('events.html', **templateData)            

@app.route("/saveparameters", methods=['POST'])
@login_required
def saveparameters():
    '''
    Sauvegarde des paramètres de configuration de gestion de la serre.

    '''
    global MOISTURE_THRESHOLD_ZONE_1, MOISTURE_THRESHOLD_ZONE_2
    global TEMP_MAX_THRESHOLD, TEMP_MIN_THRESHOLD
    global WATERING_TIME_ZONE_1,WATERING_TIME_ZONE_2   
    global INTERVAL, ALERT_EMAIL

    
    if request.method == "POST":

        TEMP_MAX_THRESHOLD          = int(request.form.get("TempMaxThreshold"))
        TEMP_MIN_THRESHOLD          = int(request.form.get("TempMinThreshold"))
        MOISTURE_THRESHOLD_ZONE_1   = int(request.form.get("HumidityLevelZone1"))
        MOISTURE_THRESHOLD_ZONE_2   = int(request.form.get("HumidityLevelZone2"))
        WATERING_TIME_ZONE_1        = int(request.form.get("WateringTimeZone1"))
        WATERING_TIME_ZONE_2        = int(request.form.get("WateringTimeZone2"))
        

        data = {'HumidityLevelZone1' : MOISTURE_THRESHOLD_ZONE_1, 
                'HumidityLevelZone2' : MOISTURE_THRESHOLD_ZONE_2,
                'TempMaxThreshold'   : TEMP_MAX_THRESHOLD,
                'TempMinThreshold'   : TEMP_MIN_THRESHOLD, 
                'WateringTimeZone1'  : WATERING_TIME_ZONE_1,
                'WateringTimeZone2'  : WATERING_TIME_ZONE_2,
                
                }

        SaveParametersToFile()

        if DEBUG : 
            LogEvent("DEBUG - Sauvegarde des paramètres de configurations : " + str(data))

    return render_template('parameters.html') 


@app.route("/getparameters", methods=['GET'])
@login_required
def getparameters():
    '''
    Retourne la liste des paramètres de gestion de la serre.
    Requête API sous forme : http://mygreengarden.ppdlab.ch/getparameters

    '''
    global MOISTURE_THRESHOLD_ZONE_1, MOISTURE_THRESHOLD_ZONE_2
    global TEMP_MAX_THRESHOLD, TEMP_MIN_THRESHOLD
    global WATERING_TIME_ZONE_1,WATERING_TIME_ZONE_2     
   

    if request.method == "GET": 
        data = {'HumidityLevelZone1' : int(MOISTURE_THRESHOLD_ZONE_1), 
                'HumidityLevelZone2' : int(MOISTURE_THRESHOLD_ZONE_2),
                'TempMinThreshold'   : int(TEMP_MIN_THRESHOLD),
                'TempMaxThreshold'   : int(TEMP_MAX_THRESHOLD), 
                'WateringTimeZone1'  : int(WATERING_TIME_ZONE_1),
                'WateringTimeZone2'  : int(WATERING_TIME_ZONE_2),
                
                }
        
        if DEBUG : LogEvent("DEBUG - Envoi des paramètres de configurations : " + str(data))

        return jsonify(data)


####################   fin API   ###########################



def SaveParametersToFile():
    '''
    Sauvegarde des paramètres de gestion de la serre dans un fichier : CONFIG_FILENAME.
    '''
    global MOISTURE_THRESHOLD_ZONE_1, MOISTURE_THRESHOLD_ZONE_2
    global TEMP_MAX_THRESHOLD, TEMP_MIN_THRESHOLD
    global WATERING_TIME_ZONE_1,WATERING_TIME_ZONE_2     
    global WINDSPEEDLIMIT, HUMIDITYLIMIT, INTERVAL
    
    data = {'TEMP_MAX_THRESHOLD'        : TEMP_MAX_THRESHOLD,
            'TEMP_MIN_THRESHOLD'        : TEMP_MIN_THRESHOLD, 
            'MOISTURE_THRESHOLD_ZONE_1' : MOISTURE_THRESHOLD_ZONE_1, 
            'MOISTURE_THRESHOLD_ZONE_2' : MOISTURE_THRESHOLD_ZONE_2,
            'WATERING_TIME_ZONE_1'      : WATERING_TIME_ZONE_1,
            'WATERING_TIME_ZONE_2'      : WATERING_TIME_ZONE_2,
            'WINDSPEEDLIMIT'            : WINDSPEEDLIMIT,
            'HUMIDITYLIMIT'             : HUMIDITYLIMIT,
            }

    if writeJSONtoFile(CONFIG_FILENAME, data):
        LogEvent("Sauvegarde des paramètres sur fichier : " + CONFIG_FILENAME)
    else: 
        LogEvent("Erreur de sauvegarde des paramètres sur fichier : " + CONFIG_FILENAME)

    return
    
def LoadParametersFromFile():
    '''
    Chargement des paramètres de gestion de la serre depuis fichier : CONFIG_FILENAME.
    '''
    global MOISTURE_THRESHOLD_ZONE_1, MOISTURE_THRESHOLD_ZONE_2
    global TEMP_MAX_THRESHOLD, TEMP_MIN_THRESHOLD
    global WATERING_TIME_ZONE_1,WATERING_TIME_ZONE_2     
    global WINDSPEEDLIMIT, HUMIDITYLIMIT
    
    data = []
    
    validConfig, data = readJSONfromFile(CONFIG_FILENAME)

    if validConfig :     
        LogEvent("Chargement des paramètres de configuration de la serre depuis le fichier : " + CONFIG_FILENAME)
        
        LogEvent("TEMP_MAX_THRESOLD = " + str(data['TEMP_MAX_THRESHOLD']))
        LogEvent("TEMP_MIN_THRESOLD = " + str(data['TEMP_MIN_THRESHOLD']))
        LogEvent("MOISTURE_THRESHOLD_ZONE_1 = " + str(data['MOISTURE_THRESHOLD_ZONE_1']))
        LogEvent("MOISTURE_THRESHOLD_ZONE_2 = " + str(data['MOISTURE_THRESHOLD_ZONE_2']))
        LogEvent("WATERING_TIME_ZONE_1 = " + str(data['WATERING_TIME_ZONE_1']))
        LogEvent("WATERING_TIME_ZONE_2 = " + str(data['WATERING_TIME_ZONE_2']))
        LogEvent("WINDSPEEDLIMIT = " + str(data['WINDSPEEDLIMIT']))
        LogEvent("HUMIDITYLIMIT = " + str(data['HUMIDITYLIMIT']))

        TEMP_MAX_THRESHOLD          = (data['TEMP_MAX_THRESHOLD'])
        TEMP_MIN_THRESHOLD          = (data['TEMP_MIN_THRESHOLD'])
        MOISTURE_THRESHOLD_ZONE_1   = (data['MOISTURE_THRESHOLD_ZONE_1'])
        MOISTURE_THRESHOLD_ZONE_2   = (data['MOISTURE_THRESHOLD_ZONE_2'])
        WATERING_TIME_ZONE_1        = (data['WATERING_TIME_ZONE_1'])
        WATERING_TIME_ZONE_2        = (data['WATERING_TIME_ZONE_2'])
        WINDSPEEDLIMIT              = (data['WINDSPEEDLIMIT'])
        HUMIDITYLIMIT               = (data['HUMIDITYLIMIT'])
    else: 
        LogEvent("Fichier inexistant, chargement des paramètres de configuration par défaut.")

    return

def ReadHumidityWindSpeedAndTemperatures():
    """
        Lecture des capteurs d'humidités et de températures ainsi que vitesse du vent.
        Le capteur d'humidité au sol n'est pas encore connecté.
    """

    global HUMIDITY, MOISTURE_ZONE_1, MOISTURE_ZONE_2, TEMPERATURE_INSIDE, TEMPERATURE_OUTSIDE, WINDSPEED

    
    MOISTURE_ZONE_1 = MOISTURE_SENSOR_ZONE_1.read()  
    MOISTURE_ZONE_2 = MOISTURE_SENSOR_ZONE_2.read()
    t = TEMPERATURES_SENSOR.read()
    TEMPERATURE_INSIDE = t[0]  # température interieure en °C
    TEMPERATURE_OUTSIDE = t[1]  # température extérieure en °C 
    #HUMIDITY = HUMIDITY_SENSOR.read(TEMPERATURE_INSIDE)
    WINDSPEED = ANEMOMETER.read() 

    if DEBUG : LogEvent("DEBUG - Lecture des capteurs effectuée.")
    
    return 

def SaveState():

    global H0, H1, H2, HUMIDITY, MOISTURE_ZONE_1, MOISTURE_ZONE_2, W1, W2, WATERING_ZONE_1, WATERING_ZONE_2
    global T1, T2, TEMPERATURE_INSIDE, TEMPERATURE_OUTSIDE, L, WINDOW_STATE
    global WINDSPEED, WS
    global FAN_STATE, F
    global LABELS


    now = datetime.datetime.now()
    date = now.strftime("%-d.%-m")  
    time = now.strftime("%H:%M:%S")  
    dateandtime = date + " " + time 
    
    LABELS.append(dateandtime)
 
    H0.append(HUMIDITY)
    H1.append(MOISTURE_ZONE_1)
    H2.append(MOISTURE_ZONE_2)
    T1.append(TEMPERATURE_INSIDE)
    T2.append(TEMPERATURE_OUTSIDE)
    WS.append(WINDSPEED)
    
    if FAN_STATE :
        F.append(FAN_ON_VALUE)
    else:
        F.append(FAN_OFF_VALUE)

    if WINDOW_STATE :
        L.append(WINDOW_OPEN_VALUE)
    else:
        L.append(WINDOW_CLOSE_VALUE)

    if WATERING_ZONE_1:
        W1.append(WATERING_ON_VALUE)
    else:
        W1.append(WATERING_OFF_VALUE)

    if WATERING_ZONE_2:
        W2.append(WATERING_ON_VALUE)
    else:
        W2.append(WATERING_OFF_VALUE)
    
    l = len(LABELS)
    
    if l > MAX_RECORD_SIZE-1:
                    
        LABELS.pop(0)
        H0.pop(0)
        H1.pop(0)
        H2.pop(0)
        T1.pop(0)
        T2.pop(0)
        WS.pop(0)
        F.pop(0)
        L.pop(0)
        W1.pop(0)
        W2.pop(0)

    return 

def SaveData():

    # Sauvegarde des données enregistrées sur disque

    global H0, H1, H2, HUMIDITY, MOISTURE_ZONE_1, MOISTURE_ZONE_2, W1, W2, WATERING_ZONE_1, WATERING_ZONE_2
    global T1, T2, TEMPERATURE_INSIDE, TEMPERATURE_OUTSIDE, L, WINDOW_STATE
    global WINDSPEED, WS
    global FAN_STATE, F
    global LABELS
    
    #LogEvent("Sauvegarde sur disque des mesures enregistrées en cours ....")
    
    try: 
        with open(DATAFILE , 'wb') as file:
            pickle.dump(H0, file)
            pickle.dump(H1, file)
            pickle.dump(H2, file)
            pickle.dump(T1, file)
            pickle.dump(T2, file)
            pickle.dump(W1, file)
            pickle.dump(W2, file)
            pickle.dump(L, file)
            pickle.dump(WS, file)
            pickle.dump(F, file)
            pickle.dump(LABELS, file)

    except IOError as e:
        LogEvent("Erreur: {0}".format(e))

    LogEvent("Sauvegarde des mesures enregistrées terminée.")
    
def LoadData():

    # Chargement des données enregistrées sur disque 

    global H0, H1, H2, HUMIDITY, MOISTURE_ZONE_1, MOISTURE_ZONE_2, W1, W2, WATERING_ZONE_1, WATERING_ZONE_2
    global T1, T2, TEMPERATURE_INSIDE, TEMPERATURE_OUTSIDE, L, WINDOW_STATE
    global WINDSPEED, WS
    global FAN_STATE, F
    global LABELS

    if os.path.isfile(DATAFILE ):
        LogEvent("Fichier de sauvegarde des mesures : " + DATAFILE + " disponible." )
    
        try: 
            with open(DATAFILE , 'rb') as file:
                H0 = pickle.load(file)
                H1 = pickle.load(file)
                H2 = pickle.load(file)
                T1 = pickle.load(file)
                T2 = pickle.load(file)
                W1 = pickle.load(file)
                W2 = pickle.load(file)
                L = pickle.load(file)
                WS = pickle.load(file)
                F = pickle.load(file)
                LABELS = pickle.load(file)

        except OSError as err:
            LogEvent("Erreur: {0}".format(err))
       
        LogEvent("Chargement des mesures sauvegardées terminé." )
    else:
        LogEvent("Fichier de sauvegarde des mesures inexistant." )
    return   



def WateringAndAerate():
    """
    Mesures des différents capteurs, ventilation et arrosage en fonction 
    des paramètres de chacune des zones.
    """
    global MOISTURE_ZONE_1, MOISTURE_ZONE_2, WATERING_ZONE_1, WATERING_ZONE_2
    global WATERING_TIME_ZONE_1, WATERING_TIME_ZONE_2
    global MOISTURE_THRESHOLD_ZONE_1, MOISTURE_THRESHOLD_ZONE_2
    global WATERING_AUTO_MODE
    global TEMP_MAX_THRESHOLD, TEMP_MIN_THRESHOLD, TEMPERATURE_INSIDE, TEMPERATURE_OUTSIDE, T1, T2 
    global L, WINDOW_STATE, WINDOW_AUTO_MODE
    global FAN_STATE, FAN_AUTO_MODE
    global WINDSPEED, WINDSPEEDLIMIT, count
    global HUMIDITY, HUMIDITYLIMIT
   
   
    if DEBUG : LogEvent("DEBUG - Lecture des capteurs en cours...")

    if not SIMULATE : 
        CPU = CPUTemperature()
        TCPU = round(CPU.temperature,2)
        CPU_usage = psutil.cpu_percent()
    else:
        CPU_usage = random.randint(0,30)
        TCPU = random.randint(30,70)
        

    ReadHumidityWindSpeedAndTemperatures()

    LogEvent("Mesure de l'humidité dans la zone 1 : " + str(MOISTURE_ZONE_1) + " [% HR]")
    LogEvent("Mesure de l'humidité dans la zone 2 : " + str(MOISTURE_ZONE_2) + " [% HR]")
    LogEvent("Mesure de la température extérieure : " + str(TEMPERATURE_OUTSIDE) + " [°C]") 
    LogEvent("Mesure de la température intérieure : " + str(TEMPERATURE_INSIDE) + " [°C]") 
    LogEvent("Mesure de la vitesse du vent        : " + str(WINDSPEED) + " [km/h]") 
    #LogEvent("Mesure de l'humidité de l'air      : " + str(HUMIDITY) + " [% HR]")   
    LogEvent("Température CPU du Raspberry Pi 4   : " + str(TCPU)+ " [°C]")
    LogEvent("Utilisation CPU du Raspberry Pi 4   : " + str(CPU_usage)+ " [%]")

    if FAN_AUTO_MODE : 
        if (TEMPERATURE_INSIDE > TEMP_MAX_THRESHOLD) :
            # si température intérieure > temp max, alors activation des ventilateurs
            if not FAN_STATE:
                LogEvent("Température intérieure supérieure au maximum de " + str(TEMP_MAX_THRESHOLD) + " [°C]. Activation des ventilateurs.")
                FAN.on()  # activer les ventilateurs
                FAN_STATE = True
            else:
                LogEvent("Température intérieure supérieure au maximum de " + str(TEMP_MAX_THRESHOLD) + " [°C]. Ventilateurs enclenchés.")

        if (TEMPERATURE_INSIDE < TEMP_MIN_THRESHOLD) :
            if FAN_STATE:
                LogEvent("Température intérieure inférieure au minimum de " + str(TEMP_MIN_THRESHOLD) + " [°C]. Arrêt des ventilateurs.")
                FAN.off() # arrêt des ventilateurs
                FAN_STATE = False
            else:
                LogEvent("Température intérieure inférieure au minimum de " + str(TEMP_MIN_THRESHOLD) + " [°C].")
    else:
        if TEMPERATURE_INSIDE > TEMP_MAX_THRESHOLD:
            LogEvent("ATTENTION : Température élevée.  Mode manuel enclenché pour ventilateurs. Veuillez aérer la serre manuellement svp !") 
        else:
            LogEvent("Température intérieure dans les limites définies. Pas de changements nécessaires.") 

    if WINDSPEED>WINDSPEEDLIMIT:
        count = count + 1
        if count>2 : 
            if WINDOW_STATE:
                LogEvent("ATTENTION : Vitesse du vent : " + str(WINDSPEED) + ". Supérieur à la limite autorisée de : "  + str(WINDSPEEDLIMIT) + ". Fermeture Lucarne svp.")
                #WINDOW.close()   # verin pas encore installé
            else:
                LogEvent("ATTENTION : Vitesse du vent : " + str(WINDSPEED) + ". Supérieur à la limite autorisée de : "  + str(WINDSPEEDLIMIT) + ". Lucarne déjà fermée.")
    else:
        count = 0

    if WATERING_AUTO_MODE:
        if MOISTURE_ZONE_1 < int(MOISTURE_THRESHOLD_ZONE_1):
            LogEvent("Humidité relative en zone 1 est inférieure à valeur minimale de " + str(MOISTURE_THRESHOLD_ZONE_1))
            LogEvent("Début de la période d'arrosage dans zone 1 pendant : " + str(WATERING_TIME_ZONE_1) + " sec." )
            WATERING_ZONE_1 = True 
            SaveState()
            WATER_VALVE_ZONE_1.open()   # pour démarrer l'arrosage pendant WATERING_TIME
            sleep(WATERING_TIME_ZONE_1)
            LogEvent("Fin de la période d'arrosage de la zone 1.")
            WATER_VALVE_ZONE_1.close()    # pour arrêt de l'arrosage
            WATERING_ZONE_1 = False
           
        else:
            LogEvent("Humidité relative en zone 1 est supérieure à valeur minimale. Pas d'arrosage.") 
            WATERING_ZONE_1 = False
            

        if MOISTURE_ZONE_2 < int(MOISTURE_THRESHOLD_ZONE_2):
            LogEvent("Humidité relative en zone 2 est inférieure à valeur minimale de " + str(MOISTURE_THRESHOLD_ZONE_2))
            LogEvent("Début de la période d'arrosage dans zone 2 pendant : " + str(WATERING_TIME_ZONE_1) + " sec." )
            WATERING_ZONE_2 = True
            SaveState()
            WATER_VALVE_ZONE_2.open()   # pour démarrer l'arrosage pendant WATERING_TIME
            sleep(WATERING_TIME_ZONE_2)
            LogEvent("Fin de la période d'arrosage de la zone 2.")
            WATER_VALVE_ZONE_2.close()    # pour arrêt de l'arrosage
            WATERING_ZONE_2 = False
            
        else:
            LogEvent("Humidité relative en zone 2 est supérieure à valeur minimale. Pas d'arrosage.") 
            WATERING_ZONE_2 = False
           
    else:
        if MOISTURE_ZONE_1 < int(MOISTURE_THRESHOLD_ZONE_1) or MOISTURE_ZONE_2 < int(MOISTURE_THRESHOLD_ZONE_2):
            LogEvent("ATTENTION : Arrosage automatique déclenché. Veuillez arroser manuellement les zones 1 & 2.")
            
    SaveState()
    
    return   


    
##### Threads pour lancement de Flask et des mesures récurrentes #######


class FlaskApp (Thread):
   def __init__(self, threadID, name):
      Thread.__init__(self)
      self.threadID = threadID
      self.name = name
   def run(self):
      LogEvent("FlaskApp Thread started") 
      try:
        #app.run(host='0.0.0.0', port = 81, debug=False, ssl_context=('cert.pem', 'key.pem')) 
        app.run(host='0.0.0.0', port = 81, debug=False)      
      except OSError as err:
        LogEvent("ERREUR : thread FlaskApp ! Message : " + str(err))


class Loop (Thread):
    
    def __init__(self, threadID, name):
      Thread.__init__(self)
      self.threadID = threadID
      self.name = name

    def run(self):
        
        global INTERVAL

        LogEvent("Loop Thread started") 
        id = 0
        while True : 
            try:
                while True: 
                    LogEvent(" *** Thread Loop id = " + str(id) + " ***" )
                    id = id + 1
                    WateringAndAerate()
                    SaveData()
                    sleep(INTERVAL)  # 15 mn entre chaque mesure

            except OSError as err:
                LogEvent("ERREUR : thread Loop ! Message : " + str(err))




if __name__ == '__main__': 
    
    
    app.secret_key = os.urandom(12)
    count = 0
    LogEvent("Remise à zéro de tous les relais.")
    if not SIMULATE: SequentLib8relay.set_all(0,0)
    LoadParametersFromFile() 
    LogEvent("Mesure automatique des capteurs toutes les " + str(INTERVAL) + " secondes.")
    LoadData()
    

    ReadHumidityWindSpeedAndTemperatures()

    thread1 = FlaskApp(1, "FlaskApp")
    thread2 = Loop(2, "Loop")
    
    thread1.start()
    thread2.start()
    
    thread1.join()
    thread2.join()
   
    
    
    
  
    
    



    

    
   





