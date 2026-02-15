import json
import os
from typing import List, Dict, Optional
import config

class AccountManager:
    """Загружает аккаунты из accounts.txt и .maFile"""
    
    def __init__(self):
        self.accounts_file = config.ACCOUNTS_FILE
        self.mafiles_dir = os.path.join(os.getcwd(), 'login', 'mafiles')
        self.accounts: List[Dict] = []
        self.current_index = 0
        
    def load_accounts(self) -> List[Dict]:
        """Загружает все аккаунты с shared_secret"""
        # Получаем все shared_secret из .maFile
        secrets = {}
        if os.path.exists(self.mafiles_dir):
            for filename in os.listdir(self.mafiles_dir):
                if filename.endswith('.maFile'):
                    try:
                        with open(os.path.join(self.mafiles_dir, filename), 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if 'account_name' in data and 'shared_secret' in data:
                                secrets[data['account_name']] = data['shared_secret']
                    except:
                        pass
        
        # Загружаем аккаунты из accounts.txt
        accounts = []
        if os.path.exists(self.accounts_file):
            with open(self.accounts_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if ':' in line:
                        login, password = line.split(':', 1)
                        shared_secret = secrets.get(login, '')
                        accounts.append({
                            'login': login,
                            'password': password,
                            'shared_secret': shared_secret
                        })
        
        self.accounts = accounts
        return accounts
    
    def get_next_account(self) -> Optional[Dict]:
        """Возвращает следующий аккаунт для использования"""
        if not self.accounts:
            self.load_accounts()
        
        if not self.accounts:
            return None
        
        account = self.accounts[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.accounts)
        return account