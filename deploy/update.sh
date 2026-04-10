#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
#  MyGreenGarden V7 — Mise à jour sur Raspberry Pi
#
#  À exécuter sur le Pi après une synchronisation depuis le Mac :
#    sudo bash /opt/mygreengarden/deploy/update.sh
#
#  Ce script :
#    1. Arrête proprement le service (attend la fin des arrosages en cours)
#    2. Met à jour les dépendances Python si pyproject.toml a changé
#    3. Recharge la configuration nginx si elle a changé
#    4. Redémarre le service
#    5. Vérifie que tout est opérationnel
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'; BOLD='\033[1m'
info()  { echo -e "${GREEN}[✓]${NC} $*"; }
step()  { echo -e "\n${BOLD}── $*${NC}"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
error() { echo -e "${RED}[✗]${NC} $*"; exit 1; }

[[ $EUID -ne 0 ]] && error "Exécutez avec sudo : sudo bash $0"

APP_DIR="/opt/mygreengarden"
VENV_DIR="$APP_DIR/.venv"
APP_USER="mgg"
SERVICE="mygreengarden"

echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║   🌱  MyGreenGarden — Mise à jour    ║${NC}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════╝${NC}"
echo ""

# ── 1. Arrêt propre ──────────────────────────────────────────────────────────
step "Arrêt du service"
if systemctl is-active --quiet "$SERVICE"; then
    systemctl stop "$SERVICE"
    info "Service arrêté."
else
    info "Service déjà arrêté."
fi

# ── 2. Mise à jour des dépendances Python ────────────────────────────────────
step "Dépendances Python"
sudo -u "$APP_USER" "$VENV_DIR/bin/pip" install --quiet -e "$APP_DIR[raspberry]"
info "Dépendances à jour."

# ── 3. Nginx — recharger la config si elle a changé ─────────────────────────
step "Configuration nginx"
NGINX_SRC="$APP_DIR/deploy/nginx.conf"
NGINX_DST="/etc/nginx/sites-available/mygreengarden"

if ! cmp -s "$NGINX_SRC" "$NGINX_DST"; then
    cp "$NGINX_SRC" "$NGINX_DST"
    if nginx -t -q 2>/dev/null; then
        systemctl reload nginx
        info "Nginx rechargé."
    else
        warn "Erreur nginx — configuration non appliquée."
    fi
else
    info "Configuration nginx inchangée."
fi

# ── 4. Service systemd — recharger si le fichier a changé ───────────────────
step "Service systemd"
SERVICE_SRC="$APP_DIR/deploy/mygreengarden.service"
SERVICE_DST="/etc/systemd/system/${SERVICE}.service"

if ! cmp -s "$SERVICE_SRC" "$SERVICE_DST"; then
    cp "$SERVICE_SRC" "$SERVICE_DST"
    systemctl daemon-reload
    info "Définition du service rechargée."
else
    info "Service systemd inchangé."
fi

# ── 5. Démarrage ─────────────────────────────────────────────────────────────
step "Démarrage"
systemctl start "$SERVICE"
sleep 3

if systemctl is-active --quiet "$SERVICE"; then
    info "Service actif ✓"
    echo ""
    systemctl status "$SERVICE" --no-pager -l | head -20
else
    error "Le service n'a pas démarré. Consultez les logs :"
    journalctl -u "$SERVICE" --no-pager -n 30
fi

echo ""
echo -e "${GREEN}${BOLD}✓  Mise à jour terminée${NC}"
echo "   Logs : journalctl -fu $SERVICE"
echo ""
