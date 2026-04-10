#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  Ma Serre — Script d'installation sur Raspberry Pi
#  Auteur  : Patrick Pinard
#  Usage   : bash deploy/install.sh
# ═══════════════════════════════════════════════════════════════

set -e

APP_DIR="/home/pi/MyGreenGarden"
VENV_DIR="$APP_DIR/.venv"
SERVICE_NAME="maserre"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   Ma Serre — Installation V7.0           ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── 1. Vérifications ──────────────────────────────────────────
if [ "$(whoami)" != "root" ]; then
    echo "❌  Ce script doit être exécuté avec sudo."
    echo "    Usage : sudo bash deploy/install.sh"
    exit 1
fi

if [ ! -d "$APP_DIR" ]; then
    echo "❌  Répertoire $APP_DIR introuvable."
    exit 1
fi

echo "✔  Répertoire application : $APP_DIR"

# ── 2. Paquets système ────────────────────────────────────────
echo ""
echo "▶  Installation des paquets système..."
apt-get update -q
apt-get install -y -q python3 python3-venv python3-full

# ── 3. Environnement virtuel ──────────────────────────────────
echo ""
echo "▶  Création du virtualenv..."
if [ -d "$VENV_DIR" ]; then
    echo "   (suppression de l'ancien venv)"
    rm -rf "$VENV_DIR"
fi

python3 -m venv "$VENV_DIR"
chown -R pi:pi "$VENV_DIR"
chmod +x "$VENV_DIR/bin/"*

echo "✔  Virtualenv créé : $VENV_DIR"

# ── 4. Dépendances Python ─────────────────────────────────────
echo ""
echo "▶  Installation des dépendances Python..."
sudo -u pi "$VENV_DIR/bin/pip" install --upgrade pip -q
sudo -u pi "$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt" -q
echo "✔  Dépendances installées"

# ── 5. Permissions sur l'app ──────────────────────────────────
echo ""
echo "▶  Correction des permissions..."
chown -R pi:pi "$APP_DIR"
find "$APP_DIR" -name "*.py" -exec chmod 644 {} \;
chmod 755 "$APP_DIR"

# ── 6. Sudoers (reboot/shutdown sans mot de passe) ───────────
echo ""
echo "▶  Configuration sudoers pour reboot/shutdown..."
SUDOERS_FILE="/etc/sudoers.d/maserre"
echo "pi ALL=(ALL) NOPASSWD: /usr/sbin/reboot, /usr/sbin/shutdown" > "$SUDOERS_FILE"
chmod 440 "$SUDOERS_FILE"
echo "✔  Sudoers configuré : $SUDOERS_FILE"

# ── 7. Service systemd ────────────────────────────────────────
echo ""
echo "▶  Installation du service systemd..."
cp "$APP_DIR/deploy/maserre.service" "$SERVICE_FILE"
chmod 644 "$SERVICE_FILE"

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"
echo "✔  Service systemd installé et activé"

# ── 7. Statut final ───────────────────────────────────────────
echo ""
sleep 2
STATUS=$(systemctl is-active "$SERVICE_NAME")
if [ "$STATUS" = "active" ]; then
    echo "✔  Service $SERVICE_NAME : ACTIF"
else
    echo "⚠  Service $SERVICE_NAME : $STATUS"
    echo "   Consulter les logs : sudo journalctl -u $SERVICE_NAME -n 30"
fi

# Récupérer l'IP locale
IP=$(hostname -I | awk '{print $1}')
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   Installation terminée !                ║"
echo "║                                          ║"
printf  "║   URL locale : http://%-18s ║\n" "${IP}:8000"
echo "╚══════════════════════════════════════════╝"
echo ""
