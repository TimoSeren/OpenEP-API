"""
Token Storage Service.
Persistiert OAuth2 Tokens in der Datenbank.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select

from database import TokenModel, get_session

logger = logging.getLogger(__name__)

TOKEN_KEY = "europapark_oauth"


class TokenData:
    """Repräsentiert Token-Daten."""
    
    def __init__(
        self,
        access_token: str,
        token_type: str,
        expires_at: datetime,
        created_at: Optional[datetime] = None
    ):
        self.access_token = access_token
        self.token_type = token_type
        self.expires_at = expires_at
        self.created_at = created_at or datetime.now()
    
    def is_expired(self, buffer_seconds: int = 300) -> bool:
        """Prüft ob der Token abgelaufen ist."""
        expiry_with_buffer = self.expires_at - timedelta(seconds=buffer_seconds)
        return datetime.now() >= expiry_with_buffer


class TokenStorage:
    """Verwaltet die Persistierung von OAuth2 Tokens."""
    
    def __init__(self, key: str = TOKEN_KEY):
        self.key = key
    
    async def save(self, token_data: TokenData) -> None:
        async with get_session() as session:
            result = await session.execute(
                select(TokenModel).where(TokenModel.key == self.key)
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                existing.access_token = token_data.access_token
                existing.token_type = token_data.token_type
                existing.expires_at = token_data.expires_at
            else:
                new_token = TokenModel(
                    key=self.key,
                    access_token=token_data.access_token,
                    token_type=token_data.token_type,
                    expires_at=token_data.expires_at,
                    created_at=token_data.created_at
                )
                session.add(new_token)
            
            await session.commit()
            logger.info(f"Token gespeichert. Gültig bis: {token_data.expires_at}")
    
    async def load(self) -> Optional[TokenData]:
        async with get_session() as session:
            result = await session.execute(
                select(TokenModel).where(TokenModel.key == self.key)
            )
            token = result.scalar_one_or_none()
            
            if not token:
                return None
            
            return TokenData(
                access_token=token.access_token,
                token_type=token.token_type,
                expires_at=token.expires_at,
                created_at=token.created_at
            )


_token_storage: Optional[TokenStorage] = None


def get_token_storage() -> TokenStorage:
    global _token_storage
    if _token_storage is None:
        _token_storage = TokenStorage()
    return _token_storage
