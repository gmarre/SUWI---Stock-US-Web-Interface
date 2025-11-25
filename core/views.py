"""
Vues de l'application core.
"""
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import ensure_csrf_cookie
from .screener import run_screener
from .models import Watchlist, WatchlistStock
from .trading import get_trader
import json
import os
import yfinance as yf


def load_screener_config():
    """Charge la configuration du screener depuis le fichier JSON"""
    config_path = os.path.join(os.path.dirname(__file__), 'screener_config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def home(request):
    """
    Vue pour la page d'accueil.
    Affiche un message de bienvenue avec lien vers le screener.
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SUWI - Accueil</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
        <style>
            body {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px 0;
            }
            .card {
                border-radius: 15px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            }
            .feature-btn {
                width: 100%;
                padding: 30px;
                margin: 10px 0;
                font-size: 1.2rem;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <!-- Navigation -->
            <div class="row mb-4">
                <div class="col-12 text-center">
                    <div class="btn-group" role="group">
                        <a href="/" class="btn btn-warning btn-lg active">
                            <i class="bi bi-house"></i> Accueil
                        </a>
                        <a href="/screener/" class="btn btn-outline-light btn-lg">
                            <i class="bi bi-filter"></i> Screener
                        </a>
                        <a href="/watchlist/" class="btn btn-outline-light btn-lg">
                            <i class="bi bi-star-fill"></i> Watchlists
                        </a>
                    </div>
                </div>
            </div>
            
            <div class="row justify-content-center">
                <div class="col-lg-8">
                    <div class="card">
                        <div class="card-body text-center p-5">
                            <h1 class="display-4 mb-3">🚀 SUWI</h1>
                            <p class="lead text-muted mb-4">Stock US Web Interface</p>
                            <hr class="my-4">
                            <p class="mb-4">Application Django de screening et analyse de stocks US</p>
                            
                            <div class="row">
                                <div class="col-md-6">
                                    <a href="/screener/" class="btn btn-primary feature-btn">
                                        <i class="bi bi-filter-circle"></i><br>
                                        Screener
                                        <br><small>Filtrer les actions US</small>
                                    </a>
                                </div>
                                <div class="col-md-6">
                                    <a href="/watchlist/" class="btn btn-warning feature-btn">
                                        <i class="bi bi-star-fill"></i><br>
                                        Watchlists
                                        <br><small>Gérer vos listes</small>
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html_content)


@ensure_csrf_cookie
def screener_view(request):
    """
    Vue pour le screener boursier US avec filtres configurables.
    
    Affiche le formulaire de filtres et exécute le screener si demandé.
    
    Returns:
        HttpResponse: Page HTML avec le formulaire et les résultats
    """
    # Charger la configuration des filtres
    config = load_screener_config()
    
    # Récupérer les filtres depuis la requête GET
    filters = {}
    for param in config['display_order']:
        value = request.GET.get(param, '')
        if value:
            filters[param] = value
    
    # Extraire RS_Rating_Min si présent
    rs_rating_min = int(filters.pop('RS_Rating_Min', 0))
    
    # Préparer le contexte - Ne jamais exécuter le screener au chargement de la page
    # Le screener est uniquement exécuté via AJAX quand on clique sur le bouton
    context = {
        'config': json.dumps(config),  # Sérialiser en JSON pour JavaScript
        'current_filters': json.dumps(filters),
        'rs_rating_min': rs_rating_min,
        'is_screening': False  # Toujours False - pas d'exécution automatique
    }
    
    return render(request, 'screener.html', context)


def screener_ajax(request):
    """
    Vue AJAX pour exécuter le screener et retourner les résultats en JSON.
    Utilisé pour afficher la progression en temps réel.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})
    
    try:
        # Récupérer les filtres depuis POST
        filters = json.loads(request.body)
        rs_rating_min = int(filters.pop('RS_Rating_Min', 95))
        
        # Exécuter le screener
        df = run_screener(custom_filters=filters, rs_rating_min=rs_rating_min)
        
        # Vérifier que df n'est pas None et n'est pas vide
        if df is not None and not df.empty:
            # Enrichir le DataFrame avec les tags de watchlist
            tickers = df['Ticker'].tolist()
            
            # Créer un dictionnaire ticker -> liste de couleurs des watchlists
            ticker_watchlists = {}
            for ticker in tickers:
                watchlists = Watchlist.objects.filter(stocks__ticker=ticker)
                if watchlists.exists():
                    ticker_watchlists[ticker] = [wl.color for wl in watchlists]
            
            # Ajouter une colonne avec les tags colorés au début du ticker
            def add_watchlist_tags(row):
                ticker = row['Ticker']
                if ticker in ticker_watchlists:
                    tags = ''.join([f'<span class="color-tag" style="background-color: {color};"></span>' for color in ticker_watchlists[ticker]])
                    return f'{tags}{ticker}'
                return ticker
            
            df['Ticker'] = df.apply(add_watchlist_tags, axis=1)
            
            table_html = df.to_html(
                classes='table table-striped table-hover',
                index=False,
                border=0,
                escape=False,
                float_format=lambda x: f'{x:.2f}' if isinstance(x, float) else x
            )
            return JsonResponse({
                'success': True,
                'html': table_html,
                'count': len(df)
            })
        else:
            # Aucun résultat trouvé - retourner un tableau vide avec en-têtes
            empty_html = '''
            <table class="table table-striped table-hover">
                <thead>
                    <tr>
                        <th>Ticker</th>
                        <th>Company</th>
                        <th>Sector</th>
                        <th>Industry</th>
                        <th>Market Cap</th>
                        <th>Price</th>
                        <th>Change</th>
                        <th>Volume</th>
                        <th>RS_Rating</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td colspan="9" class="text-center text-muted py-4">
                            <i class="bi bi-inbox"></i> Aucune action ne correspond aux critères sélectionnés
                        </td>
                    </tr>
                </tbody>
            </table>
            '''
            return JsonResponse({
                'success': True,
                'html': empty_html,
                'count': 0,
                'message': 'Aucune action ne correspond aux critères.'
            })
            
    except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


def stock_detail(request, ticker):
    """
    Vue pour afficher le détail d'une action avec graphique en chandeliers.
    
    Args:
        ticker: Symbole boursier (ex: AAPL, TSLA)
    """
    # Déterminer l'URL de retour intelligemment
    referer = request.META.get('HTTP_REFERER', '/screener/')
    # Si on vient de la watchlist, retourner au screener par défaut
    if '/watchlist/' in referer:
        back_url = '/screener/'
    else:
        back_url = referer
    
    context = {
        'ticker': ticker.upper(),
        'back_url': back_url
    }
    
    return render(request, 'stock_detail.html', context)


def stock_data_ajax(request, ticker):
    """
    API AJAX pour récupérer les données d'une action et calculer les indicateurs techniques.
    
    Args:
        ticker: Symbole boursier
        
    Query params:
        indicators: Liste des indicateurs à calculer (sma20,sma50,ema20,bbands,rsi,macd,volume)
    """
    try:
        import yfinance as yf
        import pandas as pd
        from datetime import datetime, timedelta
        
        # Récupérer les indicateurs demandés
        indicators = request.GET.get('indicators', '').split(',')
        indicators = [ind.strip() for ind in indicators if ind.strip()]
        
        # Télécharger les données (1 an + marge pour SMA)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=400)
        
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date)
        
        if df.empty:
            return JsonResponse({
                'success': False,
                'error': f'Aucune donnée trouvée pour {ticker}'
            })
        
        # Calculer les indicateurs demandés
        indicators_data = {}
        
        if 'sma20' in indicators:
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            indicators_data['sma20'] = df['SMA_20'].dropna().tolist()
        
        if 'sma50' in indicators:
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            indicators_data['sma50'] = df['SMA_50'].dropna().tolist()
        
        if 'sma200' in indicators:
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            indicators_data['sma200'] = df['SMA_200'].dropna().tolist()
        
        if 'ema20' in indicators:
            df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
            indicators_data['ema20'] = df['EMA_20'].dropna().tolist()
        
        if 'bbands' in indicators:
            sma20 = df['Close'].rolling(window=20).mean()
            std20 = df['Close'].rolling(window=20).std()
            df['BB_Upper'] = sma20 + (std20 * 2)
            df['BB_Lower'] = sma20 - (std20 * 2)
            indicators_data['bb_upper'] = df['BB_Upper'].dropna().tolist()
            indicators_data['bb_lower'] = df['BB_Lower'].dropna().tolist()
        
        if 'rsi' in indicators:
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            indicators_data['rsi'] = df['RSI'].dropna().tolist()
        
        if 'macd' in indicators:
            ema12 = df['Close'].ewm(span=12, adjust=False).mean()
            ema26 = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = ema12 - ema26
            df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
            indicators_data['macd'] = df['MACD'].dropna().tolist()
            indicators_data['macd_signal'] = df['MACD_Signal'].dropna().tolist()
            indicators_data['macd_hist'] = df['MACD_Hist'].dropna().tolist()
        
        # Garder seulement les 252 derniers jours (1 an de bourse)
        df = df.tail(252)
        
        # Préparer les données OHLCV
        dates = df.index.strftime('%Y-%m-%d').tolist()
        ohlcv = {
            'dates': dates,
            'open': df['Open'].tolist(),
            'high': df['High'].tolist(),
            'low': df['Low'].tolist(),
            'close': df['Close'].tolist(),
            'volume': df['Volume'].tolist()
        }
        
        # Informations de l'action
        info = stock.info
        stock_info = {
            'name': info.get('longName', ticker),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'market_cap': info.get('marketCap', 0),
            'pe_ratio': info.get('trailingPE', 'N/A'),
            'dividend_yield': info.get('dividendYield', 0),
            'beta': info.get('beta', 'N/A'),
            '52w_high': info.get('fiftyTwoWeekHigh', 0),
            '52w_low': info.get('fiftyTwoWeekLow', 0),
            'avg_volume': info.get('averageVolume', 0)
        }
        
        return JsonResponse({
            'success': True,
            'ticker': ticker.upper(),
            'ohlcv': ohlcv,
            'indicators': indicators_data,
            'info': stock_info
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


# ============= WATCHLIST VIEWS =============

def watchlist_view(request):
    """
    Vue pour afficher toutes les watchlists et leurs tickers.
    """
    watchlists = Watchlist.objects.all().prefetch_related('stocks')
    
    context = {
        'watchlists': watchlists,
        'back_url': request.META.get('HTTP_REFERER', '/screener/')
    }
    
    return render(request, 'watchlist.html', context)


def create_watchlist_ajax(request):
    """
    API AJAX pour créer une nouvelle watchlist.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})
    
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        color = data.get('color', '#007bff')  # Bleu par défaut
        
        if not name:
            return JsonResponse({'success': False, 'error': 'Le nom est requis'})
        
        # Vérifier si une watchlist avec ce nom existe déjà
        if Watchlist.objects.filter(name=name).exists():
            return JsonResponse({'success': False, 'error': 'Une watchlist avec ce nom existe déjà'})
        
        watchlist = Watchlist.objects.create(name=name, color=color)
        
        return JsonResponse({
            'success': True,
            'watchlist': {
                'id': watchlist.id,
                'name': watchlist.name,
                'color': watchlist.color
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def add_to_watchlist_ajax(request):
    """
    API AJAX pour ajouter un ticker à une watchlist.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})
    
    try:
        data = json.loads(request.body)
        watchlist_id = data.get('watchlist_id')
        ticker = data.get('ticker', '').strip().upper()
        
        if not watchlist_id or not ticker:
            return JsonResponse({'success': False, 'error': 'Watchlist ID et ticker requis'})
        
        watchlist = get_object_or_404(Watchlist, id=watchlist_id)
        
        # Vérifier si le ticker existe déjà dans cette watchlist
        if WatchlistStock.objects.filter(watchlist=watchlist, ticker=ticker).exists():
            return JsonResponse({'success': False, 'error': f'{ticker} est déjà dans cette watchlist'})
        
        WatchlistStock.objects.create(watchlist=watchlist, ticker=ticker)
        
        return JsonResponse({
            'success': True,
            'message': f'{ticker} ajouté à {watchlist.name}'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def remove_from_watchlist_ajax(request):
    """
    API AJAX pour retirer un ticker d'une watchlist.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})
    
    try:
        data = json.loads(request.body)
        watchlist_id = data.get('watchlist_id')
        ticker = data.get('ticker', '').strip().upper()
        
        if not watchlist_id or not ticker:
            return JsonResponse({'success': False, 'error': 'Watchlist ID et ticker requis'})
        
        watchlist = get_object_or_404(Watchlist, id=watchlist_id)
        stock = get_object_or_404(WatchlistStock, watchlist=watchlist, ticker=ticker)
        stock.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'{ticker} retiré de {watchlist.name}'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def delete_watchlist_ajax(request):
    """
    API AJAX pour supprimer une watchlist complète.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})
    
    try:
        data = json.loads(request.body)
        watchlist_id = data.get('watchlist_id')
        
        if not watchlist_id:
            return JsonResponse({'success': False, 'error': 'Watchlist ID requis'})
        
        watchlist = get_object_or_404(Watchlist, id=watchlist_id)
        watchlist_name = watchlist.name
        watchlist.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Watchlist "{watchlist_name}" supprimée'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def get_watchlists_ajax(request):
    """
    API AJAX pour récupérer toutes les watchlists (pour le dropdown).
    """
    try:
        watchlists = Watchlist.objects.all().values('id', 'name')
        return JsonResponse({
            'success': True,
            'watchlists': list(watchlists)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def get_watchlist_tags_ajax(request):
    """
    API AJAX pour récupérer les tags (couleurs) des watchlists pour une liste de tickers.
    Utilisé pour la mise à jour en temps réel des tags dans le screener.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})
    
    try:
        data = json.loads(request.body)
        tickers = data.get('tickers', [])
        
        if not tickers:
            return JsonResponse({'success': True, 'tags': {}})
        
        # Créer un dictionnaire ticker -> [couleurs]
        ticker_tags = {}
        for ticker in tickers:
            watchlists = Watchlist.objects.filter(stocks__ticker=ticker)
            if watchlists.exists():
                ticker_tags[ticker] = [wl.color for wl in watchlists]
            else:
                ticker_tags[ticker] = []
        
        return JsonResponse({
            'success': True,
            'tags': ticker_tags
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def get_stock_price_ajax(request, ticker):
    """
    API AJAX pour récupérer le prix actuel d'une action.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose', 0)
        
        return JsonResponse({
            'success': True,
            'price': float(price)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'price': 0
        })


def place_order_ajax(request):
    """
    API AJAX pour placer un ordre via Interactive Brokers.
    Effectue les vérifications de sécurité et place un ordre bracket.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})
    
    try:
        data = json.loads(request.body)
        
        # Récupérer les paramètres
        ticker = data.get('ticker')
        action = data.get('action')  # 'BUY' ou 'SELL'
        quantity = int(data.get('quantity', 0))
        take_profit_pct = data.get('take_profit_pct')
        stop_loss_pct = data.get('stop_loss_pct')
        
        # Validations
        if not ticker or not action:
            return JsonResponse({
                'success': False,
                'message': 'Paramètres manquants'
            })
        
        if action not in ['BUY', 'SELL']:
            return JsonResponse({
                'success': False,
                'message': 'Action invalide (doit être BUY ou SELL)'
            })
        
        if quantity <= 0:
            return JsonResponse({
                'success': False,
                'message': 'Quantité invalide'
            })
        
        # Convertir None en None pour les pourcentages
        if take_profit_pct:
            take_profit_pct = float(take_profit_pct)
        if stop_loss_pct:
            stop_loss_pct = float(stop_loss_pct)
        
        # Récupérer l'instance du trader
        trader = get_trader()
        
        # Placer l'ordre bracket
        result = trader.place_bracket_order(
            ticker=ticker,
            action=action,
            quantity=quantity,
            take_profit_pct=take_profit_pct,
            stop_loss_pct=stop_loss_pct
        )
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur serveur: {str(e)}'
        })
