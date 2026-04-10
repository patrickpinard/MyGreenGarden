#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
#  MyGreenGarden V7 — Installation complète sur Raspberry Pi 4
#
#  Prérequis : Raspberry Pi OS Bookworm (64-bit), accès sudo
#  Usage     : sudo bash /opt/mygreengarden/deploy/setup.sh
#
#  Ce script installe et configure :
#    • Python 3.11 + environnement virtuel
#    • Dépendances système (GPIO, I2C, SPI)
#    • MyGreenGarden et toutes ses dépendances Python
#    • Service systemd (démarrage automatique au boot)
#    • Nginx (reverse proxy port 80 → 8000)
#    • Logrotate (rotation des logs)
#    • Activation I2C/SPI dans /boot/firmware/config.txt
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# ── Couleurs & helpers ────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

info()    { echo -e "${GREEN}[✓]${NC} $*"; }
step()    { echo -e "\n${CYAN}${BOLD}── $* ${NC}"; }
warn()    { echo -e "${YELLOW}[!]${NC} $*"; }
error()   { echo -e "${RED}[✗]${NC} $*"; exit 1; }
ask()     { echo -e "${YELLOW}[?]${NC} $*"; }

# ── Vérification root ────────────────────────────────────────────────────────
[[ $EUID -ne 0 ]] && error "Ce script doit être exécuté avec sudo : sudo bash $0"

# ── Constantes ────────────────────────────────────────────────────────────────
APP_USER="mgg"
APP_DIR="/opt/mygreengarden"
VENV_DIR="$APP_DIR/.venv"
DATA_DIR="$APP_DIR/data"
LOGS_DIR="$APP_DIR/logs"
SERVICE="mygreengarden"
PYTHON="python3"

echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║   🌱  MyGreenGarden V7.0 — Installation Pi 4     ║${NC}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════════╝${NC}"
echo ""

# ── 1. Vérification architecture et Python ───────────────────────────────────
step "Vérification de l'environnement"

ARCH=$(uname -m)
info "Architecture : $ARCH"

PY_VER=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")
info "Python : $PY_VER"

# Python 3.10 minimum requis
python_ok=$(python3 -c "import sys; print(1 if sys.version_info >= (3,10) else 0)" 2>/dev/null || echo 0)
[[ "$python_ok" == "1" ]] || error "Python 3.10+ requis. Version détectée : $PY_VER"

# ── 2. Mise à jour et dépendances système ─────────────────────────────────────
step "Installation des dépendances système"

apt-get update -qq
apt-get install -y -qq \
    python3-pip \
    python3-venv \
    python3-dev \
    python3-setuptools \
    libopenjp2-7 \
    libjpeg-dev \
    libatlas-base-dev \
    libgpiod2 \
    gpiod \
    i2c-tools \
    nginx \
    sqlite3 \
    curl \
    logrotate

info "Dépendances système installées."

# ── 3. Activation I2C et SPI ─────────────────────────────────────────────────
step "Activation I2C / SPI"

BOOT_CFG="/boot/firmware/config.txt"
# Fallback pour anciens OS Raspberry Pi
[[ -f "$BOOT_CFG" ]] || BOOT_CFG="/boot/config.txt"

if [[ -f "$BOOT_CFG" ]]; then
    grep -qx "dtparam=i2c_arm=on" "$BOOT_CFG" || {
        echo "dtparam=i2c_arm=on" >> "$BOOT_CFG"
        info "I2C activé dans $BOOT_CFG"
    }
    grep -qx "dtparam=spi=on" "$BOOT_CFG" || {
        echo "dtparam=spi=on" >> "$BOOT_CFG"
        info "SPI activé dans $BOOT_CFG"
    }
    # Charger les modules maintenant sans reboot
    modprobe i2c-dev 2>/dev/null || true
    modprobe spi-bcm2835 2>/dev/null || true
    info "Modules I2C/SPI chargés."
else
    warn "Fichier config.txt introuvable — activez I2C/SPI via raspi-config."
fi

# ── 4. Utilisateur applicatif ─────────────────────────────────────────────────
step "Utilisateur système '$APP_USER'"

if ! id "$APP_USER" &>/dev/null; then
    useradd \
        --system \
        --no-create-home \
        --home-dir "$APP_DIR" \
        --shell /usr/sbin/nologin \
        "$APP_USER"
    info "Utilisateur '$APP_USER' créé."
else
    info "Utilisateur '$APP_USER' déjà présent."
fi

# Accès GPIO/I2C/SPI
for grp in gpio i2c spi dialout; do
    getent group "$grp" &>/dev/null && usermod -aG "$grp" "$APP_USER" && info "Groupe $grp → $APP_USER"
done

# ── 5. Répertoires ────────────────────────────────────────────────────────────
step "Répertoires de l'application"

mkdir -p "$DATA_DIR" "$LOGS_DIR"
chown -R "$APP_USER":"$APP_USER" "$APP_DIR"
chmod 750 "$APP_DIR" "$DATA_DIR" "$LOGS_DIR"
info "Répertoires : $APP_DIR, data/, logs/"

# ── 6. Environnement virtuel Python ──────────────────────────────────────────
step "Environnement virtuel Python"

if [[ ! -d "$VENV_DIR" ]]; then
    sudo -u "$APP_USER" $PYTHON -m venv "$VENV_DIR"
    info "Venv créé : $VENV_DIR"
else
    info "Venv existant conservé."
fi

info "Mise à jour de pip..."
sudo -u "$APP_USER" "$VENV_DIR/bin/pip" install --quiet --upgrade pip setuptools wheel

info "Installation des dépendances Python (avec extras raspberry)..."
sudo -u "$APP_USER" "$VENV_DIR/bin/pip" install --quiet -e "$APP_DIR[raspberry]"

info "Dépendances installées."

# ── 7. Fichier de configuration .env ─────────────────────────────────────────
step "Configuration (.env)"

if [[ ! -f "$APP_DIR/.env" ]]; then
    cp "$APP_DIR/.env.example" "$APP_DIR/.env"

    # Mode réel (pas démo)
    sed -i 's/^DEMO_MODE=.*/DEMO_MODE=false/' "$APP_DIR/.env"

    # Clé secrète aléatoire
    SECRET=$($PYTHON -c "import secrets; print(secrets.token_hex(32))")
    sed -i "s|^SECRET_KEY=.*|SECRET_KEY=${SECRET}|" "$APP_DIR/.env"

    # Chemin base de données dans data/
    sed -i "s|^DATABASE_URL=.*|DATABASE_URL=sqlite+aiosqlite:////opt/mygreengarden/data/mygreengarden.db|" "$APP_DIR/.env"

    # Désactiver le debug
    sed -i 's/^DEBUG=.*/DEBUG=false/' "$APP_DIR/.env"

    chown "$APP_USER":"$APP_USER" "$APP_DIR/.env"
    chmod 600 "$APP_DIR/.env"

    info "Fichier .env créé avec une clé secrète générée."
    warn "Éditez $APP_DIR/.env pour configurer :"
    warn "  • ADMIN_USERNAME / ADMIN_PASSWORD"
    warn "  • SMTP_USER / SMTP_PASSWORD / ALERT_EMAIL_TO"
    warn "  • Les seuils d'automatisation"
else
    info "Fichier .env existant conservé (paramètres non modifiés)."
fi

# ── 8. Service systemd ────────────────────────────────────────────────────────
step "Service systemd"

cp "$APP_DIR/deploy/mygreengarden.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable "$SERVICE"
info "Service '$SERVICE' activé (démarrage automatique au boot)."

# ── 9. Nginx (reverse proxy) ──────────────────────────────────────────────────
step "Nginx (reverse proxy port 80 → 8000)"

cp "$APP_DIR/deploy/nginx.conf" /etc/nginx/sites-available/mygreengarden
ln -sf /etc/nginx/sites-available/mygreengarden /etc/nginx/sites-enabled/mygreengarden
rm -f /etc/nginx/sites-enabled/default

if nginx -t -q 2>/dev/null; then
    systemctl restart nginx
    info "Nginx configuré et redémarré."
else
    warn "Erreur de configuration nginx — vérifiez manuellement."
    nginx -t
fi

# ── 10. Logrotate ─────────────────────────────────────────────────────────────
step "Rotation des logs (logrotate)"

cp "$APP_DIR/deploy/logrotate.conf" /etc/logrotate.d/mygreengarden
info "Logrotate configuré."

# ── 11. Démarrage du service ──────────────────────────────────────────────────
step "Démarrage"

systemctl start "$SERVICE"
sleep 3

if systemctl is-active --quiet "$SERVICE"; then
    info "Service démarré et actif ✓"
else
    warn "Le service ne semble pas actif. Consultez les logs :"
    journalctl -u "$SERVICE" --no-pager -n 20
fi

# ── Résumé ────────────────────────────────────────────────────────────────────
LOCAL_IP=$(hostname -I | awk '{print $1}')
HOSTNAME=$(hostname)

echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║   🌱  Installation terminée avec succès !                 ║${NC}"
echo -e "${GREEN}${BOLD}╠══════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}${BOLD}║${NC}                                                            ${GREEN}${BOLD}║${NC}"
echo -e "${GREEN}${BOLD}║${NC}  Accès local  : ${CYAN}http://${LOCAL_IP}${NC}                    ${GREEN}${BOLD}║${NC}"
echo -e "${GREEN}${BOLD}║${NC}  Accès réseau : ${CYAN}http://${HOSTNAME}.local${NC}               ${GREEN}${BOLD}║${NC}"
echo -e "${GREEN}${BOLD}║${NC}  Direct (sans nginx) : ${CYAN}http://${LOCAL_IP}:8000${NC}         ${GREEN}${BOLD}║${NC}"
echo -e "${GREEN}${BOLD}║${NC}                                                            ${GREEN}${BOLD}║${NC}"
echo -e "${GREEN}${BOLD}║${NC}  Commandes utiles :                                        ${GREEN}${BOLD}║${NC}"
echo -e "${GREEN}${BOLD}║${NC}    journalctl -fu mygreengarden   # logs temps réel        ${GREEN}${BOLD}║${NC}"
echo -e "${GREEN}${BOLD}║${NC}    sudo systemctl restart mygreengarden                    ${GREEN}${BOLD}║${NC}"
echo -e "${GREEN}${BOLD}║${NC}    sudo nano /opt/mygreengarden/.env   # configuration      ${GREEN}${BOLD}║${NC}"
echo -e "${GREEN}${BOLD}║${NC}                                                            ${GREEN}${BOLD}║${NC}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

if grep -q "ADMIN_PASSWORD=admin" "$APP_DIR/.env" 2>/dev/null; then
    echo -e "${RED}${BOLD}⚠  SÉCURITÉ : Changez le mot de passe admin dans .env !${NC}"
    echo -e "${RED}   sudo nano /opt/mygreengarden/.env${NC}"
    echo ""
fi

if grep -q "DEMO_MODE=false" "$APP_DIR/.env" 2>/dev/null; then
    echo -e "${YELLOW}ℹ  Mode RÉEL activé — assurez-vous que vos capteurs"
    echo -e "   et actionneurs sont correctement branchés.${NC}"
    echo ""
fi
