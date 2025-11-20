# 🚀 SUWI - Stock US Web Interface

## 📋 Description

**SUWI (Stock US Web Interface)** est une application web Django pour la gestion et l'analyse de stocks américains.

Version actuelle : **Hello World** (v0.1)

---

## 🔧 Installation et Configuration

### Prérequis
- **Python** ≥ 3.10
- **pip** (gestionnaire de paquets Python)

### Étapes d'installation

#### 1. Créer l'environnement virtuel

```powershell
python -m venv venv
```

#### 2. Activer l'environnement virtuel

**Windows (PowerShell)** :
```powershell
venv\Scripts\activate
```

**Linux/macOS** :
```bash
source venv/bin/activate
```

#### 3. Installer Django 5.x

```powershell
pip install "Django>=5.0,<6.0"
```

---

## 🏗️ Structure du Projet

```
SUWI - Stock US Web Interface/
│
├── suwi/                    # Configuration principale du projet Django
│   ├── __init__.py
│   ├── settings.py          # Configuration Django (DEBUG, INSTALLED_APPS, etc.)
│   ├── urls.py              # Routes principales du projet
│   ├── asgi.py              # Point d'entrée ASGI
│   └── wsgi.py              # Point d'entrée WSGI
│
├── core/                    # Application Django principale
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py             # Vue "Hello World"
│   ├── urls.py              # Routes de l'application core
│   ├── tests.py
│   └── migrations/
│
├── manage.py                # Script de gestion Django
├── db.sqlite3               # Base de données SQLite (générée après migrate)
├── venv/                    # Environnement virtuel Python
└── README.md                # Ce fichier
```

---

## ▶️ Démarrage du Serveur

### 1. Appliquer les migrations

```powershell
python manage.py migrate
```

### 2. Lancer le serveur de développement

```powershell
python manage.py runserver
```

Le serveur démarre sur : **http://127.0.0.1:8000/**

### 3. Tester l'application

Ouvrez votre navigateur et accédez à :

```
http://127.0.0.1:8000/
```

Vous devriez voir : **Hello World**

---

## 📂 Fichiers Principaux

### `core/views.py`

```python
"""
Vue principale de l'application core.
"""
from django.http import HttpResponse


def home(request):
    """
    Vue pour la page d'accueil.
    Retourne un simple message "Hello World".
    """
    return HttpResponse("Hello World")
```

### `core/urls.py`

```python
"""
Configuration des URLs de l'application core.
"""
from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),
]
```

### `suwi/urls.py`

```python
"""
Configuration des URLs principales du projet SUWI.
"""
from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    # Interface d'administration Django
    path('admin/', admin.site.urls),
    
    # Routes de l'application core (page d'accueil, etc.)
    path('', include('core.urls')),
]
```

### `suwi/settings.py` (extrait)

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Applications locales
    'core',
]
```

---

## 🧪 Commandes Utiles

### Créer un superuser (admin)

```powershell
python manage.py createsuperuser
```

### Accéder à l'interface d'administration

```
http://127.0.0.1:8000/admin/
```

### Lancer les tests

```powershell
python manage.py test
```

### Créer une nouvelle application

```powershell
python manage.py startapp nom_de_lapp
```

---

## 📝 Notes Techniques

- **Django** : 5.2.8
- **Python** : 3.12.0
- **Base de données** : SQLite (développement)
- **Mode DEBUG** : Activé (à désactiver en production)

---

## 🎯 Prochaines Étapes

1. Ajouter des modèles de données pour les stocks
2. Créer des vues pour afficher les données
3. Implémenter l'authentification utilisateur
4. Ajouter une API REST
5. Créer une interface utilisateur moderne

---

## 👤 Auteur

**Projet SUWI** - Stock US Web Interface

---

## 📄 Licence

Ce projet est actuellement en phase de développement initial.
