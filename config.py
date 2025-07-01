
"""
🔧 Sistema de Configuración Robusto - Robot AI
Maneja configuración desde múltiples fuentes para máxima portabilidad
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any

class ConfigManager:
    """Gestor de configuración que busca credenciales en múltiples fuentes"""
    
    def __init__(self):
        self.config_sources = [
            self._load_from_env,
            self._load_from_config_file,
            self._load_from_json_files,
            self._load_from_replit_secrets
        ]
        
        self.config = self._load_configuration()
    
    def _load_from_env(self) -> Dict[str, Any]:
        """Carga configuración desde variables de entorno"""
        config = {}
        
        # OpenAI
        if os.getenv('OPENAI_API_KEY'):
            config['openai_api_key'] = os.getenv('OPENAI_API_KEY')
            print("✅ OpenAI API Key encontrado en variables de entorno")
        
        # Google Drive
        if os.getenv('GOOGLE_CREDENTIALS'):
            config['google_credentials'] = os.getenv('GOOGLE_CREDENTIALS')
            print("✅ Google Credentials encontrado en variables de entorno")
        elif os.getenv('GOOGLE_DRIVE_CREDENTIALS'):
            config['google_credentials'] = os.getenv('GOOGLE_DRIVE_CREDENTIALS')
            print("✅ Google Drive Credentials encontrado en variables de entorno")
        
        return config
    
    def _load_from_config_file(self) -> Dict[str, Any]:
        """Carga configuración desde archivo config.json"""
        config = {}
        config_file = Path('config.json')
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                
                if 'openai_api_key' in file_config:
                    config['openai_api_key'] = file_config['openai_api_key']
                    print("✅ OpenAI API Key encontrado en config.json")
                
                if 'google_credentials' in file_config:
                    config['google_credentials'] = json.dumps(file_config['google_credentials'])
                    print("✅ Google Credentials encontrado en config.json")
                
            except Exception as e:
                print(f"⚠️ Error leyendo config.json: {e}")
        
        return config
    
    def _load_from_json_files(self) -> Dict[str, Any]:
        """Carga configuración desde archivos JSON individuales"""
        config = {}
        
        # Buscar archivo de credenciales de Google
        google_files = [
            'google_credentials.json',
            'service_account.json',
            'credentials.json',
            'google_service_account.json'
        ]
        
        for filename in google_files:
            file_path = Path(filename)
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        credentials = json.load(f)
                    
                    # Validar que es un service account
                    if credentials.get('type') == 'service_account':
                        config['google_credentials'] = json.dumps(credentials)
                        print(f"✅ Google Credentials encontrado en {filename}")
                        break
                except Exception as e:
                    print(f"⚠️ Error leyendo {filename}: {e}")
        
        return config
    
    def _load_from_replit_secrets(self) -> Dict[str, Any]:
        """Carga configuración desde Replit Secrets"""
        config = {}
        
        try:
            # Intentar importar Replit
            import replit
            
            # OpenAI
            if hasattr(replit, 'Database'):
                db = replit.Database()
                if 'OPENAI_API_KEY' in db.keys():
                    config['openai_api_key'] = db['OPENAI_API_KEY']
                    print("✅ OpenAI API Key encontrado en Replit Secrets")
                
                if 'GOOGLE_CREDENTIALS' in db.keys():
                    config['google_credentials'] = db['GOOGLE_CREDENTIALS']
                    print("✅ Google Credentials encontrado en Replit Secrets")
        
        except ImportError:
            # No estamos en Replit, continuar
            pass
        except Exception as e:
            print(f"⚠️ Error accediendo a Replit Secrets: {e}")
        
        return config
    
    def _load_configuration(self) -> Dict[str, Any]:
        """Carga configuración desde todas las fuentes disponibles"""
        final_config = {}
        
        print("🔧 Cargando configuración desde múltiples fuentes...")
        
        for source_func in self.config_sources:
            try:
                source_config = source_func()
                # Las primeras fuentes tienen prioridad
                for key, value in source_config.items():
                    if key not in final_config:
                        final_config[key] = value
            except Exception as e:
                print(f"⚠️ Error en fuente de configuración: {e}")
        
        self._validate_configuration(final_config)
        return final_config
    
    def _validate_configuration(self, config: Dict[str, Any]):
        """Valida la configuración cargada"""
        print("\n🔍 Validando configuración...")
        
        # Validar OpenAI
        if 'openai_api_key' in config and config['openai_api_key']:
            if config['openai_api_key'].startswith('sk-'):
                print("✅ OpenAI API Key válido")
            else:
                print("⚠️ OpenAI API Key no parece válido (debería empezar con 'sk-')")
        else:
            print("❌ OpenAI API Key no configurado")
        
        # Validar Google Drive
        if 'google_credentials' in config and config['google_credentials']:
            try:
                creds = json.loads(config['google_credentials'])
                if creds.get('type') == 'service_account':
                    print("✅ Google Drive Service Account válido")
                else:
                    print("⚠️ Google Credentials no es un service account")
            except json.JSONDecodeError:
                print("❌ Google Credentials no es JSON válido")
        else:
            print("❌ Google Drive Credentials no configurado")
    
    def get_openai_api_key(self) -> Optional[str]:
        """Obtiene la API Key de OpenAI"""
        return self.config.get('openai_api_key')
    
    def get_google_credentials(self) -> Optional[str]:
        """Obtiene las credenciales de Google Drive"""
        return self.config.get('google_credentials')
    
    def is_fully_configured(self) -> bool:
        """Verifica si la configuración está completa"""
        return (
            self.get_openai_api_key() is not None and
            self.get_google_credentials() is not None
        )
    
    def get_configuration_status(self) -> Dict[str, Any]:
        """Obtiene el estado de la configuración"""
        return {
            'openai_configured': self.get_openai_api_key() is not None,
            'google_drive_configured': self.get_google_credentials() is not None,
            'fully_configured': self.is_fully_configured(),
            'sources_checked': len(self.config_sources),
            'config_keys_found': list(self.config.keys())
        }

# Instancia global del gestor de configuración
config_manager = ConfigManager()

def get_openai_api_key() -> Optional[str]:
    """Función helper para obtener OpenAI API Key"""
    return config_manager.get_openai_api_key()

def get_google_credentials() -> Optional[str]:
    """Función helper para obtener Google Credentials"""
    return config_manager.get_google_credentials()

def is_configured() -> bool:
    """Función helper para verificar si está configurado"""
    return config_manager.is_fully_configured()
