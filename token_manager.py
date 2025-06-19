import aiohttp
import asyncio
from datetime import datetime, timedelta

class TokenManager:
    """Manages authentication tokens for the TeamDynamix API."""
    
    def __init__(self, username: str, password: str):
        """
        Initialize the TokenManager with credentials and authentication URL.
        
        Args:
            username (str): API username.
            password (str): API password.
        """
        self.username = username
        self.password = password
        self.auth_url = "https://servicecenter.midlandhealth.org/TDWebApi/api/auth"
        self.access_token = None
        self.expires_at = None
        self.payload = {"UserName": self.username, "Password": self.password}

    async def authenticate(self) -> None:
        """Authenticates with the TeamDynamix API and updates token information."""
        async with aiohttp.ClientSession() as session:
            async with session.post(self.auth_url, json=self.payload) as response:
                response.raise_for_status()
                self.access_token = await response.text()
                self.expires_at = datetime.now() + timedelta(hours=24)

    async def refresh_token(self) -> None:
        """Refreshes the access token."""
        await self.authenticate()

    async def get_access_token(self) -> str:
        """
        Returns the current access token, refreshing if necessary.
        
        Returns:
            str: Valid access token.
        """
        if not self.access_token or self.expires_at < datetime.now():
            await self.refresh_token()
        
        return str(self.access_token)