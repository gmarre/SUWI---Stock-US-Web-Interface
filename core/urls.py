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
    path('watchlist/update/', views.update_watchlist_ajax, name='update_watchlist'),
    path('watchlist/add/', views.add_to_watchlist_ajax, name='add_to_watchlist'),
    path('watchlist/remove/', views.remove_from_watchlist_ajax, name='remove_from_watchlist'),
    path('watchlist/delete/', views.delete_watchlist_ajax, name='delete_watchlist'),
    path('watchlist/list/', views.get_watchlists_ajax, name='get_watchlists'),
    
    # API pour mise à jour des tags
    path('api/get-watchlist-tags/', views.get_watchlist_tags_ajax, name='get_watchlist_tags'),
    
    # Trading API
    path('stock/<str:ticker>/price/', views.get_stock_price_ajax, name='get_stock_price'),
    path('trading/place-order/', views.place_order_ajax, name='place_order'),
    
    # IB Session Management
    path('ib-auth/', views.ib_auth_view, name='ib_auth'),
    path('ib-session-status/', views.ib_session_status_ajax, name='ib_session_status'),
    path('ib-logout/', views.ib_logout_ajax, name='ib_logout'),
    path('ib-mark-session-start/', views.ib_mark_session_start_ajax, name='ib_mark_session_start'),
    
    # Portfolio
    path('positions/', views.positions_view, name='positions'),
    path('history/', views.history_view, name='history'),
    path('get-ib-accounts/', views.get_ib_accounts_ajax, name='get_ib_accounts'),
    path('get-positions/', views.get_positions_ajax, name='get_positions'),
    path('get-trade-history/', views.get_trade_history_ajax, name='get_trade_history'),
    
    # Profile
    path('profile/', views.profile_view, name='profile'),
    path('get-account-summary/', views.get_account_summary_ajax, name='get_account_summary'),
    
    # Risk Management
    path('get-risk-info/', views.get_risk_info_ajax, name='get_risk_info'),
    path('calculate-position/', views.calculate_position_ajax, name='calculate_position'),
    path('update-risk-profile/', views.update_risk_profile_ajax, name='update_risk_profile'),
]
