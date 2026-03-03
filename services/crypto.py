"""
Kryptographie-Service für Blowfish-Entschlüsselung.
Entschlüsselt die Firebase Remote Config Credentials.
"""

import base64
import logging

from Crypto.Cipher import Blowfish

logger = logging.getLogger(__name__)


def decrypt_blowfish(encrypted_base64: str, key: str, iv: str) -> str:
    """
    Entschlüsselt einen Base64-kodierten Blowfish-CBC verschlüsselten String.
    
    Args:
        encrypted_base64: Base64-kodierter verschlüsselter Text
        key: Blowfish-Schlüssel (muss 4-56 Bytes sein)
        iv: Initialisierungsvektor (muss 8 Bytes sein)
    
    Returns:
        Entschlüsselter Text als String
    
    Raises:
        ValueError: Bei ungültigen Eingaben oder Entschlüsselungsfehlern
    """
    try:
        encrypted = base64.b64decode(encrypted_base64)
        
        cipher = Blowfish.new(
            key.encode('utf-8'),
            Blowfish.MODE_CBC,
            iv.encode('utf-8')
        )
        
        decrypted = cipher.decrypt(encrypted)
        
        # PKCS7 Padding entfernen
        padding_length = decrypted[-1]
        if padding_length > 0 and padding_length <= 8:
            decrypted = decrypted[:-padding_length]
        
        return decrypted.decode('utf-8')
        
    except Exception as e:
        logger.error(f"Blowfish Entschlüsselung fehlgeschlagen: {e}")
        raise ValueError(f"Entschlüsselung fehlgeschlagen: {e}")
