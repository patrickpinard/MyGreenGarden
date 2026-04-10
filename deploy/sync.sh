#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
#  MyGreenGarden V7 — Synchronisation Mac → Raspberry Pi
#
#  Usage   : ./deploy/sync.sh [user@]ip_du_raspberry
#  Exemple : ./deploy/sync.sh pi@192.168.1.42
#
#  Ce script :
#    1. Crée /opt/mygreengarden sur le Pi si nécessaire
#    2. Copie tous les fichiers du projet (exclut .venv, *.db, *.log, etc.)
#    3. Affiche la commande pour redémarrer/installer
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# ── Couleurs ──────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${GREEN}▶${NC}  $*"; }
step()  { echo -e "${CYAN}══${NC}  $*"; }
warn()  { echo -e "${YELLOW}⚠${NC}   $*"; }

# ── Paramètre ─────────────────────────────────────────────────────────────────
TARGET="${1:-}"
if [[ -z "$TARGET" ]]; then
    echo ""
    echo "  Usage : $0 [user@]ip_du_raspberry"
    echo ""
    echo "  Exemples :"
    echo "    $0 pi@192.168.1.42"
    echo "    $0 pi@serre.local"
    echo ""
    exit 1
fi

# Extraire user@host (sans éventuel :path)
SSH_TARGET="${TARGET%%:*}"

# ── Répertoires ───────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$(dirname "$SCRIPT_DIR")"   # racine V7.0
REMOTE_DIR="/opt/mygreengarden"

echo ""
step "MyGreenGarden V7 — Synchronisation"
echo "   Source  : $SRC_DIR"
echo "   Cible   : $SSH_TARGET:$REMOTE_DIR"
echo ""

# ── 1. Créer le répertoire cible sur le Pi (avec sudo) ───────────────────────
info "Préparation du répertoire cible..."
ssh "$SSH_TARGET" "sudo mkdir -p $REMOTE_DIR && sudo chown \$(whoami):\$(whoami) $REMOTE_DIR"

# ── 2. rsync ─────────────────────────────────────────────────────────────────
info "Transfert des fichiers..."
rsync -avz \
    --progress \
    --delete \
    --exclude='.venv/' \
    --exclude='.DS_Store' \
    --exclude='**/.DS_Store' \
    --exclude='*.pyc' \
    --exclude='**/__pycache__/' \
    --exclude='.git/' \
    --exclude='*.db' \
    --exclude='*.log' \
    --exclude='maserre.HEIC' \
    --exclude='data/' \
    --exclude='logs/' \
    "$SRC_DIR/" \
    "$SSH_TARGET:$REMOTE_DIR/"

echo ""
info "Synchronisation terminée ✓"
echo ""

# ── 3. Instructions post-sync ─────────────────────────────────────────────────
echo -e "${CYAN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║${NC}  Prochaines étapes                                   ${CYAN}║${NC}"
echo -e "${CYAN}╠══════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║${NC}                                                      ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}  Première installation :                              ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}    ssh $SSH_TARGET                              ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}    sudo bash $REMOTE_DIR/deploy/setup.sh             ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}                                                      ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}  Mise à jour (app déjà installée) :                  ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}    ssh $SSH_TARGET                              ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}    sudo bash $REMOTE_DIR/deploy/update.sh            ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}                                                      ${CYAN}║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
