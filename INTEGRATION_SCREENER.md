# 🚀 Guide d'Intégration du Screener

## ✅ Ce qui a été créé

### 1. **Module screener (`core/screener.py`)**
Contient le code exact du notebook Jupyter :
- `calculate_rs_score()` : Calcul du RS Score
- `calculate_rs_rating()` : Conversion en RS Rating (1-99)
- `add_rs_rating_to_df()` : Ajout du RS aux DataFrames
- `run_screener()` : Fonction principale qui exécute tout le screener

### 2. **Vue Django (`core/views.py`)**
- `screener_view()` : Vue qui exécute le screener et affiche les résultats
- `home()` : Page d'accueil mise à jour avec lien vers le screener

### 3. **Template HTML (`core/templates/screener.html`)**
Page web stylisée avec Bootstrap 5 affichant :
- Les critères du screener
- Le nombre d'actions trouvées
- Un tableau HTML élégant avec les résultats
- Gestion des erreurs

### 4. **Routes (`core/urls.py`)**
- `/` : Page d'accueil
- `/screener/` : Page du screener

### 5. **Dépendances (`requirements.txt`)**
Fichier créé avec toutes les bibliothèques nécessaires.

---

## 🔧 Installation

Les packages ont déjà été installés, mais pour référence future :

```powershell
pip install finvizfinance yfinance pandas numpy
```

Ou depuis le fichier requirements.txt :

```powershell
pip install -r requirements.txt
```

---

## ▶️ Démarrage

1. **Lancer le serveur Django** :
```powershell
python manage.py runserver
```

2. **Accéder au screener** :
```
http://127.0.0.1:8000/screener/
```

---

## 📊 Fonctionnement

### Critères du screener Finviz :
- 🌍 **Pays** : USA uniquement
- 💰 **Market Cap** : > 50M$ (micro cap minimum)
- 📈 **Performance mensuelle** : > +10%
- 📊 **Volatilité mensuelle** : > 5%
- 📅 **Performance trimestrielle** : Positive
- ⚡ **RS Rating** : > 95 (force relative vs SPX)

### Calcul du RS Rating :
Le RS Rating mesure la performance relative d'une action par rapport au S&P 500 sur 4 périodes :
- **63 jours** (40% de poids)
- **126 jours** (20% de poids)
- **189 jours** (20% de poids)
- **252 jours** (20% de poids)

Le score est ensuite converti en une échelle de 1 à 99.

---

## 📁 Structure Créée

```
SUWI - Stock US Web Interface/
├── core/
│   ├── screener.py           # ⭐ Code du notebook
│   ├── views.py              # Vue Django
│   ├── urls.py               # Routes
│   └── templates/
│       └── screener.html     # Template HTML
├── requirements.txt          # Dépendances
└── manage.py
```

---

## 🎯 Utilisation

### Page d'accueil
```
http://127.0.0.1:8000/
```
Affiche un lien vers le screener.

### Page du screener
```
http://127.0.0.1:8000/screener/
```
Exécute le screener et affiche les résultats dans un tableau.

---

## ⚠️ Notes Importantes

1. **Temps d'exécution** : Le screener peut prendre plusieurs minutes car il :
   - Télécharge les données de toutes les actions filtrées
   - Calcule le RS Rating pour chacune
   - Filtre pour ne garder que RS > 95

2. **Données en temps réel** : Les données proviennent de :
   - **Finviz** : Screening initial
   - **Yahoo Finance** : Prix historiques pour le RS Rating

3. **Code préservé** : Le code du notebook a été conservé à l'identique, seul l'encapsulation en fonctions a été ajoutée pour l'intégration Django.

---

## 🔄 Prochaines Améliorations Possibles

- ✨ Ajout d'un loader/spinner pendant l'exécution
- 💾 Cache des résultats pour éviter de recalculer
- 📊 Graphiques de performance
- 🔔 Notifications par email des nouvelles actions
- 📱 Version mobile responsive

---

## ✅ Résultat

Votre screener Jupyter fonctionne maintenant dans Django sans modification du code métier ! 🎉
