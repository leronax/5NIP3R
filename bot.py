import asyncio
import os
import random
import json
from datetime import datetime, timedelta
from aiogram import Bot

import config
from steam_api import SteamVanityChecker
from steam_login import claim_vanity_url
from account_manager import AccountManager

class HumanSteamChecker:
    """Чекер с человеческим поведением и поддержкой нескольких кук"""
    
    def __init__(self):
        self.bot = Bot(token=config.YOUR_BOT_TOKEN)
        self.account_manager = AccountManager()
        self.checked_count = 0
        self.found_count = 0
        self.session_found = 0
        self.total_checked = 0  # Общее количество проверенных за все время
        
        # Файлы
        self.progress_file = "checker_progress.json"
        self.cookies_dir = "cookies"
        self.cookies_list = []
        self.current_cookie_index = 0
        
        # Загружаем списки
        self.words = []
        self.banned = []
        self.load_lists()
        
        # Загружаем прогресс
        self.load_progress()
        
        # Загружаем все куки из папки
        self.load_all_cookies()
        
        # Создаем папку для логов
        self.log_dir = os.path.join(os.getcwd(), 'logs', datetime.now().strftime("%Y_%m_%d"))
        os.makedirs(self.log_dir, exist_ok=True)
    
    def load_lists(self):
        """Загружает списки слов и бана"""
        self.words = config.load_words()
        self.banned = config.load_banned()
        
        # Удаляем уже проверенные/забаненные
        original_count = len(self.words)
        self.words = [w for w in self.words if w not in self.banned]
        skipped = original_count - len(self.words)
        
        print(f"\n{'='*60}")
        print("🤖 STEAM ID ЧЕКЕР С TOR И 4 КЛЮЧАМИ")
        print(f"{'='*60}")
        print(f"📋 ID для проверки: {len(self.words)}")
        print(f"⛔ В бане: {skipped}")
        print(f"🎯 Прогресс: {self.checked_count}")
        print(f"🔑 Ключей: {len(config.STEAM_API_KEYS)}")
        print(f"👤 Наборов кук: {len(self.cookies_list)}")
        print(f"🔄 IP ротация: каждые 2 минуты")
        print(f"🔄 Ключи: каждые 2 часа")
        print(f"{'='*60}\n")
    
    def load_progress(self):
        """Загружает прогресс проверки"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.checked_count = data.get('checked', 0)
                    self.total_checked = data.get('total_checked', 0)
                    print(f"🔄 Загружен прогресс: проверено {self.checked_count} ID в текущем цикле, всего {self.total_checked}")
            except:
                pass
    
    def save_progress(self):
        """Сохраняет прогресс проверки"""
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'checked': self.checked_count,
                    'total_checked': self.total_checked
                }, f, indent=2)
        except:
            pass
    
    def reset_progress(self):
        """Сбрасывает прогресс проверки"""
        self.checked_count = 0
        self.total_checked = 0
        if os.path.exists(self.progress_file):
            try:
                os.remove(self.progress_file)
                print("🔄 Прогресс сброшен")
            except:
                pass
    
    def load_all_cookies(self):
        """Загружает все куки из папки cookies/"""
        self.cookies_list = []
        
        if not os.path.exists(self.cookies_dir):
            os.makedirs(self.cookies_dir)
            print(f"📁 Создана папка {self.cookies_dir}")
            print("   Положи туда JSON-файлы с куками для разных аккаунтов")
            print("   Формат файла: { 'sessionid': '...', 'steamLoginSecure': '...', 'steamid': '...' }")
            return False
        
        for filename in os.listdir(self.cookies_dir):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(self.cookies_dir, filename), 'r', encoding='utf-8') as f:
                        cookies = json.load(f)
                        if 'sessionid' in cookies and 'steamLoginSecure' in cookies:
                            # Добавляем имя файла для идентификации
                            cookies['filename'] = filename
                            self.cookies_list.append(cookies)
                            print(f"✅ Загружены куки: {filename}")
                        else:
                            print(f"⚠️ В файле {filename} нет нужных полей (sessionid, steamLoginSecure)")
                except Exception as e:
                    print(f"❌ Ошибка загрузки {filename}: {e}")
        
        self.current_cookie_index = 0
        print(f"📊 Всего загружено наборов кук: {len(self.cookies_list)}")
        return len(self.cookies_list) > 0
    
    def get_next_cookie(self):
        """Возвращает следующий набор кук по кругу"""
        if not self.cookies_list:
            return None
        cookies = self.cookies_list[self.current_cookie_index]
        self.current_cookie_index = (self.current_cookie_index + 1) % len(self.cookies_list)
        return cookies
    
    def human_delay(self):
        """Генерирует человеческую задержку"""
        delay = random.uniform(1.2, 2.8)
        
        if random.random() < 0.15:
            extra = random.uniform(5, 15)
            delay += extra
            print(f"  ☕ Пауза: {extra:.1f} сек (кофе-брейк)")
        
        if random.random() < 0.05:
            extra = random.uniform(30, 90)
            delay += extra
            print(f"  📱 Пауза: {extra:.1f} сек (отвлекся на телефон)")
        
        return delay
    
    async def send_start_notification(self):
        """Отправляет уведомление о запуске"""
        try:
            await self.bot.send_message(
                chat_id=config.YOUR_CHAT_ID,
                text=f'🚀 <b>Бот запущен</b>\n'
                     f'🕐 {datetime.now().strftime("%H:%M:%S")}\n'
                     f'📊 Осталось ID: {len(self.words)}\n'
                     f'📈 Прогресс: {self.checked_count}/{self.checked_count + len(self.words)}\n'
                     f'👤 Аккаунтов для занятия: {len(self.cookies_list)}\n'
                     f'🔄 IP ротация: 2 мин\n'
                     f'🔑 Ключей: {len(config.STEAM_API_KEYS)}',
                parse_mode='HTML'
            )
            print("✅ Уведомление о запуске отправлено в Telegram")
        except Exception as e:
            print(f"❌ Ошибка отправки уведомления: {e}")
    
    async def send_stop_notification(self):
        """Отправляет уведомление об остановке"""
        try:
            await self.bot.send_message(
                chat_id=config.YOUR_CHAT_ID,
                text=f'🛑 <b>Бот остановлен</b>\n'
                     f'✅ Найдено за сессию: {self.session_found}\n'
                     f'🎯 Всего найдено: {self.found_count}\n'
                     f'📊 Проверено всего: {self.total_checked}',
                parse_mode='HTML'
            )
            print("✅ Уведомление об остановке отправлено")
        except:
            pass
    
    async def send_restart_notification(self):
        """Отправляет уведомление о перезапуске цикла"""
        try:
            await self.bot.send_message(
                chat_id=config.YOUR_CHAT_ID,
                text=f'🔄 <b>Начинаем новый цикл проверки</b>\n'
                     f'📊 ID для проверки: {len(self.words)}\n'
                     f'🎯 Всего найдено: {self.found_count}\n'
                     f'📊 Всего проверено: {self.total_checked}\n'
                     f'👤 Аккаунтов: {len(self.cookies_list)}',
                parse_mode='HTML'
            )
        except:
            pass
    
    async def log_free_id(self, vanity: str, cookie_file: str):
        """Логирует найденный ID и отправляет в Telegram"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Сохраняем в файл
        try:
            with open(os.path.join(self.log_dir, 'free_ids.txt'), 'a', encoding='utf-8') as f:
                f.write(f"{timestamp} | {vanity} | {cookie_file}\n")
        except:
            pass
        
        config.save_banned(vanity)
        
        # Отправляем в Telegram
        try:
            await self.bot.send_message(
                chat_id=config.YOUR_CHAT_ID,
                text=f'✅ <b>Найден свободный ID!</b>\n'
                     f'🔗 <a href="https://steamcommunity.com/id/{vanity}">{vanity}</a>\n'
                     f'📁 Куки: {cookie_file}',
                parse_mode='HTML'
            )
            print(f"  📨 Уведомление отправлено в Telegram")
        except:
            pass
    
    async def run(self):
        """Основной цикл работы бота"""
        
        # Отправляем уведомление о запуске
        await self.send_start_notification()
        
        # Проверяем наличие кук
        if not self.cookies_list:
            print("⚠️ Нет загруженных кук! ID не будут заниматься.")
            print("📁 Положи JSON-файлы с куками в папку 'cookies/'")
        
        # Запоминаем время старта
        start_time = datetime.now()
        print(f"🕐 Старт: {start_time.strftime('%H:%M:%S')}")
        print(f"💡 Бот работает. Нажми Ctrl+C для остановки")
        print("-"*60)
        
        self.session_found = 0
        cycle_number = 1
        
        while True:
            print(f"\n{'='*60}")
            print(f"🔄 ЦИКЛ ПРОВЕРКИ #{cycle_number}")
            print(f"{'='*60}\n")
            
            # Создаем чекер с ротатором из config
            from rotator import IPKeyRotator
            rotator = IPKeyRotator(config.STEAM_API_KEYS, tor_password="mypassword")
            checker = SteamVanityChecker(rotator)
            await checker.__aenter__()
            
            try:
                # Начинаем с того места, где остановились
                start_index = self.checked_count
                for i, vanity in enumerate(self.words[start_index:], start_index + 1):
                    self.checked_count += 1
                    self.total_checked += 1
                    
                    if vanity in self.banned:
                        continue
                    
                    # Показываем какой ключ используется
                    print(f"🔍 [{self.total_checked}] {vanity} [ключ {rotator.current_key_index+1}]", end='', flush=True)
                    result = await checker.check(vanity)
                    
                    if result is True:
                        print(f" ✅ СВОБОДЕН!")
                        
                        # Пробуем занять ID всеми доступными куками по очереди
                        if self.cookies_list:
                            occupied = False
                            for idx, cookies in enumerate(self.cookies_list):
                                cookie_file = cookies.get('filename', f'cookie_{idx}.json')
                                print(f"   🔄 Пробую аккаунт {idx+1}/{len(self.cookies_list)}: {cookie_file}")
                                
                                success = await claim_vanity_url(cookies, vanity)
                                if success:
                                    print(f"   ✅ ID занят аккаунтом {cookie_file}!")
                                    await self.log_free_id(vanity, cookie_file)
                                    self.found_count += 1
                                    self.session_found += 1
                                    occupied = True
                                    break
                                else:
                                    print(f"   ❌ Аккаунт {cookie_file} не смог занять ID")
                            
                            if not occupied:
                                print(f"   ⚠️ Ни один аккаунт не смог занять {vanity}")
                        else:
                            print(f"  ⚠️ Нет кук для занятия ID")
                    
                    elif result is False:
                        print(f" ❌ Занят")
                        
                    elif result == 429:
                        print(f" ⚠️ 429 Too Many Requests")
                        print(f"\n⚠️ Лимит API! Пауза 5 минут...")
                        await asyncio.sleep(300)
                    
                    elif result == 403:
                        print(f" 🔐 403 Forbidden")
                        print(f"\n❌ Ошибка API ключа!")
                        break
                        
                    else:
                        print(f" ❓ {result}")
                    
                    # Человеческая задержка
                    delay = self.human_delay()
                    await asyncio.sleep(delay)
                    
                    # Сохраняем прогресс каждые 10 запросов
                    if i % 10 == 0:
                        self.save_progress()
                        elapsed = datetime.now() - start_time
                        elapsed_hours = elapsed.total_seconds() / 3600
                        print(f"\n📊 Прогресс: {elapsed_hours:.1f} ч, найдено за сессию: {self.session_found}, всего: {self.found_count}\n")
                
                # Если дошли сюда, значит список закончился
                print(f"\n{'='*60}")
                print(f"✅ ЦИКЛ #{cycle_number} ЗАВЕРШЕН")
                print(f"📊 Проверено в этом цикле: {self.checked_count} ID")
                print(f"🎯 Всего найдено: {self.found_count}")
                print(f"📊 Всего проверено за все время: {self.total_checked}")
                print(f"{'='*60}\n")
                
                # Обновляем списки для следующего цикла
                print("🔄 Подготовка к новому циклу проверки...")
                
                # Загружаем свежие списки
                self.words = config.load_words()
                self.banned = config.load_banned()
                
                # Удаляем уже проверенные/забаненные
                original_count = len(self.words)
                self.words = [w for w in self.words if w not in self.banned]
                skipped = original_count - len(self.words)
                
                # Сбрасываем счетчик проверенных для нового цикла
                self.checked_count = 0
                
                # Перезагружаем куки (на случай если добавили новые)
                self.load_all_cookies()
                
                # Увеличиваем номер цикла
                cycle_number += 1
                
                # Отправляем уведомление о новом цикле
                await self.send_restart_notification()
                
                print(f"\n📊 Новый цикл: {len(self.words)} ID для проверки (пропущено {skipped} в бане)")
                print(f"⏳ Пауза 10 секунд перед началом нового цикла...")
                await asyncio.sleep(10)
                
            finally:
                await checker.__aexit__(None, None, None)
            
            # Если пользователь нажал Ctrl+C, выходим
            # Иначе продолжаем цикл
    
    async def stop(self):
        """Останавливает бота"""
        await self.send_stop_notification()
        await self.bot.session.close()

async def main():
    """Точка входа"""
    checker = None
    try:
        # Проверяем аргументы командной строки для сброса
        import sys
        if len(sys.argv) > 1 and sys.argv[1] == '--reset':
            checker = HumanSteamChecker()
            checker.reset_progress()
            print("🔄 Прогресс сброшен, начинаем с начала")
            return
        
        checker = HumanSteamChecker()
        await checker.run()
        
    except KeyboardInterrupt:
        print("\n\n👋 Бот остановлен вручную.")
        if checker:
            await checker.stop()
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if checker and hasattr(checker, 'bot'):
            await checker.bot.session.close()
        print("💾 Прогресс сохранен.")

if __name__ == "__main__":
    asyncio.run(main())