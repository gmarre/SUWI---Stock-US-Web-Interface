# 🚀 GUIDE DE DÉMARRAGE RAPIDE - SUWI

## ✅ Résumé de l'installation effectuée

Votre projet Django **SUWI** est maintenant configuré et fonctionnel !

### Ce qui a été fait :

1. ✅ Environnement virtuel Python créé (`venv/`)
2. ✅ Django 5.2.8 installé
3. ✅ Projet Django `suwi` créé
4. ✅ Application `core` créée et configurée
5. ✅ Vue "Hello World" implémentée
6. ✅ Migrations appliquées
7. ✅ Serveur de développement lancé

---

## 🌐 Accéder à l'application

Le serveur Django tourne actuellement sur :

**➡️ http://127.0.0.1:8000/**

Ouvrez cette URL dans votre navigateur pour voir **"Hello World"**.

---

## 📁 Structure Créée

```
SUWI - Stock US Web Interface/
├── suwi/                    # Configuration Django
│   ├── settings.py          # 'core' ajouté dans INSTALLED_APPS
│   ├── urls.py              # Route vers core.urls
│   ├── wsgi.py
│   └── asgi.py
│
├── core/                    # Application principale
│   ├── views.py             # Fonction home() retournant "Hello World"
│   ├── urls.py              # Route '' vers views.home
│   ├── models.py
│   └── migrations/
│
├── manage.py                # Script de gestion
├── db.sqlite3               # Base de données
├── venv/                    # Environnement virtuel
└── README.md                # Documentation complète
```

---

## 🔧 Commandes Utiles

### Arrêter le serveur
Dans le terminal où il tourne : **`Ctrl + C`**

### Redémarrer le serveur
```powershell
python manage.py runserver
```

### Créer un compte admin
```powershell
python manage.py createsuperuser
```

Puis accédez à : http://127.0.0.1:8000/admin/

---

## 📝 Code Principal

### `core/views.py`
```python
from django.http import HttpResponse

def home(request):
    """Vue pour la page d'accueil."""
    return HttpResponse("Hello World")
```

### `core/urls.py`
```python
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
]
```

### `suwi/urls.py`
```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
]
```

---

## ✨ Versions Installées

- **Python** : 3.12.0
- **Django** : 5.2.8
- **Base de données** : SQLite

---

## 🎯 Prochaines Étapes

1. **Testez l'application** : http://127.0.0.1:8000/
2. **Créez un superuser** : `python manage.py createsuperuser`
3. **Explorez l'admin** : http://127.0.0.1:8000/admin/
4. Commencez à développer vos fonctionnalités !

---

🎉 **Votre projet Django est prêt à être développé !**
