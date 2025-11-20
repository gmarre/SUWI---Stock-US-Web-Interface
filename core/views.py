"""
Vues de l'application core.
"""
from django.http import HttpResponse
from django.shortcuts import render
from .screener import run_screener


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
        <style>
            body {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .card {
                border-radius: 15px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-lg-6">
                    <div class="card">
                        <div class="card-body text-center p-5">
                            <h1 class="display-4 mb-3">🚀 SUWI</h1>
                            <p class="lead text-muted mb-4">Stock US Web Interface</p>
                            <hr class="my-4">
                            <p>Application Django de screening et analyse de stocks US</p>
                            <a href="/screener/" class="btn btn-primary btn-lg mt-3">
                                🔍 Accéder au Screener
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html_content)


def screener_view(request):
    """
    Vue pour le screener boursier US.
    
    Exécute le screener Finviz avec calcul du RS Rating et affiche
    les résultats dans un tableau HTML.
    
    Le screener filtre les actions US selon les critères :
    - Market Cap > 50M$
    - Performance mensuelle > +10%
    - Volatilité mensuelle > 5%
    - Performance trimestrielle positive
    - RS Rating > 95 (force relative vs SPX)
    
    Returns:
        HttpResponse: Page HTML avec le tableau des résultats
    """
    try:
        # Exécuter le screener (code du notebook)
        df = run_screener()
        
        # Convertir le DataFrame en HTML avec style Bootstrap
        table_html = df.to_html(
            classes='table table-striped table-hover',
            index=False,
            border=0,
            escape=False,
            float_format=lambda x: f'{x:.2f}' if isinstance(x, float) else x
        )
        
        # Préparer le contexte pour le template
        context = {
            'table_html': table_html,
            'count': len(df),
            'success': True
        }
        
    except Exception as e:
        # En cas d'erreur, afficher un message
        context = {
            'table_html': None,
            'count': 0,
            'success': False,
            'error_message': str(e)
        }
    
    return render(request, 'screener.html', context)
