"""
Configuration des URLs de l'application core.
"""
from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),
]
