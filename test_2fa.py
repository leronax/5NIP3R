import hmac
import base64
import struct
import time
from hashlib import sha1
import requests

def generate_2fa_code(shared_secret):
    """Генерирует код Steam Guard"""
    symbols = '23456789BCDFGHJKMNPQRTVWXY'
    
    def get_time_offset():
        try:
            resp = requests.post('https://api.steampowered.com/ITwoFactorService/QueryTime/v0001', timeout=10)
            return int(resp.json()['response']['server_time']) - time.time()
        except:
            return 0
    
    timestamp = int(time.time() + get_time_offset())
    hmac_bytes = hmac.new(
        base64.b64decode(shared_secret),
        struct.pack('>Q', timestamp // 30),
        sha1
    ).digest()
    
    start = hmac_bytes[19] & 0xF
    code_int = struct.unpack('>I', hmac_bytes[start:start+4])[0] & 0x7FFFFFFF
    
    code = ''
    for _ in range(5):
        code += symbols[code_int % len(symbols)]
        code_int //= len(symbols)
    
    return code

# Твой исправленный shared_secret
shared_secret = "tkgMOne1BUZXF/YQmNmbU06AfnA="

code = generate_2fa_code(shared_secret)
print(f"✅ Сгенерированный код: {code}")