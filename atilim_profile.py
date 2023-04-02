from bs4 import BeautifulSoup
from lxml import etree
import configparser
import requests
import json
import os


class LoginError(Exception):
    def __init__(self, message):
        super().__init__(message)


class atilim_kimlik:

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

    def login(self, uri=kimlik_uri,
              ref=referer, ua=user_agent) -> requests.Session:

        header = {
            "Connection": "keep-alive",
            "Referer": ref,
            "User-Agent": ua
        }

        payload = {
            'loginName': self.username,
            'passwd': self.password
        }

        with requests.Session() as session:
            session.headers.update(header)
            post = session.post(uri, json=payload)
            if json.loads(post.content)['success'] is False:
                raise LoginError('Invalid username or password')
            else:
                return session

    def profile_atilim(self, profile=profile_uri) -> tuple:
        saml2 = f'{profile}/saml2/acs'
        login = self.login()
        _getSaml2 = login.get(profile)
        soup_2 = BeautifulSoup(_getSaml2.content, 'html.parser')
        samlr = soup_2.find('input', attrs={'name': 'SAMLResponse'})['value']

        payload = {
            'SAMLResponse': samlr
        }
        login.post(saml2, data=payload)
        my_profile_uri = f'{profile}/profilim'
        my_profile = login.get(my_profile_uri)

        soup = BeautifulSoup(my_profile.content, 'html.parser')
        dom = etree.HTML(str(soup))
        s = dom.xpath('//*[@id="kt_post"]/div[1]/div/div/div[2]\
            /div/div/div[2]/span/text()')[3]
        status = str(s).strip()
        d = dom.xpath('//*[@id="kt_post"]/div[1]/div/div/div[2]/\
            div/div/div[3]/span/text()')[1]
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
    atilim = atilim_kimlik()
    atilim.save_profile_atilim()
