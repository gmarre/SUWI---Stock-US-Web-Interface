"""
Module de trading pour Interactive Brokers via Client Portal API
Gère les ordres bracket (market + TP/SL) et les vérifications
"""
import json
import os
import requests
import urllib3
import time

# Désactiver les warnings SSL pour localhost
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class IBTrader:
    """Classe pour gérer le trading via Interactive Brokers Client Portal API"""
    
    def __init__(self, base_url="https://localhost:5000/v1/api"):
        self.base_url = base_url
        self.config = self._load_config()
        
    def _load_config(self):
        """Charge la configuration depuis ib_config.json"""
        config_path = os.path.join(os.path.dirname(__file__), 'ib_config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_accounts(self):
        """
        Récupère la liste des comptes disponibles
        Returns: dict avec success et liste de comptes
        """
        try:
            response = requests.get(
                f"{self.base_url}/portfolio/accounts",
                verify=False,
                timeout=10
            )
            
            if response.status_code == 200:
                accounts_raw = response.json()
                account_ids = []
                for acc in accounts_raw:
                    if isinstance(acc, str):
                        account_ids.append(acc)
                    elif isinstance(acc, dict):
                        account_id = acc.get('accountId') or acc.get('id') or acc.get('account')
                        if account_id:
                            account_ids.append(account_id)
                
                return {
                    'success': True,
                    'accounts': account_ids
                }
            else:
                return {
                    'success': False,
                    'message': f'Erreur récupération comptes: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Erreur connexion: {str(e)}'
            }
    
    def get_account_balance(self, account_id):
        """
        Récupère le solde du compte
        Returns: dict avec success, balance (float) et currency
        """
        try:
            response = requests.get(
                f"{self.base_url}/portfolio/{account_id}/summary",
                verify=False,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Récupérer le cash disponible
                cash_balance = 0
                for item in data:
                    if item.get('key') == 'availablefunds':
                        cash_balance = float(item.get('value', 0))
                        break
                
                return {
                    'success': True,
                    'balance': cash_balance,
                    'currency': 'USD'
                }
            else:
                return {
                    'success': False,
                    'message': f'Erreur récupération solde: {response.status_code}',
                    'balance': 0
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Erreur: {str(e)}',
                'balance': 0
            }
    
    def search_contract(self, ticker):
        """
        Recherche le contrat IB pour un ticker
        Returns: dict avec success et conid (contract ID)
        """
        try:
            # Rechercher le ticker
            response = requests.get(
                f"{self.base_url}/iserver/secdef/search",
                params={'symbol': ticker},
                verify=False,
                timeout=10
            )
            
            if response.status_code == 200:
                results = response.json()
                
                # Chercher le premier contrat de type action US
                for contract in results:
                    if contract.get('sections', [{}])[0].get('secType') == 'STK':
                        conid = contract.get('conid')
                        if conid:
                            return {
                                'success': True,
                                'conid': conid,
                                'name': contract.get('description', ticker)
                            }
                
                return {
                    'success': False,
                    'message': f'Aucun contrat trouvé pour {ticker}'
                }
            else:
                return {
                    'success': False,
                    'message': f'Erreur recherche: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Erreur: {str(e)}'
            }
    
    def get_market_data(self, conid, ticker=None):
        """
        Récupère le prix actuel via market data snapshot
        Returns: dict avec success et price
        """
        try:
            # Essayer d'abord via IB market data
            response = requests.get(
                f"{self.base_url}/iserver/marketdata/snapshot",
                params={'conids': conid, 'fields': '31,84,86'},  # 31=last, 84=bid, 86=ask
                verify=False,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data and len(data) > 0:
                    snapshot = data[0]
                    
                    # Essayer de récupérer le dernier prix
                    price = snapshot.get('31')  # Last price
                    if not price:
                        price = snapshot.get('84')  # Bid
                    if not price:
                        price = snapshot.get('86')  # Ask
                    
                    if price:
                        return {
                            'success': True,
                            'price': float(price)
                        }
            
            # Si IB ne retourne pas de prix, essayer Yahoo Finance comme fallback
            if ticker:
                import yfinance as yf
                try:
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    
                    # Essayer plusieurs sources de prix
                    price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')
                    
                    if price and price > 0:
                        return {
                            'success': True,
                            'price': float(price)
                        }
                except:
                    pass
            
            return {
                'success': False,
                'message': 'Prix non disponible via IB et Yahoo Finance',
                'price': 0
            }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Erreur: {str(e)}',
                'price': 0
            }
    
    def place_bracket_order(self, ticker, action, quantity, take_profit_pct=None, stop_loss_price=None):
        """
        Place un ordre bracket (market + TP + SL) via Client Portal API
        
        Args:
            ticker: Symbol de l'action (ex: 'AAPL')
            action: 'BUY' ou 'SELL'
            quantity: Nombre d'actions
            take_profit_pct: % de take profit (optionnel)
            stop_loss_price: Prix du stop loss en dollars (optionnel)
            
        Returns: dict avec success, message, order_id, et détails
        """
        try:
            # 1. Récupérer les comptes
            accounts_result = self.get_accounts()
            if not accounts_result['success'] or not accounts_result['accounts']:
                return {
                    'success': False,
                    'message': 'Aucun compte IB disponible'
                }
            
            account_id = accounts_result['accounts'][0]
            
            # 2. Rechercher le contrat
            contract_result = self.search_contract(ticker)
            if not contract_result['success']:
                return {
                    'success': False,
                    'message': f"Impossible de trouver le contrat pour {ticker}"
                }
            
            conid = contract_result['conid']
            
            # 3. Récupérer le prix actuel (essayer IB puis Yahoo comme fallback)
            price_result = self.get_market_data(conid, ticker)
            if not price_result['success']:
                return {
                    'success': False,
                    'message': f"Impossible de récupérer le prix pour {ticker}: {price_result.get('message', 'Erreur inconnue')}"
                }
            
            current_price = price_result['price']
            
            # 4. Vérifier la valeur de l'ordre
            order_value = current_price * quantity
            max_value = self.config['max_order_value']
            
            if order_value > max_value:
                return {
                    'success': False,
                    'message': f'Ordre trop important: ${order_value:.2f} > limite ${max_value}'
                }
            
            # 5. Vérifier le solde (pour les achats)
            if action == 'BUY':
                balance_result = self.get_account_balance(account_id)
                if balance_result['success'] and balance_result['balance'] < order_value:
                    return {
                        'success': False,
                        'message': f"Solde insuffisant: ${balance_result['balance']:.2f} < ${order_value:.2f}"
                    }
            
            # 6. Construire l'ordre principal (Market Order)
            side = "BUY" if action == 'BUY' else "SELL"
            
            orders = []
            
            # Ordre principal
            main_order = {
                "conid": conid,
                "orderType": "MKT",
                "side": side,
                "quantity": quantity,
                "tif": "DAY"
            }
            
            # Ajouter le Stop Loss si spécifié
            if stop_loss_price and stop_loss_price > 0:
                main_order["stopPrice"] = stop_loss_price
            
            # Ajouter le Take Profit si spécifié
            if take_profit_pct and take_profit_pct > 0:
                if action == 'BUY':
                    tp_price = current_price * (1 + take_profit_pct / 100)
                else:
                    tp_price = current_price * (1 - take_profit_pct / 100)
                main_order["profitPrice"] = tp_price
            
            orders.append(main_order)
            
            # 7. Placer l'ordre
            response = requests.post(
                f"{self.base_url}/iserver/account/{account_id}/orders",
                json={"orders": orders},
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # L'API peut demander une confirmation
                if isinstance(result, list) and len(result) > 0:
                    order_response = result[0]
                    
                    # Si confirmation requise
                    if order_response.get('id'):
                        confirm_id = order_response['id']
                        
                        # Confirmer l'ordre
                        confirm_response = requests.post(
                            f"{self.base_url}/iserver/reply/{confirm_id}",
                            json={"confirmed": True},
                            verify=False,
                            timeout=30
                        )
                        
                        if confirm_response.status_code == 200:
                            confirm_result = confirm_response.json()
                            
                            if isinstance(confirm_result, list) and len(confirm_result) > 0:
                                final_result = confirm_result[0]
                                order_id = final_result.get('order_id', 'N/A')
                                
                                return {
                                    'success': True,
                                    'message': f"Ordre {action} placé pour {quantity} {ticker}",
                                    'order_id': order_id,
                                    'details': {
                                        'ticker': ticker,
                                        'action': action,
                                        'quantity': quantity,
                                        'price': current_price,
                                        'total_value': order_value,
                                        'take_profit': f"{take_profit_pct}%" if take_profit_pct else None,
                                        'stop_loss': f"${stop_loss_price:.2f}" if stop_loss_price else None
                                    }
                                }
                
                # Si pas de confirmation requise (ordre directement placé)
                return {
                    'success': True,
                    'message': f"Ordre {action} placé pour {quantity} {ticker}",
                    'order_id': result.get('order_id', 'N/A'),
                    'details': {
                        'ticker': ticker,
                        'action': action,
                        'quantity': quantity,
                        'price': current_price,
                        'total_value': order_value,
                        'take_profit': f"{take_profit_pct}%" if take_profit_pct else None,
                        'stop_loss': f"${stop_loss_price:.2f}" if stop_loss_price else None
                    }
                }
            else:
                return {
                    'success': False,
                    'message': f'Erreur placement ordre: {response.status_code} - {response.text}'
                }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Erreur placement ordre: {str(e)}'
            }
    
    def disconnect(self):
        """Pas besoin de déconnexion pour le Client Portal API"""
        pass


# Instance globale du trader
_trader_instance = None

def get_trader():
    """Récupère l'instance unique du trader"""
    global _trader_instance
    if _trader_instance is None:
        _trader_instance = IBTrader()
    return _trader_instance
