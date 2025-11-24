"""
Script de diagnostic pour tester l'API Yahoo Finance
"""
import yfinance as yf
from datetime import datetime, timedelta
import time
import pandas as pd

# Liste de tickers à tester
test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'ACRS', 'ADMA', 'AENT', 'ALB']

print("🔍 Test de l'API Yahoo Finance")
print("=" * 60)

end_date = datetime.now()
start_date = end_date - timedelta(days=368)

print(f"Période: {start_date.strftime('%Y-%m-%d')} à {end_date.strftime('%Y-%m-%d')}")
print(f"Nombre de jours: {(end_date - start_date).days}")
print("=" * 60)

success_count = 0
fail_count = 0

for ticker in test_tickers:
    try:
        print(f"\n📊 Test de {ticker}...", end=" ")
        data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        
        if data.empty:
            print(f"❌ Aucune donnée retournée")
            fail_count += 1
        else:
            # Extraire la colonne Close
            if isinstance(data.columns, pd.MultiIndex):
                close_data = data['Close']
            else:
                close_data = data
            
            data_len = len(close_data)
            first_date = close_data.index[0].strftime('%Y-%m-%d')
            last_date = close_data.index[-1].strftime('%Y-%m-%d')
            
            print(f"✅ {data_len} jours de données")
            print(f"   Du {first_date} au {last_date}")
            
            if data_len < 200:
                print(f"   ⚠️ Données insuffisantes (< 200 jours)")
                fail_count += 1
            else:
                print(f"   ✓ Données suffisantes")
                success_count += 1
        
        # Petit délai pour éviter le rate limiting
        time.sleep(0.2)
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        fail_count += 1

print("\n" + "=" * 60)
print(f"Résultats: {success_count} succès, {fail_count} échecs sur {len(test_tickers)} tests")
print("=" * 60)

if fail_count > success_count:
    print("\n⚠️ Problème détecté avec l'API Yahoo Finance!")
    print("Causes possibles:")
    print("  - Rate limiting (trop de requêtes)")
    print("  - Problème temporaire de l'API")
    print("  - Tickers invalides ou délistés")
    print("\nRecommandations:")
    print("  - Attendre quelques minutes avant de relancer")
    print("  - Réduire le nombre d'actions à analyser")
    print("  - Vérifier que les tickers sont valides")
else:
    print("\n✅ L'API Yahoo Finance semble fonctionner correctement")
