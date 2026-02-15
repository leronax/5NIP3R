import asyncio
import random
from datetime import datetime
from stem import Signal
from stem.control import Controller
import aiohttp
from aiohttp_socks import ProxyConnector

class IPKeyRotator:
    """Ротация IP (через Tor) и API ключей"""
    
    def __init__(self, api_keys: list, tor_password: str = None):
        self.api_keys = api_keys
        self.tor_password = tor_password
        self.current_key_index = 0
        self.last_ip_rotation = datetime.now()
        self.last_key_rotation = datetime.now()
        self.ip_rotation_interval = 120  # секунд (2 минуты) - меняем IP
        self.key_rotation_interval = 7200  # секунд (2 часа) - меняем ключ
        
    async def rotate_ip(self):
        """Принудительно меняет IP через Tor"""
        try:
            # Подключаемся к ControlPort Tor
            with Controller.from_port(port=9051) as controller:
                if self.tor_password:
                    controller.authenticate(password=self.tor_password)
                controller.signal(Signal.NEWNYM)  # Новая цепь = новый IP
                self.last_ip_rotation = datetime.now()
                print(f"🔄 IP ротация в {datetime.now().strftime('%H:%M:%S')}")
                return True
        except Exception as e:
            print(f"❌ Ошибка ротации IP: {e}")
            return False
    
    def rotate_key(self):
        """Переключает на следующий API ключ"""
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        self.last_key_rotation = datetime.now()
        print(f"🔑 Смена API ключа на #{self.current_key_index + 1}")
        return self.get_current_key()
    
    def get_current_key(self):
        """Возвращает текущий API ключ"""
        return self.api_keys[self.current_key_index]
    
    def need_ip_rotation(self):
        """Проверяет, пора ли менять IP"""
        elapsed = (datetime.now() - self.last_ip_rotation).total_seconds()
        return elapsed >= self.ip_rotation_interval
    
    def need_key_rotation(self):
        """Проверяет, пора ли менять ключ"""
        elapsed = (datetime.now() - self.last_key_rotation).total_seconds()
        return elapsed >= self.key_rotation_interval
    
    async def get_tor_session(self):
        """Создает aiohttp сессию через Tor прокси"""
        connector = ProxyConnector.from_url('socks5://127.0.0.1:9050')
        return aiohttp.ClientSession(connector=connector)