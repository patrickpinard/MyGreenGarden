# MyGreenGarden V3.0
Dernière mise à jour le 4 juin 2022. 
APP pour mobile en BootStrap 5.

MyGreenGarden est un projet qui consiste à mettre en œuvre une serre pour la culture de légumes. La serre est pilotée par un ensemble de capteurs et actionneurs connectés à un Raspberry PI 4. Une interface WEB permet de gérer et contrôler la serre à distance depuis n’importe où via un VPN privé.

![](/images/greengarden.png)

## Objectifs

Ce projet a comme objectifs de :

    1.	Comprendre les bases de la programmation en Phython, Flask, Ajax, Bootstrap, POO, etc.
    2.	Mettre en œuvre un ensemble de capteurs et actionneurs pour piloter la serre de manière intelligente.
    3.	Faire pousser des légumes BIO !
    4.	S’amuser et apprendre

## La serre 

Les fondations (...un peu trop large, prévoir 15-20cm maximum):
 
![](/images/serre4.jpg)

Construction de la serre. Mise en place de l'eau, électricité et accès internet : 

![](/images/serre0.jpg)

Test de l'installation de pilotage des vannes d'eau et étanchéité du tableau électrique :

![](/images/serre3.jpg)

Les premières plantations et l'installation informatique presque terminée (reste encore les ventilateurs)

![](/images/serre1.jpg)

## les 3 zones de la serre

La serre sera organisée en 3 zones distinctes pour permettre un contrôle différencié de l’arrosage en fonction de l’humidité du sol selon les légumes. 

Les zones 1 & 2 seront automatisées. La zone 3 ne sera pas automatisée, uniquement arrosage manuelle.

![](/images/zones.png)

Quels légumes sous serre et à quelles conditions ?

https://www.gammvert.fr/conseils/conseils-de-jardinage/cultiver-des-legumes-sous-serre


## Quels valeurs pour la température, l'hydrométrie, l'humidité au sol, etc.. 

sources : 

    En général : 
        https://www.gammvert.fr/conseils/conseils-de-jardinage/comment-ventiler-une-serre-de-jardin
    
    Pour les tomates : 
        https://krosagro.com/fr/serres-de-culture/temperature-ideale-pour-la-culture-des-tomates-sous-serre/
        https://caldor.fr/cultures/tomates/
        https://fr.tomathouse.com/pochva-dlya-pomidor.html



### Chaleur : 

La particularité de la serre est de retenir le rayonnement solaire, de par le fameux effet de serre. De plus, la température de l’air non renouvelé dans un endroit clos ne peut qu’augmenter, devenant trop haute pour les végétaux qui ont notamment besoin d’un air plus frais la nuit et qui de toute façon ne supportent pas les températures excessives. Et plus la température est élevée, plus les végétaux transpirent , ils perdent donc de l’humidité, ce qui est dommageable pour leur organisme et ce qui ajoute de l’humidité à l’air intérieur de la serre.

Au-delà de la sensibilité des plantes face à des températures élevées, il faut également prendre en compte les écarts rapides de températures. Lorsque, au printemps, le soleil tape sur les parois d’une serre, la température peut monter facilement jusqu’à 30°. Le soir par contre la température baisse rapidement et peut même s’approcher de 0. Les tissus végétaux supportent mal ces grandes amplitudes et peuvent se fissurer, laissant pénétrer les agents pathogènes.

En moyenne, la température de croissance idéale pour les plantes se situe entre ** 15 et 24 ° ** . En-dessous de 10°, la croissance stoppe, au-dessus de 28° la photosynthèse ne se fait plus, donc la croissance s’arrête aussi. Une température de 40° ne peut être supportée que quelques heures, après les plantes meurent.

Nous allons donc limiter la température de notre serre avec un maximum à **30°** (si possible...)

### Humidité air et sol : 

Plus l’air est chaud, plus il peut contenir d’eau sous forme de vapeur. La condensation qui se produit est due à un taux d’humidité important. C’est le cas lorsqu’il y a un écart important entre les températures extérieure et intérieure. Quand l’air à l’intérieur de la serre se refroidit, l’humidité qu’il contient redevient liquide et se dépose, notamment sur les parois puisqu’elles sont plus froides que le reste (cette eau goutte sur le sol), mais aussi sur les feuilles. Les champignons pathogènes, ceux qui provoquent des maladies chez les végétaux, apprécient beaucoup cet environnement humide et tiède.

Le taux d’hygrométrie idéal pour la majorité des plantes que l’on cultive se situe entre **60 et 80 %**, et plutôt entre ** 25 et 40 % ** durant la période hivernale. Au-delà, les risques de développement de maladies cryptogamiques sont élevés. De plus, avec un air très humide, le substrat, que ce soit la terre ou du terreau, garde son humidité, ce qui peut entraîner un pourrissement au niveau des racines.

Une forte humidité dans l’air a d’autres conséquences : les plantes sont stressées et leur production est de moins bonne qualité car elles utilisent moins bien l’eau et elles absorbent moins de nutriments.

Le taux d’hygrométrie idéal pour la majorité des plantes que l’on cultive se situe entre 60 et 80 %. Nous allons essayer de réguler l'hydrométrie de notre serre autour de **70%** (si possible...)

### Acidité du sol

L’acidité du sol est l’un des indicateurs les plus importants à surveiller. 

La parcelle où les tomates sont plantées devrait avoir un pH compris entre **6 et 6,8**.

Exemple de sonde de mesures multiples qui nous permettra d'étaloner notre système pour l'humidité du sol, la température et mesurer l'acidité du sol : 

    https://www.galaxus.ch/de/s4/product/x4-4in1-bodentester-detektor-10055330?gclsrc=aw.ds

![](/images/X4.png)

(Mesure régulière de l'acidité du sol grâce à MyGreenGarden pour une prochaine mise à jour du projet)

### La ventilation forcée

Si cette aération passive n’est pas suffisante, la mise en place de ventilateurs est une solution. Vous prévoierez tout d’abord dans ce cas toute l’installation électrique nécessaire : boîtier électrique, lignes, etc.

Les ventilateurs pour serre sont des modèles hélicoïdaux avec persienne (le plus souvent). Ils seront installés en hauteur, si possible à l'opposé des vents dominants. Ils sont mis en marche sur le mode **extracteur d’air**, sachant qu’une vitesse basse est plus efficace.

### En résumé il faut : 

    - réguler la température avec un maximum de ** 30°C ** via une bonne aération.
    - réguler l’humidité de l'air entre ** 60-80% ** et du sol ** 55% ** grâce à l'arosage
    - amener de l’oxygène et évacuer le dioxyde de carbone  grâce aux ventilateurs.
    - contrôler et ajuster le PH du sol entre ** 6 et 6,6 ** (à venir)

Tout cela est la théorie. Essayons de mettre en pratique maintenant et voyons les résultats.... ;-)

## Matériel

## Raspberry PI 4 : 

https://www.pi-shop.ch/raspberry-pi-4-starter-kit-pi-4-8gb

![](/images/raspi.png)

## Boitier : 

https://www.distrelec.ch/fr/boitier-plastique-polycarbonate-couvercle-charniere-transparent-390x167x316mm-ip65-fibox-pc-36-31-enclosure/p/15058771?q=TABLEAU+ELECTRIQUE&pos=3&origPos=3&origPageSize=50&track=true

![](/images/boitier.png)

## Sonde température : 

https://www.pi-shop.ch/waterproof-ds18b20-digital-temperature-sensor-extras

![](/images/ds18b20.jpg)

## Sonde humidité d'air : 

https://learn.sparkfun.com/tutorials/hih-4030-humidity-sensor-hookup-guide?_ga=2.262327566.340503846.1650249449-1295637178.1650249449

![](/images/HIH-4030.png)


## Sonde d'humidité sol :

Ce type de sonde est bien meilleur que celle bon marché qui fluctue beaucoup dans les mesures.

https://www.tindie.com/products/pinotech/soilwatch-10-soil-moisture-sensor/

![](/images/sondeHumidité.jpg)

## Valve d'eau : 

https://www.galaxus.ch/fr/s4/product/gardena-valve-dirrigation-vanne-dirrigation-systemes-dirrigation-5614519?gclsrc=aw.ds

![](/images/watervalve.jpg)


## Ventilateurs : 

https://www.distrelec.ch/fr/ventilateur-axial-dc-60x60x38mm-12v-128m-sunon-pf60381bx-000u-a99/p/30090826?ext_cid=shgooaqchde-Shopping-CSS&gclid=CjwKCAjw9e6SBhB2EiwA5myr9ngOBPXpPBWowDOHywrxmRUTWoqybUH_C7YOZ2dqQssrNvasPt92HBoC4GsQAvD_BwE


![](/images/fan.jpg)

## Vérin 24V : 

https://vevor.fr/products/20-verin-actionneur-lineaire-dc12v-moteur-electrique-500mm-leve-tele-1?gclid=EAIaIQobChMIy6W3n_D39AIVSu7tCh0kqgDFEAQYAiABEgLF9fD_BwE

![](/images/verin.png)

## Alimentations 5, 12 et 24 V : 

https ://www.galaxus.ch/fr/s1/product/weidmueller-pro-insta-60w-24v-25a-alimentation-a-decoupage-24-vdc-25-a-60-w-60-w-alimentations-pc-15915864?supplier=4867603

https://www.galaxus.ch/fr/s1/product/weidmueller-pro-insta-60w-12v-5a-alimentatore-switching-12-vdc-5-a-60-w-60-w-alimentations-pc-15915900?supplier=4867603

https://www.galaxus.ch/fr/s1/product/weidmueller-koppelrelais-10-st-24-vdc-6-relais-8436567?supplier=4909783#gallery-open

![](/images/alim5-12-24V.jpg)

## Anénomètre : 

https://www.pi-shop.ch/anemometer-wind-speed-sensor-w-analog-voltage-output-windmesser
 
![](/images/anenometre.png)

## Module 8 relais : 

https://www.pi-shop.ch/8-relay-card-for-raspberry-pi

![](/images/module8relais.jpg)

## Convertisseur A/D (ADC) : 

https://www.distrelec.ch/fr/adc-canaux-12-bits-pour-raspberry-pi-seeed-studio-103030280/p/30135129?track=true&no-cache=true&marketingPopup=false

![](/images/ADC.png)

## Montage du tableau

![](/images/schema.png)

![](/images/montage_tableau.jpg)


## Architecture simple

![](/images/architecture.png)

## API's

Les API vont permettre de commander la serre via des requêtes http.

Exemple :

GET   http://mygreengarden.ppdlab.ch/watering

retourne le status des vannes d'eau au format JSON 
{"WATERING_ZONE_1":false,"WATERING_ZONE_2":false}

POST. http://mygreengarden.ppdlab.ch/watering/zone=1?state=1

activation de la vanne d’arrosage dans la zone 1 



URL principale : 
http://mygreengarden.ppdlab.ch

| Verb    |   URL         | Arg     |  Description                                         |
|---------|---------------|---------|-------------------------------------------------------
| GET     | /main         |  -      | page principale                                      |
| GET     | /light        |  -      | retourne l'état de la lumière (allumé/étient)        |
| GET     | /watering     |  zone   | retourne l'état de la valve d'eau dans zone=1 ou 2   |
| GET     | /windspeed    |  -      | retourne la vitesse du vent en km/h                  |
| GET     | /window/auto  |  -      | retourne l'état du mode automatique de la lucarne    |
| GET     | /window       |  -      | retourne l'état de la lucarne (ouverte/fermée)       | 
| GET     | /watering/auto|  -      | retourne l'état du mode d'arrosage automatique       | 
| GET     | /graph        |  -      | affichage des graphiques                             |
| GET     | /camera       |  -      | retourne si caméra est active ou inactive            |
| GET     | /fan          |  -      | retourne l'état des ventilateurs (on/off)            |
| GET     | /events       |  -      | affichage des événements enregsitrés                 |
| POST    | /window       |  state  | ouverture/fermeture de la lucarne                    | 
| POST    | /watering     |  zone   | arrosage de la zone 1 ou 2                           |
| POST    | /watering/auto|  state  | active désactive le mode d'arrosage automatique      |
| POST    | /window/auto  |  state  | active/désactive le mode automatique de la lucarne   |
| POST    | /camera       |  state  | active/désactive caméra state = 1/0                  |
| POST    | /reboot       |  -      | reboot Raspberry Pi 4                                |
| POST    | /shutdown     |  -      | shutdown Raspberry Pi 4                              |
| POST    | /fan          |  state  | active les ventilateurs (mode extraction d'air)      |
| POST    | /light        |  state  | allume la lumière (state = 1) eteindre (state=0)     |


## Interface Web

L'interface web est crée en Flask/Bootrap/Javascript & Ajax. 

![](/images/dashboard.png)

