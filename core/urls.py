"""
Configuration des URLs de l'application core.
"""
from django.urls import path
from . import views


urlpatterns = [
    # Page d'accueil
    path('', views.home, name='home'),
    
    # Screener boursier US
    path('screener/', views.screener_view, name='screener'),
]
