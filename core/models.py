from django.db import models


class Watchlist(models.Model):
    """
    Modèle représentant une watchlist (liste de surveillance).
    """
    # Choix de couleurs prédéfinies
    COLOR_CHOICES = [
        ('#dc3545', 'Rouge'),
        ('#fd7e14', 'Orange'),
        ('#ffc107', 'Jaune'),
        ('#28a745', 'Vert'),
        ('#20c997', 'Turquoise'),
        ('#17a2b8', 'Cyan'),
        ('#007bff', 'Bleu'),
        ('#6610f2', 'Violet'),
        ('#e83e8c', 'Rose'),
        ('#6c757d', 'Gris'),
    ]
    
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom")
    color = models.CharField(
        max_length=7, 
        choices=COLOR_CHOICES, 
        default='#007bff',
        verbose_name="Couleur"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de mise à jour")
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = "Watchlist"
        verbose_name_plural = "Watchlists"
    
    def __str__(self):
        return self.name
    
    def stock_count(self):
        """Retourne le nombre d'actions dans cette watchlist"""
        return self.stocks.count()
    
    def get_color_name(self):
        """Retourne le nom de la couleur"""
        return dict(self.COLOR_CHOICES).get(self.color, 'Bleu')


class WatchlistStock(models.Model):
    """
    Modèle représentant un ticker dans une watchlist.
    """
    watchlist = models.ForeignKey(
        Watchlist, 
        on_delete=models.CASCADE, 
        related_name='stocks',
        verbose_name="Watchlist"
    )
    ticker = models.CharField(max_length=10, verbose_name="Ticker")
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'ajout")
    notes = models.TextField(blank=True, verbose_name="Notes")
    
    class Meta:
        ordering = ['ticker']
        unique_together = ['watchlist', 'ticker']
        verbose_name = "Action dans watchlist"
        verbose_name_plural = "Actions dans watchlist"
    
    def __str__(self):
        return f"{self.ticker} - {self.watchlist.name}"


class Trade(models.Model):
    """
    Modèle représentant un trade historique.
    """
    EXIT_TYPE_CHOICES = [
        ('TP', 'Take Profit'),
        ('SL', 'Stop Loss'),
        ('MANUAL', 'Manuel'),
    ]
    
    # Informations du trade
    ticker = models.CharField(max_length=10, verbose_name="Ticker")
    account_id = models.CharField(max_length=50, verbose_name="Compte IB")
    quantity = models.IntegerField(verbose_name="Quantité")
    
    # Prix d'entrée et sortie
    entry_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix d'entrée")
    entry_date = models.DateTimeField(verbose_name="Date d'entrée")
    exit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Prix de sortie")
    exit_date = models.DateTimeField(null=True, blank=True, verbose_name="Date de sortie")
    
    # Stop Loss et Take Profit
    sl_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Stop Loss")
    tp_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Take Profit")
    
    # P&L et Risk/Reward
    pnl_dollar = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="P&L ($)")
    pnl_percent = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="P&L (%)")
    risk_reward = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Risk/Reward (R)")
    
    # Type de sortie
    exit_type = models.CharField(max_length=10, choices=EXIT_TYPE_CHOICES, null=True, blank=True, verbose_name="Type de sortie")
    
    # Métadonnées
    ib_order_id = models.CharField(max_length=50, null=True, blank=True, verbose_name="ID ordre IB")
    consecutive_counter_after = models.IntegerField(default=0, verbose_name="Compteur après ce trade")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de mise à jour")
    notes = models.TextField(blank=True, verbose_name="Notes")
    
    class Meta:
        ordering = ['-entry_date']
        verbose_name = "Trade"
        verbose_name_plural = "Trades"
    
    def __str__(self):
        status = "Ouvert" if self.exit_date is None else "Fermé"
        return f"{self.ticker} - {self.quantity} @ {self.entry_price} ({status})"
    
    def calculate_risk_reward(self):
        """
        Calcule le Risk/Reward: R = (Exit - Entry) / (Entry - SL)
        Retourne None si les données sont manquantes
        """
        if self.exit_price and self.entry_price and self.sl_price:
            denominator = float(self.entry_price) - float(self.sl_price)
            if denominator != 0:
                numerator = float(self.exit_price) - float(self.entry_price)
                return round(numerator / denominator, 2)
        return None
    
    def save(self, *args, **kwargs):
        """Calcule automatiquement le R avant de sauvegarder"""
        if self.exit_price:
            # Calcul P&L
            if self.entry_price:
                self.pnl_dollar = (self.exit_price - self.entry_price) * self.quantity
                self.pnl_percent = ((self.exit_price - self.entry_price) / self.entry_price) * 100
            
            # Calcul Risk/Reward
            self.risk_reward = self.calculate_risk_reward()
        
        super().save(*args, **kwargs)


class RiskProfile(models.Model):
    """
    Modèle pour stocker la configuration de gestion du risque
    """
    account_id = models.CharField(max_length=50, unique=True, verbose_name="Compte IB")
    
    # Risque initial (niveau STANDARD)
    base_risk_percent = models.DecimalField(max_digits=5, decimal_places=2, default=1.0, verbose_name="Risque de base (%)")
    
    # Seuils pour les niveaux AVANCE
    advance_level_1_min = models.IntegerField(default=7, verbose_name="Niveau AVANCE 1 min")
    advance_level_2_min = models.IntegerField(default=14, verbose_name="Niveau AVANCE 2 min")
    advance_level_3_min = models.IntegerField(default=21, verbose_name="Niveau AVANCE 3 min")
    
    # Seuils pour les niveaux DRAWDOWN
    drawdown_level_1_max = models.IntegerField(default=-5, verbose_name="Niveau DRAWDOWN 1 max")
    drawdown_level_2_max = models.IntegerField(default=-10, verbose_name="Niveau DRAWDOWN 2 max")
    drawdown_level_3_max = models.IntegerField(default=-15, verbose_name="Niveau DRAWDOWN 3 max")
    drawdown_level_4_max = models.IntegerField(default=-20, verbose_name="Niveau DRAWDOWN 4 max")
    
    # Compteur actuel de trades consécutifs
    current_consecutive_counter = models.IntegerField(default=0, verbose_name="Compteur actuel")
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de mise à jour")
    
    class Meta:
        verbose_name = "Profil de Risque"
        verbose_name_plural = "Profils de Risque"
    
    def __str__(self):
        return f"Profil de risque - {self.account_id}"
