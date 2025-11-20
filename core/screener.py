"""
Module de screener boursier US - Finviz + RS Rating
Réutilise le code exact du notebook Jupyter Scraper_finviz.ipynb
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import warnings
from finvizfinance.screener.overview import Overview

# Ignorer les warnings
warnings.filterwarnings('ignore')


# ============================================
# CONSTANTES DES SEUILS RS RATING
# ============================================
SEUILS = {
    'first': 195.93,  # RS Score pour 99 (98ème percentile)
    'scnd':  117.11,  # RS Score pour 90 (89ème percentile)
    'thrd':  99.04,   # RS Score pour 70 (69ème percentile)
    'frth':  91.66,   # RS Score pour 50 (49ème percentile)
    'ffth':  80.96,   # RS Score pour 30 (29ème percentile)
    'sxth':  53.64,   # RS Score pour 10 (9ème percentile)
    'svth':  24.86    # RS Score pour 1  (1er percentile)
}


def calculate_rs_score(ticker_data, spx_data):
    """
    Calcule le RS Score (score de performance relative par rapport au SPX)
    
    Args:
        ticker_data: Series pandas des prix de clôture du ticker (252 jours minimum)
        spx_data: Series pandas des prix de clôture du SPX (252 jours minimum)
    
    Returns:
        float: RS Score ou np.nan si erreur
    """
    try:
        # Vérifier qu'on a assez de données
        if len(ticker_data) < 252 or len(spx_data) < 252:
            return np.nan

        # Récupérer les indices des 4 périodes
        n63  = min(62, len(ticker_data) - 1)
        n126 = min(125, len(ticker_data) - 1)
        n189 = min(188, len(ticker_data) - 1)
        n252 = min(251, len(ticker_data) - 1)

        # Performance du ticker
        perf_ticker_63  = ticker_data.iloc[-1][0] / ticker_data.iloc[-1-n63][0]
        perf_ticker_126 = ticker_data.iloc[-1][0] / ticker_data.iloc[-1-n126][0]
        perf_ticker_189 = ticker_data.iloc[-1][0] / ticker_data.iloc[-1-n189][0]
        perf_ticker_252 = ticker_data.iloc[-1][0] / ticker_data.iloc[-1-n252][0]

        # Performance du SPX
        perf_spx_63  = spx_data.iloc[-1][0] / spx_data.iloc[-1-n63][0]
        perf_spx_126 = spx_data.iloc[-1][0] / spx_data.iloc[-1-n126][0]
        perf_spx_189 = spx_data.iloc[-1][0] / spx_data.iloc[-1-n189][0]
        perf_spx_252 = spx_data.iloc[-1][0] / spx_data.iloc[-1-n252][0]

        # RS pondéré (40% poids sur 63j, 20% sur les autres)
        rs_stock = 0.4 * perf_ticker_63 + 0.2 * perf_ticker_126 + 0.2 * perf_ticker_189 + 0.2 * perf_ticker_252
        rs_ref   = 0.4 * perf_spx_63   + 0.2 * perf_spx_126   + 0.2 * perf_spx_189   + 0.2 * perf_spx_252

        # RS Score
        rs_score = (rs_stock / rs_ref) * 100

        return float(rs_score)
    except:
        return np.nan


def f_attribute_percentile(rs_score, taller_perf, smaller_perf, range_up, range_dn, weight):
    """
    Interpole linéairement pour attribuer un percentile entre deux seuils
    
    Args:
        rs_score: Score RS à convertir
        taller_perf: Seuil supérieur
        smaller_perf: Seuil inférieur
        range_up: Range supérieur
        range_dn: Range inférieur
        weight: Poids d'interpolation
    
    Returns:
        float: Rating interpolé ou np.nan si erreur
    """
    try:
        sum_val = rs_score + (rs_score - smaller_perf) * weight
        if sum_val > taller_perf - 1:
            sum_val = taller_perf - 1

        k1 = smaller_perf / range_dn
        k2 = (taller_perf - 1) / range_up
        k3 = (k1 - k2) / (taller_perf - 1 - smaller_perf)
        rs_rating = sum_val / (k1 - k3 * (rs_score - smaller_perf))

        if rs_rating > range_up:
            rs_rating = range_up
        if rs_rating < range_dn:
            rs_rating = range_dn

        return rs_rating
    except:
        return np.nan


def calculate_rs_rating(rs_score):
    """
    Convertit le RS Score en RS Rating (échelle 1-99)
    
    Args:
        rs_score: Score RS calculé
    
    Returns:
        float: RS Rating entre 1 et 99, ou np.nan si invalide
    """
    if pd.isna(rs_score):
        return np.nan

    first, scnd, thrd, frth, ffth, sxth, svth = (
        SEUILS['first'], SEUILS['scnd'], SEUILS['thrd'], SEUILS['frth'],
        SEUILS['ffth'], SEUILS['sxth'], SEUILS['svth']
    )

    if rs_score >= first:
        return 99
    if rs_score <= svth:
        return 1
    if rs_score < first and rs_score >= scnd:
        return f_attribute_percentile(rs_score, first, scnd, 98, 90, 0.33)
    if rs_score < scnd and rs_score >= thrd:
        return f_attribute_percentile(rs_score, scnd, thrd, 89, 70, 2.1)
    if rs_score < thrd and rs_score >= frth:
        return f_attribute_percentile(rs_score, thrd, frth, 69, 50, 0)
    if rs_score < frth and rs_score >= ffth:
        return f_attribute_percentile(rs_score, frth, ffth, 49, 30, 0)
    if rs_score < ffth and rs_score >= sxth:
        return f_attribute_percentile(rs_score, ffth, sxth, 29, 10, 0)
    if rs_score < sxth and rs_score >= svth:
        return f_attribute_percentile(rs_score, sxth, svth, 9, 2, 0)

    return np.nan


def add_rs_rating_to_df(df, ticker_column='Ticker', lookback_days=252):
    """
    Ajoute les colonnes RS_Score et RS_Rating à un DataFrame de tickers
    
    Args:
        df: DataFrame pandas contenant les tickers
        ticker_column: Nom de la colonne contenant les symboles boursiers
        lookback_days: Nombre de jours historiques à analyser (défaut: 252)
    
    Returns:
        DataFrame: DataFrame enrichi avec RS_Score et RS_Rating
    """
    print("📥 Téléchargement des données SPX...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=368)

    try:
        spx_data = yf.download('^GSPC', start=start_date, end=end_date, progress=False)['Close']
    except:
        print("❌ Erreur téléchargement SPX")
        return df

    rs_ratings = []
    rs_scores = []

    print(f"📊 Calcul RS Rating pour {len(df)} actions...\n")

    for idx, row in df.iterrows():
        ticker = row[ticker_column].strip()

        try:
            # Télécharger les données du ticker
            ticker_data = yf.download(ticker, start=start_date, end=end_date, progress=False)['Close']

            # Calculer le RS Score
            rs_score = calculate_rs_score(ticker_data, spx_data)

            # Convertir en RS Rating
            rs_rating = calculate_rs_rating(rs_score)

            rs_ratings.append(rs_rating)
            rs_scores.append(rs_score)

            status = f"✓ {ticker}: Score={rs_score:.2f} | Rating={rs_rating:.1f}" if not pd.isna(rs_rating) else f"⚠ {ticker}: Données insuffisantes"
            print(f"{idx+1:3d}. {status}")

        except Exception as e:
            print(f"{idx+1:3d}. ✗ {ticker}: Erreur ({str(e)[:30]})")
            rs_scores.append(np.nan)
            rs_ratings.append(np.nan)

    df['RS_Score'] = rs_scores
    df['RS_Rating'] = rs_ratings

    print(f"\n✅ Calcul terminé!\n")

    return df


def run_screener(custom_filters=None, rs_rating_min=95):
    """
    Fonction principale : exécute le screener Finviz avec les critères définis
    et calcule le RS Rating pour chaque action
    
    Args:
        custom_filters: Dictionnaire personnalisé de filtres Finviz (optionnel)
        rs_rating_min: RS Rating minimum pour filtrer les résultats (défaut: 95)
    
    Critères du screener par défaut :
    - Pays : USA
    - Market Cap : > 50M$ (Micro cap et plus)
    - Performance mensuelle : +10%
    - Volatilité mensuelle : > 5%
    - Performance trimestrielle : positive
    
    Returns:
        DataFrame: DataFrame pandas avec toutes les actions filtrées et leur RS Rating
                   Filtré pour ne garder que les actions avec RS_Rating > rs_rating_min
    """
    print("🔍 Lancement du screener Finviz...")
    
    # Initialiser le screener Finviz
    foverview = Overview()
    
    # Utiliser les filtres personnalisés ou les filtres par défaut
    if custom_filters is None:
        filters_dict = {
            'Country': 'USA',
            'Market Cap.': "+Micro (over $50mln)",
            'Performance': 'Month +10%',
            'Volatility': 'Month - Over 5%',
            'Performance 2': 'Quarter Up'
        }
    else:
        # Créer le dictionnaire pour Finviz (sans RS_Rating_Min)
        filters_dict = {k: v for k, v in custom_filters.items() if k != 'RS_Rating_Min'}
    
    # Appliquer les filtres
    foverview.set_filter(filters_dict=filters_dict)
    
    # Récupérer les résultats
    print("📊 Récupération des données Finviz...")
    df = foverview.screener_view()
    
    print(f"✅ {len(df)} actions trouvées avant filtrage RS\n")
    
    # Calculer le RS Rating pour chaque action
    df = add_rs_rating_to_df(df, ticker_column='Ticker')
    
    # Filtrer pour ne garder que les actions avec RS_Rating > rs_rating_min
    df_filtered = df[df['RS_Rating'] > rs_rating_min]
    
    print(f"\n🎯 {len(df_filtered)} actions avec RS_Rating > {rs_rating_min}")
    
    return df_filtered
