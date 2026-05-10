# 📖 PDF Magic Pro — Backend Django

Backend REST API pour PDF Magic Pro. Traite les PDFs côté serveur avec PyPDF2, ReportLab et pypdfium2.

---

## 📁 Structure du projet

```
pdf_magic/
├── pdf_magic/          ← Package Django principal
│   ├── settings.py     ← Configuration (lit le .env)
│   ├── urls.py         ← Routes racine
│   └── wsgi.py         ← Point d'entrée WSGI
├── api/                ← Application API
│   ├── views.py        ← Les 6 fonctionnalités PDF
│   └── urls.py         ← Routes /api/pdf/...
├── requirements.txt    ← Dépendances Python
├── manage.py           ← CLI Django
├── .env.example        ← Variables d'environnement (modèle)
├── nginx.conf          ← Configuration Nginx (VPS)
├── pdf_magic.service   ← Service systemd Gunicorn
└── deploy.sh           ← Script de déploiement automatique
```

---

## ⚡ Démarrage rapide (local)

```bash
# 1. Créer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate        # Windows : venv\Scripts\activate

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configurer l'environnement
cp .env.example .env
# Éditez .env : mettez DEBUG=True pour le développement local

# 4. Lancer le serveur de développement
python manage.py runserver
```

Le backend est accessible sur `http://localhost:8000`

---

## 🌐 Déploiement VPS (Ubuntu 22.04)

### Déploiement automatique

```bash
# Clonez / uploadez le projet sur le VPS, puis :
chmod +x deploy.sh
bash deploy.sh
```

Le script installe automatiquement :
- Les paquets système (Python, Nginx)
- L'environnement virtuel et les dépendances
- Le service systemd Gunicorn
- La configuration Nginx

### Déploiement manuel étape par étape

```bash
# 1. Paquets système
sudo apt update && sudo apt install -y python3 python3-venv python3-pip nginx

# 2. Environnement virtuel
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Variables d'environnement
cp .env.example .env
nano .env   # Remplissez les valeurs

# 4. Fichiers statiques
python manage.py collectstatic --noinput

# 5. Gunicorn (service systemd)
sudo cp pdf_magic.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable pdf_magic
sudo systemctl start pdf_magic

# 6. Nginx
sudo cp nginx.conf /etc/nginx/sites-available/pdf_magic
sudo ln -s /etc/nginx/sites-available/pdf_magic /etc/nginx/sites-enabled/
# Éditez VOTRE_DOMAINE dans le fichier nginx.conf
sudo nginx -t && sudo systemctl reload nginx

# 7. (Optionnel) SSL gratuit avec Certbot
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d votre-domaine.com
```

---

## 🔌 Endpoints API

| Méthode | Route | Description |
|---------|-------|-------------|
| POST | `/api/pdf/merge` | Fusionner plusieurs PDFs |
| POST | `/api/pdf/split` | Extraire une plage de pages |
| POST | `/api/pdf/extract-text` | Extraire le texte brut |
| POST | `/api/pdf/to-image` | Convertir en JPEG(s) |
| POST | `/api/pdf/create` | Créer un PDF depuis du texte |
| POST | `/api/pdf/protect` | Chiffrer avec mot de passe |

### Détail des paramètres

**POST /api/pdf/merge**
```
files[]   : fichiers PDF (multipart, ≥ 2)
→ Retourne : application/pdf
```

**POST /api/pdf/split**
```
file      : fichier PDF (multipart)
start     : numéro de première page (int, ≥ 1)
end       : numéro de dernière page (int, ≥ start)
→ Retourne : application/pdf
```

**POST /api/pdf/extract-text**
```
file      : fichier PDF (multipart)
→ Retourne : text/plain (UTF-8)
```

**POST /api/pdf/to-image**
```
file      : fichier PDF (multipart)
→ 1 page   : image/jpeg
→ N pages  : application/zip (JPEG par page)
```

**POST /api/pdf/create**
```
content   : texte brut (form field)
title     : titre du document (optionnel)
→ Retourne : application/pdf
```

**POST /api/pdf/protect**
```
file      : fichier PDF (multipart)
password  : mot de passe (min. 4 caractères)
→ Retourne : application/pdf (chiffré AES-128)
```

---

## 🔧 Configuration du frontend

Dans votre fichier HTML, changez l'URL du backend dans les Paramètres de la sidebar :

```
URL Spring Boot → http://VOTRE_DOMAINE/
```

Ou directement dans le code (champ `set-url`), mettez votre domaine VPS.

---

## 🛠 Commandes utiles

```bash
# Voir les logs Gunicorn en temps réel
sudo journalctl -u pdf_magic -f

# Redémarrer après modification du code
sudo systemctl restart pdf_magic

# Status du service
sudo systemctl status pdf_magic

# Tester la config Nginx
sudo nginx -t

# Recharger Nginx
sudo systemctl reload nginx
```

---

## 📦 Dépendances

| Package | Rôle |
|---------|------|
| Django 4.2 | Framework web |
| djangorestframework | API REST |
| django-cors-headers | Gestion CORS |
| PyPDF2 | Fusion, extraction, protection |
| pypdfium2 | Rendu PDF → image (haute qualité) |
| reportlab | Création de PDF depuis texte |
| Pillow | Traitement d'images |
| gunicorn | Serveur WSGI production |
| python-dotenv | Chargement du .env |
