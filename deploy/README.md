# Ma Serre — Déploiement sur Raspberry Pi

## Prérequis

- Raspberry Pi OS (Bookworm / Bullseye)
- Python 3.11+
- Application dans `/home/pi/MyGreenGarden`

---

## Installation automatique

```bash
cd /home/pi/MyGreenGarden
sudo bash deploy/install.sh
```

Le script effectue automatiquement :
1. Installation des paquets système (`python3-venv`, `python3-full`)
2. Création du virtualenv `.venv` avec les bonnes permissions
3. Installation des dépendances Python (`requirements.txt`)
4. Installation et activation du service systemd `maserre`

---

## Commandes de gestion

```bash
# Statut du service
sudo systemctl status maserre

# Démarrer / Arrêter / Redémarrer
sudo systemctl start maserre
sudo systemctl stop maserre
sudo systemctl restart maserre

# Activer / désactiver au démarrage
sudo systemctl enable maserre
sudo systemctl disable maserre

# Logs en temps réel
sudo journalctl -u maserre -f

# Dernières 50 lignes de logs
sudo journalctl -u maserre -n 50
```

---

## Mise à jour de l'application

```bash
# 1. Copier les nouveaux fichiers dans /home/pi/MyGreenGarden

# 2. Si requirements.txt a changé :
.venv/bin/pip install -r requirements.txt

# 3. Redémarrer le service
sudo systemctl restart maserre
```

---

## Démarrage manuel (debug)

```bash
cd /home/pi/MyGreenGarden
.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Accès

| Réseau  | URL                          |
|---------|------------------------------|
| Local   | `http://<IP_PI>:8000`        |
| Pi      | `http://localhost:8000`      |
