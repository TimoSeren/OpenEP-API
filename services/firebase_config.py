"""
Firebase Remote Config Service.
Ruft die verschlüsselten Credentials von Firebase ab und entschlüsselt sie.
"""

import base64
import logging
import os
import re
from typing import Optional

import httpx

from config import Settings, get_settings
from services.crypto import decrypt_blowfish

logger = logging.getLogger(__name__)

FIREBASE_ID_PATTERN = re.compile(r'^[cdef][\w-]{21}$')


def generate_firebase_id() -> str:
    """Generiert eine Firebase Installation ID im korrekten Format."""
    try:
        fid_bytes = bytearray(os.urandom(17))
        fid_bytes[0] = 0b01110000 + (fid_bytes[0] % 0b00010000)
        
        b64_string = base64.b64encode(bytes(fid_bytes)).decode('utf-8')
        b64_string = b64_string.replace('+', '-').replace('/', '_')
        fid = b64_string[:22]
        
        if FIREBASE_ID_PATTERN.match(fid):
            return fid
        return ""
    except Exception as e:
        logger.error(f"Fehler beim Generieren der Firebase ID: {e}")
        return ""


class FirebaseConfigService:
    """Service zum Abrufen und Entschlüsseln von Firebase Remote Config."""
    
    REMOTE_CONFIG_URL = "https://firebaseremoteconfig.googleapis.com/v1/projects/{project_id}/namespaces/firebase:fetch"
    ANDROID_PACKAGE = "com.EuropaParkMackKG.EPGuide"
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self._cached_credentials: Optional[dict] = None
    
    async def fetch_remote_config(self) -> dict:
        """
        Ruft die Firebase Remote Config ab und entschlüsselt alle Einträge.
        
        Returns:
            Dictionary mit den entschlüsselten Remote Config Einträgen
        """
        url = self.REMOTE_CONFIG_URL.format(project_id=self.settings.fb_project_id)
        fid = generate_firebase_id()
        
        payload = {
            "appInstanceId": fid,
            "appId": self.settings.fb_app_id,
            "packageName": self.ANDROID_PACKAGE,
            "languageCode": "en_GB",
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.settings.fb_api_key,
        }
        
        logger.info("Rufe Firebase Remote Config ab...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if "entries" not in data:
                logger.warning("Remote Config enthält keine 'entries'")
                return {}
            
            decrypted_entries = {}
            for key, value in data["entries"].items():
                try:
                    decrypted_entries[key] = decrypt_blowfish(
                        value,
                        self.settings.enc_key,
                        self.settings.enc_iv
                    )
                except Exception as e:
                    logger.warning(f"Konnte Eintrag '{key}' nicht entschlüsseln: {e}")
                    decrypted_entries[key] = value
            
            logger.info(f"Remote Config erfolgreich abgerufen. {len(decrypted_entries)} Einträge.")
            return decrypted_entries
    
    async def get_decrypted_credentials(self, force_refresh: bool = False) -> dict:
        """
        Ruft die entschlüsselten API Credentials ab.
        
        Args:
            force_refresh: Wenn True, wird der Cache ignoriert
        
        Returns:
            Dictionary mit 'username' (client_id) und 'password' (client_secret)
        """
        if self._cached_credentials and not force_refresh:
            return self._cached_credentials
        
        entries = await self.fetch_remote_config()
        
        username = entries.get(self.settings.user_key)
        password = entries.get(self.settings.pass_key)
        
        if not username or not password:
            logger.warning("Remote Config Credentials nicht gefunden. Verwende Fallback aus .env")
            self._cached_credentials = {
                "username": self.settings.api_username,
                "password": self.settings.api_password
            }
            return self._cached_credentials
        
        logger.info("Credentials aus Remote Config erfolgreich geladen.")
        self._cached_credentials = {
            "username": username,
            "password": password
        }
        return self._cached_credentials


_firebase_config_service: Optional[FirebaseConfigService] = None


def get_firebase_config_service() -> FirebaseConfigService:
    """Gibt die globale FirebaseConfigService-Instanz zurück."""
    global _firebase_config_service
    if _firebase_config_service is None:
        _firebase_config_service = FirebaseConfigService()
    return _firebase_config_service
