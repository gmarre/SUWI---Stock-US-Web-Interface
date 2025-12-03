"""
Module de gestion du risque dynamique
Calcule le pourcentage de risque basé sur le compteur de trades consécutifs
"""
from decimal import Decimal
from .models import RiskProfile, Trade


class RiskManager:
    """Gestionnaire de risque dynamique"""
    
    def __init__(self, account_id):
        self.account_id = account_id
        self.profile, _ = RiskProfile.objects.get_or_create(
            account_id=account_id,
            defaults={'base_risk_percent': Decimal('1.0')}
        )
    
    def get_current_risk_percent(self):
        """
        Retourne le pourcentage de risque actuel basé sur le compteur
        
        Returns:
            Decimal: Pourcentage de risque à utiliser
        """
        counter = self.profile.current_consecutive_counter
        base_risk = self.profile.base_risk_percent
        
        # Niveau AVANCE 3: [21, ...]
        if counter >= self.profile.advance_level_3_min:
            return base_risk * 8  # x8 du risque initial
        
        # Niveau AVANCE 2: [14, 20]
        elif counter >= self.profile.advance_level_2_min:
            return base_risk * 4  # x4 du risque initial
        
        # Niveau AVANCE 1: [7, 13]
        elif counter >= self.profile.advance_level_1_min:
            return base_risk * 2  # x2 du risque initial
        
        # Niveau STANDARD: [-4, 6]
        elif counter >= -4:
            return base_risk  # Risque de base
        
        # Niveau DRAWDOWN -1: [-5, -9]
        elif counter >= self.profile.drawdown_level_2_max:
            return base_risk / 2  # /2 du risque initial
        
        # Niveau DRAWDOWN -2: [-10, -14]
        elif counter >= self.profile.drawdown_level_3_max:
            return base_risk / 4  # /4 du risque initial
        
        # Niveau DRAWDOWN -3: [-15, -19]
        elif counter >= self.profile.drawdown_level_4_max:
            return base_risk / 8  # /8 du risque initial
        
        # Niveau DRAWDOWN -4: [-20, ...]
        else:
            return base_risk / 16  # /16 du risque initial
    
    def get_risk_level_name(self):
        """
        Retourne le nom du niveau de risque actuel
        
        Returns:
            str: Nom du niveau (ex: "AVANCE 2", "STANDARD", "DRAWDOWN -1")
        """
        counter = self.profile.current_consecutive_counter
        
        if counter >= self.profile.advance_level_3_min:
            return "AVANCE 3"
        elif counter >= self.profile.advance_level_2_min:
            return "AVANCE 2"
        elif counter >= self.profile.advance_level_1_min:
            return "AVANCE 1"
        elif counter >= -4:
            return "STANDARD"
        elif counter >= self.profile.drawdown_level_2_max:
            return "DRAWDOWN -1"
        elif counter >= self.profile.drawdown_level_3_max:
            return "DRAWDOWN -2"
        elif counter >= self.profile.drawdown_level_4_max:
            return "DRAWDOWN -3"
        else:
            return "DRAWDOWN -4"
    
    def calculate_position_size(self, capital, entry_price, sl_price):
        """
        Calcule la taille de position basée sur le risque actuel
        
        Args:
            capital: Capital total disponible
            entry_price: Prix d'entrée prévu
            sl_price: Prix du stop loss
            
        Returns:
            dict avec quantity (quantité), risk_amount (montant risqué), risk_percent
        """
        risk_percent = self.get_current_risk_percent()
        risk_amount = float(capital) * (float(risk_percent) / 100)
        
        # Distance entre entrée et SL
        risk_per_share = abs(float(entry_price) - float(sl_price))
        
        if risk_per_share == 0:
            return {
                'quantity': 0,
                'risk_amount': 0,
                'risk_percent': float(risk_percent),
                'error': 'Stop loss doit être différent du prix d\'entrée'
            }
        
        # Quantité = Montant risqué / Risque par action
        quantity = int(risk_amount / risk_per_share)
        
        return {
            'quantity': quantity,
            'risk_amount': round(risk_amount, 2),
            'risk_percent': float(risk_percent),
            'risk_per_share': round(risk_per_share, 2),
            'total_position_value': round(quantity * float(entry_price), 2)
        }
    
    def update_counter_after_trade(self, trade_won):
        """
        Met à jour le compteur après un trade fermé
        
        Args:
            trade_won: True si trade gagné, False si perdu
            
        Returns:
            int: Nouveau compteur
        """
        if trade_won:
            self.profile.current_consecutive_counter += 1
        else:
            self.profile.current_consecutive_counter -= 1
        
        self.profile.save()
        return self.profile.current_consecutive_counter
    
    def process_closed_trade(self, trade):
        """
        Traite un trade fermé et met à jour le compteur
        
        Args:
            trade: Instance du modèle Trade
            
        Returns:
            dict: Informations sur le traitement
        """
        if not trade.exit_date or not trade.pnl_dollar:
            return {
                'success': False,
                'error': 'Trade pas encore fermé'
            }
        
        # Déterminer si c'est un gain ou une perte
        trade_won = float(trade.pnl_dollar) > 0
        
        # Mettre à jour le compteur
        new_counter = self.update_counter_after_trade(trade_won)
        
        # Sauvegarder le compteur dans le trade
        trade.consecutive_counter_after = new_counter
        trade.save(update_fields=['consecutive_counter_after'])
        
        return {
            'success': True,
            'trade_won': trade_won,
            'new_counter': new_counter,
            'new_level': self.get_risk_level_name(),
            'new_risk_percent': float(self.get_current_risk_percent())
        }
    
    def get_risk_info(self):
        """
        Retourne toutes les informations de risque actuelles
        
        Returns:
            dict: Informations complètes
        """
        return {
            'counter': self.profile.current_consecutive_counter,
            'level': self.get_risk_level_name(),
            'risk_percent': float(self.get_current_risk_percent()),
            'base_risk_percent': float(self.profile.base_risk_percent),
            'account_id': self.account_id,
            'thresholds': {
                'advance_3': self.profile.advance_level_3_min,
                'advance_2': self.profile.advance_level_2_min,
                'advance_1': self.profile.advance_level_1_min,
                'drawdown_1': self.profile.drawdown_level_1_max,
                'drawdown_2': self.profile.drawdown_level_2_max,
                'drawdown_3': self.profile.drawdown_level_3_max,
                'drawdown_4': self.profile.drawdown_level_4_max,
            }
        }


def get_risk_manager(account_id):
    """
    Factory function pour obtenir un gestionnaire de risque
    
    Args:
        account_id: ID du compte IB
        
    Returns:
        RiskManager: Instance du gestionnaire
    """
    return RiskManager(account_id)
