"""
Module de gestion du portefeuille Interactive Brokers
Récupère les positions actuelles et calcule les P&L en temps réel
"""
import requests
import urllib3
from datetime import datetime

# Désactiver les warnings SSL pour localhost
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class IBPortfolioManager:
    """Gestionnaire de portefeuille IB"""
    
    def __init__(self, base_url="https://localhost:5000/v1/api"):
        self.base_url = base_url
    
    def get_accounts(self):
        """
        Récupère la liste des comptes disponibles
        Returns: dict avec success et liste de comptes (array de strings)
        """
        try:
            response = requests.get(
                f"{self.base_url}/portfolio/accounts",
                verify=False,
                timeout=10
            )
            
            if response.status_code == 200:
                accounts_raw = response.json()
                
                # Extraire les IDs de compte (peut être des strings ou des objets)
                account_ids = []
                for acc in accounts_raw:
                    if isinstance(acc, str):
                        account_ids.append(acc)
                    elif isinstance(acc, dict):
                        # Essayer différentes clés possibles
                        account_id = acc.get('accountId') or acc.get('id') or acc.get('account')
                        if account_id:
                            account_ids.append(account_id)
                
                return {
                    'success': True,
                    'accounts': account_ids
                }
            elif response.status_code == 401:
                return {
                    'success': False,
                    'error': 'Non authentifié. Veuillez vous connecter à IB Gateway.',
                    'accounts': []
                }
            else:
                return {
                    'success': False,
                    'error': f"Status code {response.status_code}",
                    'accounts': []
                }
                
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'Impossible de se connecter à IB Gateway. Vérifiez que le Gateway est démarré sur localhost:5000',
                'accounts': []
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'accounts': []
            }
    
    def get_portfolio_positions(self, account_id):
        """
        Récupère les positions du portefeuille pour un compte
        
        Args:
            account_id: ID du compte IB
            
        Returns: dict avec success et liste de positions
        """
        try:
            response = requests.get(
                f"{self.base_url}/portfolio/{account_id}/positions/0",
                verify=False,
                timeout=15
            )
            
            if response.status_code == 200:
                positions_raw = response.json()
                
                # Parser et enrichir les positions
                positions = []
                for pos in positions_raw:
                    position = self._parse_position(pos)
                    if position:
                        positions.append(position)
                
                return {
                    'success': True,
                    'positions': positions,
                    'count': len(positions)
                }
            elif response.status_code == 401:
                return {
                    'success': False,
                    'error': 'Status code 401 - Non authentifié avec IB Gateway',
                    'positions': []
                }
            else:
                return {
                    'success': False,
                    'error': f"Status code {response.status_code}",
                    'positions': []
                }
                
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'Connexion impossible à IB Gateway (localhost:5000)',
                'positions': []
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'positions': []
            }
    
    def _parse_position(self, raw_position):
        """
        Parse une position brute de l'API IB
        
        Args:
            raw_position: dict de l'API IB
            
        Returns: dict position formatée
        """
        try:
            # Extraire les données principales
            ticker = raw_position.get('contractDesc', raw_position.get('ticker', 'N/A'))
            position_qty = float(raw_position.get('position', 0))
            
            # Prix et valeurs
            avg_price = float(raw_position.get('avgPrice', 0))
            market_price = float(raw_position.get('mktPrice', 0))
            market_value = float(raw_position.get('mktValue', 0))
            
            # P&L
            unrealized_pnl = float(raw_position.get('unrealizedPnl', 0))
            realized_pnl = float(raw_position.get('realizedPnl', 0))
            
            # Calcul du P&L en %
            if avg_price != 0:
                pnl_percent = ((market_price - avg_price) / avg_price) * 100
            else:
                pnl_percent = 0
            
            return {
                'ticker': ticker,
                'quantity': position_qty,
                'avg_price': avg_price,
                'current_price': market_price,
                'market_value': market_value,
                'unrealized_pnl': unrealized_pnl,
                'realized_pnl': realized_pnl,
                'pnl_percent': pnl_percent,
                'position_type': 'LONG' if position_qty > 0 else 'SHORT',
                'conid': raw_position.get('conid'),
                'currency': raw_position.get('currency', 'USD')
            }
            
        except Exception as e:
            print(f"Erreur parsing position: {e}")
            return None
    
    def get_orders_for_position(self, account_id, conid):
        """
        Récupère les ordres associés à une position (pour trouver SL/TP)
        
        Args:
            account_id: ID du compte
            conid: Contract ID de la position
            
        Returns: dict avec SL et TP si trouvés
        """
        try:
            # Récupérer tous les ordres actifs
            response = requests.get(
                f"{self.base_url}/iserver/account/orders",
                verify=False,
                timeout=10
            )
            
            if response.status_code != 200:
                return {'stop_loss': None, 'take_profit': None}
            
            orders = response.json().get('orders', [])
            
            sl_price = None
            tp_price = None
            
            # Chercher les ordres SL/TP pour ce conid
            for order in orders:
                if order.get('conid') == conid:
                    order_type = order.get('orderType', '').upper()
                    price = order.get('price') or order.get('auxPrice')
                    
                    if order_type in ['STP', 'STOP']:
                        sl_price = float(price) if price else None
                    elif order_type in ['LMT', 'LIMIT']:
                        tp_price = float(price) if price else None
            
            return {
                'stop_loss': sl_price,
                'take_profit': tp_price
            }
            
        except Exception as e:
            print(f"Erreur récupération ordres: {e}")
            return {'stop_loss': None, 'take_profit': None}
    
    def get_enriched_positions(self, account_id):
        """
        Récupère les positions enrichies avec SL/TP
        
        Args:
            account_id: ID du compte IB
            
        Returns: dict avec positions complètes
        """
        # Récupérer les positions
        positions_result = self.get_portfolio_positions(account_id)
        
        if not positions_result['success']:
            return positions_result
        
        positions = positions_result['positions']
        
        # Enrichir avec SL/TP
        for position in positions:
            conid = position.get('conid')
            if conid:
                orders = self.get_orders_for_position(account_id, conid)
                position['stop_loss'] = orders['stop_loss']
                position['take_profit'] = orders['take_profit']
            else:
                position['stop_loss'] = None
                position['take_profit'] = None
        
        return {
            'success': True,
            'positions': positions,
            'count': len(positions)
        }
    
    def get_account_summary(self, account_id):
        """
        Récupère le résumé du compte (capital, liquidité, etc.)
        
        Args:
            account_id: ID du compte IB
            
        Returns: dict avec success et informations du compte
        """
        try:
            response = requests.get(
                f"{self.base_url}/portfolio/{account_id}/summary",
                verify=False,
                timeout=10
            )
            
            if response.status_code == 200:
                summary_raw = response.json()
                
                # Parser les informations importantes
                account_info = {}
                
                # L'API retourne un dict avec des clés comme 'totalcashvalue', 'netliquidation', etc.
                for key, value in summary_raw.items():
                    if isinstance(value, dict) and 'amount' in value:
                        account_info[key] = float(value['amount'])
                    elif isinstance(value, (int, float, str)):
                        try:
                            account_info[key] = float(value)
                        except (ValueError, TypeError):
                            account_info[key] = value
                
                # Extraire les valeurs principales
                net_liquidation = account_info.get('netliquidation', 0) or account_info.get('NetLiquidation', 0)
                total_cash = account_info.get('totalcashvalue', 0) or account_info.get('TotalCashValue', 0)
                buying_power = account_info.get('buyingpower', 0) or account_info.get('BuyingPower', 0)
                equity = account_info.get('equitywithloanvalue', 0) or account_info.get('EquityWithLoanValue', 0)
                
                return {
                    'success': True,
                    'account_id': account_id,
                    'net_liquidation': net_liquidation,  # Valeur nette totale
                    'total_cash': total_cash,  # Liquidités
                    'buying_power': buying_power,  # Pouvoir d'achat
                    'equity_with_loan': equity,  # Capitaux propres
                    'raw_data': account_info  # Données brutes complètes
                }
            elif response.status_code == 401:
                return {
                    'success': False,
                    'error': 'Non authentifié avec IB Gateway'
                }
            else:
                return {
                    'success': False,
                    'error': f"Status code {response.status_code}"
                }
                
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'Connexion impossible à IB Gateway'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


# Instance globale
_portfolio_manager = None

def get_portfolio_manager():
    """Récupère l'instance unique du gestionnaire de portefeuille"""
    global _portfolio_manager
    if _portfolio_manager is None:
        _portfolio_manager = IBPortfolioManager()
    return _portfolio_manager
