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
