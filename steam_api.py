import aiohttp
import asyncio
from typing import Union, Optional
from rotator import IPKeyRotator

class SteamVanityChecker:
    """Проверка Steam ID с ротацией IP и ключей"""
    
    def __init__(self, rotator: IPKeyRotator):
        self.rotator = rotator
        self.base_url = "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/"
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        # Создаем сессию через Tor
        self._session = await self.rotator.get_tor_session()
        return self

    async def __aexit__(self, *args):
        if self._session:
            await self._session.close()

    async def check(self, vanity: str) -> Union[bool, int, str]:
        """Проверяет ID с автоматической ротацией IP/ключа"""
        
        # Проверяем, не пора ли сменить IP
        if self.rotator.need_ip_rotation():
            await self.rotator.rotate_ip()
            # После смены IP обновляем сессию
            if self._session:
                await self._session.close()
            self._session = await self.rotator.get_tor_session()
        
        # Проверяем, не пора ли сменить ключ
        if self.rotator.need_key_rotation():
            self.rotator.rotate_key()
        
        # Берем текущий ключ
        current_key = self.rotator.get_current_key()
        
        params = {
            'key': current_key,
            'vanityurl': vanity.strip().lower(),
            'url_type': 1
        }

        try:
            async with self._session.get(self.base_url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    response = data.get('response', {})
                    
                    if response.get('success') == 42:
                        return True
                    if response.get('steamid'):
                        return False
                    return f"Unknown: {data}"
                
                elif resp.status == 429:
                    # При 429 сразу меняем IP и ключ
                    print("⚠️ 429 - срочная ротация!")
                    await self.rotator.rotate_ip()
                    self.rotator.rotate_key()
                    return 429
                elif resp.status == 403:
                    # При 403 меняем ключ
                    self.rotator.rotate_key()
                    return 403
                else:
                    return resp.status
                    
        except Exception as e:
            return f"Error: {e}"