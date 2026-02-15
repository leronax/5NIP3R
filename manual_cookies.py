import json
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

async def get_cookies_manual():
    print("🔄 Открываю Chrome для ручного логина...")
    options = Options()
    # Не используем headless, чтобы видеть браузер
    
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get('https://steamcommunity.com/login/home/')
        
        print("⚠️ Войди в аккаунт вручную в течение 60 секунд...")
        print("✅ После успешного входа нажми Enter здесь")
        input("Нажми Enter после того, как залогинишься...")
        
        # Получаем куки
        cookies = {}
        for cookie in driver.get_cookies():
            if cookie['name'] in ['sessionid', 'steamLoginSecure']:
                cookies[cookie['name']] = cookie['value']
        
        # Получаем steamid из URL
        current_url = driver.current_url
        if 'profiles' in current_url:
            steamid = current_url.split('/')[-1].split('?')[0]
            if steamid and steamid.isdigit():
                cookies['steamid'] = steamid
        
        # Сохраняем в файл
        with open('cookies.json', 'w') as f:
            json.dump(cookies, f, indent=2)
        
        print(f"✅ Куки сохранены: {cookies}")
        return cookies
        
    finally:
        driver.quit()

if __name__ == "__main__":
    asyncio.run(get_cookies_manual())