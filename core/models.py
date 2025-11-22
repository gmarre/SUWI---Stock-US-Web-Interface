from django.db import models


class Watchlist(models.Model):
    """
    Modèle représentant une watchlist (liste de surveillance).
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom")
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
