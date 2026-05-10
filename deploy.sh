#!/bin/bash
# ══════════════════════════════════════════════════════════════════════════════
# deploy.sh — Script de déploiement VPS pour PDF Magic Pro
# Usage : bash deploy.sh
# Testé sur : Ubuntu 22.04 LTS
# ══════════════════════════════════════════════════════════════════════════════
set -e

PROJET_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$PROJET_DIR/venv"
LOG_DIR="/var/log/pdf_magic"
USER=$(whoami)

echo ""
echo "╔══════════════════════════════════════╗"
echo "║   PDF Magic Pro — Déploiement VPS   ║"
echo "╚══════════════════════════════════════╝"
echo ""

# ── 1. Paquets système ────────────────────────────────────────────────────────
echo "▶ [1/7] Installation des paquets système..."
sudo apt-get update -q
sudo apt-get install -y -q python3 python3-pip python3-venv nginx

# ── 2. Environnement virtuel Python ──────────────────────────────────────────
echo "▶ [2/7] Création de l'environnement virtuel Python..."
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip -q
pip install -r "$PROJET_DIR/requirements.txt" -q

# ── 3. Fichier .env ───────────────────────────────────────────────────────────
if [ ! -f "$PROJET_DIR/.env" ]; then
    echo "▶ [3/7] Création du fichier .env depuis .env.example..."
    cp "$PROJET_DIR/.env.example" "$PROJET_DIR/.env"
    SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
    sed -i "s|remplacez-moi-par-une-vraie-cle-secrete|$SECRET|g" "$PROJET_DIR/.env"
    echo "   ⚠  Pensez à éditer .env pour renseigner ALLOWED_HOSTS et CORS_ALLOWED_ORIGINS !"
else
    echo "▶ [3/7] Fichier .env existant conservé."
fi

# ── 4. Django : migrations + static ──────────────────────────────────────────
echo "▶ [4/7] Collecte des fichiers statiques Django..."
python "$PROJET_DIR/manage.py" collectstatic --noinput -v 0

# ── 5. Dossier de logs ────────────────────────────────────────────────────────
echo "▶ [5/7] Création du dossier de logs..."
sudo mkdir -p "$LOG_DIR"
sudo chown "$USER":"$USER" "$LOG_DIR"

# ── 6. Service systemd ────────────────────────────────────────────────────────
echo "▶ [6/7] Installation du service systemd Gunicorn..."
SERVICE_FILE="/etc/systemd/system/pdf_magic.service"
sudo cp "$PROJET_DIR/pdf_magic.service" "$SERVICE_FILE"
# Adapte le chemin au dossier réel et à l'utilisateur courant
sudo sed -i "s|/home/ubuntu/pdf_magic|$PROJET_DIR|g" "$SERVICE_FILE"
sudo sed -i "s|User=ubuntu|User=$USER|g" "$SERVICE_FILE"
sudo sed -i "s|Group=ubuntu|Group=$USER|g" "$SERVICE_FILE"
sudo systemctl daemon-reload
sudo systemctl enable pdf_magic
sudo systemctl restart pdf_magic

# ── 7. Nginx ──────────────────────────────────────────────────────────────────
echo "▶ [7/7] Configuration Nginx..."
sudo cp "$PROJET_DIR/nginx.conf" /etc/nginx/sites-available/pdf_magic
sudo ln -sf /etc/nginx/sites-available/pdf_magic /etc/nginx/sites-enabled/pdf_magic
sudo nginx -t && sudo systemctl reload nginx

echo ""
echo "✅ Déploiement terminé !"
echo ""
echo "Prochaines étapes :"
echo "  1. Éditez .env : nano $PROJET_DIR/.env"
echo "  2. Remplacez VOTRE_DOMAINE dans nginx.conf, puis : sudo nginx -t && sudo systemctl reload nginx"
echo "  3. (Optionnel) SSL : sudo apt install certbot python3-certbot-nginx && sudo certbot --nginx"
echo "  4. Vérifiez les logs : sudo journalctl -u pdf_magic -f"
echo ""
