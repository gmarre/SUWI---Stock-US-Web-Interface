"""
Gestionnaire de session Interactive Brokers
Gère le keepalive, la vérification du statut, et la ré-authentification automatique
"""
import requests
import threading
import time
import json
import os
from datetime import datetime, timedelta
import urllib3

# Désactiver les warnings SSL pour localhost
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class IBSessionManager:
    """Gestionnaire de session IB avec keepalive automatique"""
    
    def __init__(self):
        self.config = self._load_config()
        self.base_url = f"https://localhost:{self.config.get('gateway_port', 5000)}/v1/api"
        self.session_active = False
        self.authenticated = False
        self.last_tickle = None
        self.session_start = None
        self.tickle_thread = None
        self.running = False
        
    def _load_config(self):
        """Charge la configuration IB"""
        config_path = os.path.join(os.path.dirname(__file__), 'ib_config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def start(self):
        """Démarre le gestionnaire de session"""
        if not self.running:
            self.running = True
            self.tickle_thread = threading.Thread(target=self._keepalive_loop, daemon=True)
            self.tickle_thread.start()
            print("✅ IB Session Manager démarré")
    
    def stop(self):
        """Arrête le gestionnaire de session"""
        self.running = False
        if self.tickle_thread:
            self.tickle_thread.join(timeout=2)
        print("🛑 IB Session Manager arrêté")
    
    def _keepalive_loop(self):
        """Boucle de maintien de session (tickle toutes les 30 secondes)"""
        while self.running:
            try:
                # Vérifier le statut d'authentification
                status = self.check_auth_status()
                
                if status['success']:
                    self.authenticated = status['authenticated']
                    self.session_active = status['connected']
                    
                    if self.authenticated and self.session_active:
                        # Envoyer un tickle pour maintenir la session
                        self.tickle()
                        self.last_tickle = datetime.now()
                    else:
                        # Tenter une ré-authentification automatique
                        if self.session_start and (datetime.now() - self.session_start) < timedelta(hours=23):
                            print("⚠️ Session déconnectée, tentative de ré-authentification...")
                            self.attempt_reauth()
                
            except Exception as e:
                print(f"❌ Erreur dans keepalive loop: {e}")
            
            # Attendre 30 secondes avant la prochaine vérification
            time.sleep(30)
    
    def check_auth_status(self):
        """
        Vérifie le statut d'authentification via /iserver/auth/status
        Returns: dict avec success, authenticated, connected
        """
        try:
            response = requests.get(
                f"{self.base_url}/iserver/auth/status",
                verify=False,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'authenticated': data.get('authenticated', False),
                    'connected': data.get('connected', False),
                    'competing': data.get('competing', False),
                    'message': data.get('message', '')
                }
            else:
                return {
                    'success': False,
                    'authenticated': False,
                    'connected': False,
                    'error': f"Status code {response.status_code}"
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'authenticated': False,
                'connected': False,
                'error': f"Erreur de connexion: {str(e)}"
            }
    
    def tickle(self):
        """
        Envoie un tickle pour maintenir la session active
        Endpoint: POST /tickle
        """
        try:
            response = requests.post(
                f"{self.base_url}/tickle",
                verify=False,
                timeout=5
            )
            
            if response.status_code == 200:
                return {'success': True, 'message': 'Tickle envoyé'}
            else:
                return {'success': False, 'error': f"Status code {response.status_code}"}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def attempt_reauth(self):
        """
        Tente une ré-authentification automatique via SSODH
        Endpoint: POST /iserver/auth/ssodh/init
        """
        try:
            # Étape 1: Initialiser SSODH
            response = requests.post(
                f"{self.base_url}/iserver/auth/ssodh/init",
                verify=False,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Si une URL est retournée, l'utilisateur doit se reconnecter manuellement
                if 'url' in data:
                    print(f"⚠️ Reconnexion manuelle requise: {data['url']}")
                    return {
                        'success': False,
                        'manual_auth_required': True,
                        'auth_url': data['url']
                    }
                
                # Sinon, vérifier le nouveau statut
                new_status = self.check_auth_status()
                if new_status['authenticated']:
                    print("✅ Ré-authentification automatique réussie")
                    self.session_start = datetime.now()
                    return {'success': True, 'message': 'Ré-authentification réussie'}
                
            return {'success': False, 'error': 'Échec de la ré-authentification'}
            
        except Exception as e:
            print(f"❌ Erreur lors de la ré-authentification: {e}")
            return {'success': False, 'error': str(e)}
    
    def logout(self):
        """Déconnecte la session IB"""
        try:
            response = requests.post(
                f"{self.base_url}/logout",
                verify=False,
                timeout=5
            )
            
            if response.status_code == 200:
                self.authenticated = False
                self.session_active = False
                return {'success': True, 'message': 'Déconnexion réussie'}
            else:
                return {'success': False, 'error': f"Status code {response.status_code}"}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_session_info(self):
        """
        Retourne les informations de session pour l'interface utilisateur
        """
        status = self.check_auth_status()
        
        time_since_start = None
        time_until_expiry = None
        
        if self.session_start:
            time_since_start = datetime.now() - self.session_start
            # Session expire après 24h
            expiry_time = self.session_start + timedelta(hours=24)
            time_until_expiry = expiry_time - datetime.now()
        
        return {
            'authenticated': status.get('authenticated', False),
            'connected': status.get('connected', False),
            'competing': status.get('competing', False),
            'last_tickle': self.last_tickle.isoformat() if self.last_tickle else None,
            'session_start': self.session_start.isoformat() if self.session_start else None,
            'time_since_start_seconds': int(time_since_start.total_seconds()) if time_since_start else None,
            'time_until_expiry_seconds': int(time_until_expiry.total_seconds()) if time_until_expiry else None,
            'expires_soon': time_until_expiry and time_until_expiry < timedelta(hours=1) if time_until_expiry else False,
            'message': status.get('message', ''),
            'gateway_url': f"https://localhost:{self.config.get('gateway_port', 5000)}"
        }
    
    def mark_session_start(self):
        """Marque le début d'une nouvelle session (après login manuel)"""
        self.session_start = datetime.now()
        self.authenticated = True
        self.session_active = True
        print(f"✅ Session IB démarrée à {self.session_start}")


# Instance globale du gestionnaire de session
_session_manager = None

def get_session_manager():
    """Récupère l'instance unique du gestionnaire de session"""
    global _session_manager
    if _session_manager is None:
        _session_manager = IBSessionManager()
        _session_manager.start()
    return _session_manager
