import json
import pickle
import requests
import configparser
from pathlib import Path
from bs4 import BeautifulSoup
from tools.config import Config
from typing import NoReturn, Union
from datetime import datetime, timedelta
from tools.exceptions import LoginError, IPBanned


class AtilimAuth:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config_file = Config.get_auth_data_filepath()
        self.session_file = Config.get_session_filepath()
        self.cookie_file = Config.get_cookie_filepath()
        self.user_agent = Config.user_agent

        if self.config_file.exists():
            self.config.read(self.config_file)
            self.username = self.config['auth']['username']
            self.password = self.config['auth']['password']
        else:
            self.username, self.password = self.create_config_file()

    def create_config_file(self):
        username: str = str(input('Enter your Atilim University username: '))
        password: str = str(input('Enter your Atilim University password: '))
        with open(self.config_file, 'w') as configfile:
            self.config['auth'] = {'username': username, 'password': password}
            self.config.write(configfile)
        return username, password

    def get_session(self):
        with requests.Session() as session:
            session.headers.update({
                'Connection': 'keep-alive',
                'Referer': Config.kiyos_url,
                'User-Agent': self.user_agent
            })
            payload = {'loginName': self.username, 'passwd': self.password}
            post = session.post(Config.kiyos_login_url, json=payload)

            if post.status_code == 504:
                raise IPBanned('Your IP Address is Banned')
            if json.loads(post.content)['success'] is False:
                self.config_file.unlink()
                raise LoginError('Invalid username or password')
            else:
                session.get(Config.kiyos_auth_token_url)
                with self.session_file.open('wb') as s:
                    pickle.dump(session, s, protocol=pickle.HIGHEST_PROTOCOL)
                    self.save_cookies(session, Config.kiyos_cookie_key, 'kiyos')
                    print(f'Session Stored - {self.username} Logged Into System')
            return session

    def save_cookies(self, session, key: Union[str, list], category: str) -> NoReturn:
        if isinstance(key, str):
            key = [key]

        if self.cookie_file.exists():
            with self.cookie_file.open('r+') as cookie_file:
                try:
                    cookies = json.load(cookie_file)
                except json.JSONDecodeError:
                    cookies = {}

                if 'kiyos' not in cookies:
                    cookies['kiyos'] = {}

                if category not in cookies:
                    cookies[category] = {}

                for k in key:
                    if k in session.cookies.get_dict():
                        cookies[category][k] = session.cookies.get_dict().get(k)

                cookie_file.seek(0)
                json.dump(cookies, cookie_file, indent=4)
                cookie_file.truncate()
        else:
            with self.cookie_file.open('w') as cookie_file:
                cookies = {
                    'kiyos': {}
                }

                cookies[category] = {k: session.cookies.get_dict().get(k) for k in key if
                                     k in session.cookies.get_dict()}
                json.dump(cookies, cookie_file, indent=4)

    @staticmethod
    def expire_file(file_location: Path) -> bool:
        if file_location.exists():
            m_time = file_location.stat().st_mtime
            mtime = datetime.fromtimestamp(m_time)
            now = datetime.now()
            elapsed = now - mtime
            if elapsed > timedelta(minutes=20):
                with file_location.open('w') as file:
                    file.truncate(0)
                file_location.unlink(missing_ok=True)
                return True
            return False
        return True

    def load_cookies(self, session, key: Union[str, list], category: str) -> bool:
        if not isinstance(session, requests.Session):
            raise TypeError('Provided session is not a requests.Session instance.')

        is_cookie_expire = AtilimAuth.expire_file(Config.get_cookie_filepath())
        if not is_cookie_expire:
            if isinstance(key, str):
                key = [key]

            if self.cookie_file.exists():
                with self.cookie_file.open('r') as cookie_file:
                    cookies = json.load(cookie_file)

                    if category in cookies:
                        category_cookies = cookies[category]
                        all_cookie_exists = set(key).issubset(category_cookies.keys())
                        if all_cookie_exists:
                            filtered_cookies = {k: v for k, v in category_cookies.items() if k in key}
                            for k, v in filtered_cookies.items():
                                if k not in session.cookies or session.cookies[k] != v:
                                    # print(f'Kiyos::Loaded cookie: {k}={v}')
                                    session.cookies.set(k, v)
                            return True
            return False
        return False

    def login(self) -> requests.Session:
        is_session_expire = AtilimAuth.expire_file(self.session_file)
        if is_session_expire:
            return self.get_session()
        else:
            with requests.Session() as session:
                with self.session_file.open("rb") as s:
                    saved_session = pickle.load(s)
                    session.cookies.update(saved_session.cookies)
                    print(f'Stored Session Used - No Required Login - username: {self.username}')
                    session.headers.update({"User-Agent": self.user_agent})
                return session
