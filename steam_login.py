import aiohttp
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import hmac
import base64
import struct
from hashlib import sha1
import requests

PROFILES_URL = 'https://steamcommunity.com/profiles/'

def generate_2fa_code(shared_secret: str) -> str:
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

async def get_cookies(username: str, password: str, shared_secret: str):
    """Получает cookies через Selenium (headless) с автоматическим драйвером"""
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    
    # Добавляем аргументы для обхода обнаружения автоматизации
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # User-Agent как у реального браузера
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    driver = None
    try:
        # Автоматически скачиваем и устанавливаем подходящий ChromeDriver
        print(f"🔄 Запускаем Chrome для {username}...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # Устанавливаем таймаут загрузки страницы
        driver.set_page_load_timeout(30)
        
        # Переходим на страницу логина
        print("   Переход на страницу логина...")
        driver.get('https://steamcommunity.com/login/home/')
        
        # Ждем загрузки страницы
        wait = WebDriverWait(driver, 20)
        
        # Ждем появления полей ввода
        print("   Ждем поля ввода...")
        login_fields = wait.until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, '_2GBWeup5cttgbTw8FM3tfx'))
        )
        
        # Вводим логин и пароль
        print("   Вводим логин и пароль...")
        login_fields[0].send_keys(username)
        login_fields[1].send_keys(password)
        
        # Нажимаем кнопку входа
        print("   Нажимаем кнопку входа...")
        login_button = wait.until(EC.element_to_be_clickable((
            By.XPATH, '//*[@id="responsive_page_template_content"]/div[1]/div[1]/div/div/div/div[2]/div/form/div[4]/button'
        )))
        login_button.click()
        
        # Ждем появления кнопки Steam Guard
        print("   Ждем запрос 2FA...")
        guard_button = wait.until(EC.element_to_be_clickable((
            By.XPATH, '//*[@id="responsive_page_template_content"]/div[1]/div[1]/div/div/div/div[2]/div/div[3]/div/div'
        )))
        guard_button.click()
        
        # Генерируем и вводим 2FA код
        print("   Генерируем 2FA код...")
        code = generate_2fa_code(shared_secret)
        print(f"   Сгенерированный код: {code}")
        
        # Ждем поле для ввода кода
        code_input = wait.until(EC.presence_of_element_located((
            By.XPATH, '/html/body/div[1]/div[7]/div[4]/div[1]/div[1]/div/div/div/div[2]/form/div/div[2]/div[1]/div/input[1]'
        )))
        code_input.send_keys(code)
        # После code_input.send_keys(code) добавь:
        code_input.send_keys(u'\ue007')  # Enter
        print("   Enter нажат")
        
        
        # Ждем обработки кода
        print("   Отправляем 2FA код...")
        time.sleep(3)
        
        # Получаем SteamID из текущего URL
        current_url = driver.current_url
        if 'profiles' in current_url:
            steamid = current_url.split('/')[-1][:-5]
        else:
            # Если не получилось, пробуем другой способ
            steamid = username
            
        # Переходим в редактирование профиля для получения кук
        print(f"   Переходим в профиль {steamid}...")
        driver.get(f'https://steamcommunity.com/profiles/{steamid}/edit/info')
        time.sleep(2)
        
        # Собираем cookies
        cookies = {}
        for cookie in driver.get_cookies():
            if cookie['name'] in ['sessionid', 'steamLoginSecure']:
                cookies[cookie['name']] = cookie['value']
                print(f"   Получена кука: {cookie['name']}")
        
        # Добавляем steamid
        cookies['steamid'] = steamid
        
        print(f"✅ Успешно получены куки для {username}")
        return cookies
        
    except Exception as e:
        print(f"❌ Ошибка Selenium для {username}: {str(e)}")
        # Сохраняем скриншот для отладки
        if driver:
            try:
                screenshot_path = f"error_{username}_{int(time.time())}.png"
                driver.save_screenshot(screenshot_path)
                print(f"   Скриншот ошибки сохранен: {screenshot_path}")
            except:
                pass
        return None
        
    finally:
        if driver:
            driver.quit()
            print("   Браузер закрыт")

async def claim_vanity_url(cookies: dict, vanity: str) -> bool:
    """Занимает свободный Steam ID"""
    if not cookies or 'sessionid' not in cookies or 'steamLoginSecure' not in cookies:
        print("❌ Нет валидных кук для занятия")
        return False
    
    session = None
    try:
        session = aiohttp.ClientSession()
        
        # Добавляем куки в сессию
        session.cookie_jar.update_cookies({
            'sessionid': cookies['sessionid'],
            'steamLoginSecure': cookies['steamLoginSecure']
        })
        
        # Добавляем заголовки как у реального браузера
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://steamcommunity.com',
            'Referer': f'https://steamcommunity.com/profiles/{cookies["steamid"]}/edit/info',
        })
        
        form_data = aiohttp.FormData()
        form_data.add_field('sessionID', cookies['sessionid'])
        form_data.add_field('type', 'profileSave')
        form_data.add_field('customURL', vanity)
        form_data.add_field('json', '1')
        
        print(f"   Отправляем запрос на занятие {vanity}...")
        
        async with session.post(
            f'{PROFILES_URL}{cookies["steamid"]}/edit/',
            data=form_data
        ) as resp:
            text = await resp.text()
            
            if 'Your Profile Name must be between 2 and 32 characters in length' in text:
                print(f"✅ ID {vanity} успешно занят!")
                return True
            elif 'RL specified is already in use' in text:
                print(f"❌ ID {vanity} уже занят кем-то другим")
                return False
            elif 'Invalid sessionID' in text or 'sessionid' in text.lower():
                print(f"⚠️ Сессия истекла, нужно обновить куки")
                return False
            else:
                print(f"⚠️ Неизвестный ответ: {text[:200]}")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка при занятии {vanity}: {e}")
        return False
    finally:
        if session:
            await session.close()