"""
Module de trading pour Interactive Brokers
Gère la connexion, les ordres bracket (market + TP/SL), et les vérifications
"""
import json
import os
import asyncio
from ib_insync import IB, Stock, MarketOrder, Order, LimitOrder
from decimal import Decimal


class IBTrader:
    """Classe pour gérer le trading via Interactive Brokers"""
    
    def __init__(self):
        self.ib = IB()
        self.config = self._load_config()
        self.connected = False
        self._ensure_event_loop()
        
    def _ensure_event_loop(self):
        """S'assure qu'un event loop existe pour le thread actuel"""
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
    def _load_config(self):
        """Charge la configuration depuis ib_config.json"""
        config_path = os.path.join(os.path.dirname(__file__), 'ib_config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def connect(self):
        """
        Connecte à IB Gateway/TWS
        Returns: dict avec success et message
        """
        try:
            if self.connected:
                return {'success': True, 'message': 'Déjà connecté'}
            
            self.ib.connect(
                host=self.config['host'],
                port=self.config['port'],
                clientId=self.config['client_id']
            )
            self.connected = True
            
            return {
                'success': True,
                'message': f"Connecté à IB Gateway (Paper Trading: {self.config['paper_trading']})"
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Erreur de connexion: {str(e)}'
            }
    
    def disconnect(self):
        """Déconnecte d'IB"""
        if self.connected:
            self.ib.disconnect()
            self.connected = False
    
    def get_account_balance(self):
        """
        Récupère le solde du compte
        Returns: dict avec success, balance (float) et currency
        """
        try:
            self._ensure_event_loop()
            if not self.connected:
                connect_result = self.connect()
                if not connect_result['success']:
                    return connect_result
            
            # Récupérer les infos du compte
            account_values = self.ib.accountValues()
            
            # Chercher le cash disponible
            cash_balance = 0
            currency = 'USD'
            
            for value in account_values:
                if value.tag == 'CashBalance' and value.currency == 'USD':
                    cash_balance = float(value.value)
                    currency = value.currency
                    break
            
            return {
                'success': True,
                'balance': cash_balance,
                'currency': currency
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Erreur récupération solde: {str(e)}',
                'balance': 0
            }
    
    def get_current_price(self, ticker):
        """
        Récupère le prix actuel d'une action
        Returns: dict avec success et price (float)
        """
        try:
            self._ensure_event_loop()
            if not self.connected:
                connect_result = self.connect()
                if not connect_result['success']:
                    return connect_result
            
            # Créer le contrat
            contract = Stock(ticker, 'SMART', 'USD')
            self.ib.qualifyContracts(contract)
            
            # Demander les données de marché
            ticker_data = self.ib.reqMktData(contract, '', False, False)
            self.ib.sleep(2)  # Attendre les données
            
            # Récupérer le dernier prix
            price = ticker_data.marketPrice()
            
            if price and price > 0:
                return {
                    'success': True,
                    'price': float(price)
                }
            else:
                # Fallback sur le dernier prix de clôture
                price = ticker_data.close
                return {
                    'success': True,
                    'price': float(price) if price else 0
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Erreur récupération prix: {str(e)}',
                'price': 0
            }
    
    def place_bracket_order(self, ticker, action, quantity, take_profit_pct=None, stop_loss_price=None):
        """
        Place un ordre bracket (market + TP + SL)
        
        Args:
            ticker: Symbol de l'action (ex: 'AAPL')
            action: 'BUY' ou 'SELL'
            quantity: Nombre d'actions
            take_profit_pct: % de take profit (optionnel)
            stop_loss_price: Prix du stop loss en dollars (optionnel)
            
        Returns: dict avec success, message, order_id, et détails
        """
        try:
            self._ensure_event_loop()
            if not self.connected:
                connect_result = self.connect()
                if not connect_result['success']:
                    return connect_result
            
            # 1. Récupérer le prix actuel
            price_result = self.get_current_price(ticker)
            if not price_result['success']:
                return price_result
            
            current_price = price_result['price']
            
            # 2. Calculer la valeur de l'ordre
            order_value = current_price * quantity
            
            # 3. Vérifier la limite de 5000$
            max_value = self.config['max_order_value']
            if order_value > max_value:
                return {
                    'success': False,
                    'message': f'Ordre trop important: ${order_value:.2f} > limite ${max_value}'
                }
            
            # 4. Vérifier le solde (pour les achats)
            if action == 'BUY':
                balance_result = self.get_account_balance()
                if not balance_result['success']:
                    return balance_result
                
                if balance_result['balance'] < order_value:
                    return {
                        'success': False,
                        'message': f"Solde insuffisant: ${balance_result['balance']:.2f} < ${order_value:.2f}"
                    }
            
            # 5. Créer le contrat
            contract = Stock(ticker, 'SMART', 'USD')
            self.ib.qualifyContracts(contract)
            
            # 6. Créer l'ordre principal (Market Order)
            parent_order = MarketOrder(action, quantity)
            parent_order.orderId = self.ib.client.getReqId()
            parent_order.transmit = False  # Ne pas envoyer immédiatement
            
            orders = [parent_order]
            
            # 7. Ajouter le Take Profit si spécifié
            if take_profit_pct and take_profit_pct > 0:
                if action == 'BUY':
                    tp_price = current_price * (1 + take_profit_pct / 100)
                    tp_action = 'SELL'
                else:
                    tp_price = current_price * (1 - take_profit_pct / 100)
                    tp_action = 'BUY'
                
                tp_order = LimitOrder(tp_action, quantity, tp_price)
                tp_order.orderId = self.ib.client.getReqId()
                tp_order.parentId = parent_order.orderId
                tp_order.transmit = False
                orders.append(tp_order)
            
            # 8. Ajouter le Stop Loss si spécifié
            if stop_loss_price and stop_loss_price > 0:
                # Déterminer l'action pour le SL
                if action == 'BUY':
                    sl_action = 'SELL'
                else:
                    sl_action = 'BUY'
                
                sl_order = Order()
                sl_order.action = sl_action
                sl_order.orderType = 'STP'
                sl_order.auxPrice = stop_loss_price
                sl_order.totalQuantity = quantity
                sl_order.orderId = self.ib.client.getReqId()
                sl_order.parentId = parent_order.orderId
                sl_order.transmit = True  # Le dernier ordre déclenche l'envoi
                orders.append(sl_order)
            else:
                # Si pas de SL, le dernier ordre (TP ou parent) doit transmettre
                orders[-1].transmit = True
            
            # 9. Placer les ordres
            trades = []
            for order in orders:
                trade = self.ib.placeOrder(contract, order)
                trades.append(trade)
            
            # 10. Attendre la confirmation
            self.ib.sleep(2)
            
            return {
                'success': True,
                'message': f"Ordre {action} placé pour {quantity} {ticker}",
                'order_id': parent_order.orderId,
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
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Erreur placement ordre: {str(e)}'
            }


# Instance globale du trader (singleton)
_trader_instance = None

def get_trader():
    """Récupère l'instance unique du trader"""
    global _trader_instance
    if _trader_instance is None:
        _trader_instance = IBTrader()
    return _trader_instance
