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
    
    # API AJAX pour le screener
    path('screener/ajax/', views.screener_ajax, name='screener_ajax'),
    
    # Visualisation d'une action
    path('stock/<str:ticker>/', views.stock_detail, name='stock_detail'),
    
    # API AJAX pour les données de graphique
    path('stock/<str:ticker>/data/', views.stock_data_ajax, name='stock_data_ajax'),
    
    # Watchlists
    path('watchlist/', views.watchlist_view, name='watchlist'),
    path('watchlist/create/', views.create_watchlist_ajax, name='create_watchlist'),
    path('watchlist/add/', views.add_to_watchlist_ajax, name='add_to_watchlist'),
    path('watchlist/remove/', views.remove_from_watchlist_ajax, name='remove_from_watchlist'),
    path('watchlist/delete/', views.delete_watchlist_ajax, name='delete_watchlist'),
    path('watchlist/list/', views.get_watchlists_ajax, name='get_watchlists'),
    
    # API pour mise à jour des tags
    path('api/get-watchlist-tags/', views.get_watchlist_tags_ajax, name='get_watchlist_tags'),
    
    # Trading API
    path('stock/<str:ticker>/price/', views.get_stock_price_ajax, name='get_stock_price'),
    path('trading/place-order/', views.place_order_ajax, name='place_order'),
]
