import json
from typing import Tuple
from pathlib import Path
from bs4 import BeautifulSoup
from tools.config import Config
from tools.kiyos_auth import AtilimAuth
from tools.exceptions import SaveError


class Profile:

    @staticmethod
    def login():
        session = AtilimAuth().login()

        is_loaded = AtilimAuth().load_cookies(session, Config.profile_cookie_keys, 'profile')
        if is_loaded:
            return session

        saml_page = session.get(Config.profile_info_url, timeout=10)
        if saml_page.status_code != 200:
            raise ConnectionError(f'Failed to retrieve profile page, status code: {saml_page.status_code}')

        saml_page_tree = BeautifulSoup(saml_page.content, 'html.parser')
        saml_value = saml_page_tree.find('input', attrs={'name': 'SAMLResponse'})['value']
        relay_state_value = saml_page_tree.find('input', attrs={'name': 'RelayState'})['value']
        payload = {'SAMLResponse': saml_value, 'RelayState': relay_state_value}

        auth_response = session.post(Config.profile_saml2_redirect_url, data=payload)
        if auth_response.status_code == 404:
            raise ConnectionError(f'Failed to authentication, status code: {auth_response.status_code}')

        AtilimAuth().save_cookies(session, Config.profile_cookie_keys, 'profile')
        return session

    @staticmethod
    def get_profile_data() -> Tuple:
        session = Profile.login()
        if not session:
            raise SaveError('Session could not be established.')

        profile_page = session.get(Config.profile_page_url, allow_redirects=True)
        if profile_page.status_code != 200:
            raise SaveError(f'Failed to retrieve profile page, status code: {profile_page.status_code}')

        soup = BeautifulSoup(profile_page.content, 'html.parser')
        status_temp = soup.select('#kt_post > div:nth-child(1) > div > div > div:nth-child(2) > '
                                  'div > div > div:nth-child(2) > span')[0].text
        status = str(status_temp).strip()
        department_temp = soup.select('#kt_post > div:nth-child(1) > div > div > div:nth-child(2) > div '
                                      '> div > div:nth-child(3) > span')[0].text
        department = str(department_temp).strip()
        info_spans = soup.find_all('span', attrs={'class': 'fw-bolder fs-6 text-gray-800'})
        info_values = [info_value.text for info_value in info_spans]
        del info_values[0]

        return info_values, status, department

    @staticmethod
    def save_profile_data():
        variables = Profile.get_profile_data()
        info_values, status, department = variables

        (
            name,
            surname,
            student_email,
            student_number,
            phone_number,
            personal_email,
        ) = info_values

        profile_data = {
            'status': status,
            'department': department,
            'first_name': name,
            'last_name': surname,
            'student_number': student_number,
            'student_email': student_email,
            'personal_phone': phone_number,
            'personal_email': personal_email,
        }
        profile_file_path = Config.get_student_profile_filepath(student_number)
        try:
            with open(profile_file_path, 'w', encoding='utf-8') as profile:
                json.dump(obj=profile_data, fp=profile, indent=4, ensure_ascii=False)
                print(f'File Created at {profile_file_path}')
        except Exception as e:
            raise SaveError(e)


if __name__ == '__main__':
    profile = Profile()
    Profile.save_profile_data()
