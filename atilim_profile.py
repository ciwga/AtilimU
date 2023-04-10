from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import configparser
import requests
import json
import os
import pickle


class LoginError(Exception):
    def __init__(self, message):
        super().__init__(message)


class Atilim_Kimlik:

    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'\
                 'AppleWebKit/537.36 (KHTML, like Gecko)'\
                 'Chrome/109.0.0.0 Safari/537.36'
    domain = 'atilim.edu.tr'
    referer = f'https://kimlik.{domain}'
    profile_uri = f'https://profil.{domain}'
    kimlik_uri = f'{referer}/ui/login'

    def __init__(self):
        config = configparser.ConfigParser()
        if os.path.isfile('atilim_config.ini'):
            config.read('atilim_config.ini')
            self.username = config['kimlik']['username']
            self.password = config['kimlik']['password']

        else:
            username = str(input('Enter your username: '))
            password = str(input('Enter you password: '))
            self.username = username
            self.password = password

            with open('atilim_config.ini', 'w', encoding='utf-8') as conf:
                config.add_section('kimlik')
                config['kimlik']['username'] = self.username
                config['kimlik']['password'] = self.password
                config.write(conf)
            print('Username and password are saved in atilim_config.ini!')

    def get_session(self) -> requests.Session:

        header = {
            "Connection": "keep-alive",
            "Referer": self.referer,
            "User-Agent": self.user_agent
        }

        payload = {
            'loginName': self.username,
            'passwd': self.password
        }

        with requests.Session() as session:
            session.headers.update(header)
            post = session.post(self.kimlik_uri, json=payload)
            if json.loads(post.content)['success'] is False:
                raise LoginError('Invalid username or password')
            else:
                with open('atilim-session', 'wb') as s:
                    pickle.dump(session, s)
                return session

    def login(self):
        if os.path.exists('atilim-session'):
            m_time = os.stat('atilim-session').st_mtime
            mtime = datetime.fromtimestamp(m_time)
            now = datetime.now()
            elapsed = now - mtime
            if elapsed > timedelta(minutes=20):
                '''Maximum timeout limit is 120 minutes'''
                return self.get_session()
            else:
                with requests.Session() as session:
                    with open('atilim-session', 'rb') as s:
                        cookie = pickle.load(s)
                        session.cookies.update(cookie.cookies)
                    return session
        else:
            return self.get_session()

    def profile_atilim(self) -> tuple:
        saml2 = f'{self.profile_uri}/saml2/acs'
        login = self.login()
        _getSaml2 = login.get(self.profile_uri)
        soup_2 = BeautifulSoup(_getSaml2.content, 'html.parser')
        samlr = soup_2.find('input', attrs={'name': 'SAMLResponse'})['value']

        payload = {
            'SAMLResponse': samlr
        }
        login.post(saml2, data=payload)
        my_profile_uri = f'{self.profile_uri}/profilim'
        my_profile = login.get(my_profile_uri)

        soup = BeautifulSoup(my_profile.content, 'html.parser')
        # '//*[@id="kt_post"]/div[1]/div/div/div[2]\
        #  /div/div/div[2]/span/text()')[3]
        s = soup.select('#kt_post > div:nth-child(1) > div > div >\
         div:nth-child(2) > div > div > div:nth-child(2) > span')[0].text
        status = str(s).strip()
        # '//*[@id="kt_post"]/div[1]/div/div/div[2]/\
        #  div/div/div[3]/span/text()')[1]
        d = soup.select('#kt_post > div:nth-child(1) > div > div >\
         div:nth-child(2) > div > div > div:nth-child(3) > span')[0].text
        department = str(d).strip()

        spans = soup.find_all('span',
                              attrs={'class': 'fw-bolder fs-6 text-gray-800'})
        values = [value.text for value in spans]
        del values[0]
        return values, status, department

    def save_profile_atilim(self) -> None:
        values = self.profile_atilim()
        items, status, department = values
        (name, surname, student_email, student_number,
            phone_number, personal_email) = items

        person = {
            'status': status,
            'department': department,
            'first_name': name,
            'last_name': surname,
            'student_number': student_number,
            'student_email': student_email,
            'personal_phone': phone_number,
            'personal_email': personal_email
        }

        with open('my_profile.json', 'w', encoding='utf-8') as my:
            json.dump(person, my, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    atilim = Atilim_Kimlik()
    atilim.save_profile_atilim()
