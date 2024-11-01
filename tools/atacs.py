import time
import random
import pandas as pd
from tqdm import tqdm
from io import StringIO
from pathlib import Path
from bs4 import BeautifulSoup
from tools.config import Config
from typing import NoReturn, Any
from tools.kiyos_auth import AtilimAuth
from tools.exceptions import SaveError, StudentArchiveAccessException


class Atacs:

    @staticmethod
    def login():
        session = AtilimAuth().login()
        AtilimAuth().load_cookies(session, Config.atacs_cookie_keys, 'atacs')
        session.cookies.set('language', 'tr')
        saml = session.get(Config.atacs_url)
        soup = BeautifulSoup(saml.content, 'html.parser')
        saml_response = soup.find('input', attrs={'name': 'SAMLResponse'})['value']
        relay_state = soup.find('input', attrs={'name': 'RelayState'})['value']
        payload = {'SAMLResponse': saml_response, 'RelayState': relay_state}
        auth_service = session.post(Config.atacs_auth_url, data=payload, allow_redirects=False)
        redirection_url = auth_service.headers['Location']
        if 'OgrenciArsivHata' in redirection_url:
            raise StudentArchiveAccessException('Graduated students cannot access.')
        session.get(redirection_url)
        AtilimAuth().save_cookies(session, Config.atacs_cookie_keys, 'atacs')
        return session

    @staticmethod
    def save_atacs_inbox_messages() -> NoReturn:
        session = Atacs.login()
        session.headers.update({'Referer': Config.atacs_url})
        atacs_inbox_webpage = session.get(Config.atacs_inbox_url)
        soup = BeautifulSoup(atacs_inbox_webpage.content, 'html.parser')
        message_buttons = soup.find_all('button', attrs={'class': 'btn btn-link'})
        click_msg_buttons = (button['onclick'].split('/')[-1].replace("'", '') for button in message_buttons)
        message_codes = [code for code in click_msg_buttons if code.isnumeric()]

        inbox_msg_table = pd.read_html(StringIO(atacs_inbox_webpage.text))
        inbox_msgs_df = inbox_msg_table[0]
        for col in ["SİL", "CEVAPLA", "OKU", "DELETE", "REPLY", "READ"]:
            inbox_msgs_df.drop(columns=col, errors='ignore', inplace=True)
        inbox_msgs_df.columns = ["name", "surname", "subject", "date", "id"]
        inbox_msgs_df["id"] = pd.Series(message_codes)
        pbar = tqdm(range(len(inbox_msgs_df['id'])), desc='Fetched Msg')

        try:
            with open(Config.get_atacs_inbox_messages_filepath(), 'a+', encoding='utf-8') as file:
                for index in pbar:
                    inbox_msg_url = Config.get_atacs_inbox_message_view_link(inbox_msgs_df['id'], index)
                    inbox_msg_page = session.get(inbox_msg_url, data={'Tip': '1'})
                    msg_page_soup = BeautifulSoup(inbox_msg_page.content, 'html.parser')

                    sender = msg_page_soup.find('input', attrs={'id': 'Name'})['value']
                    subject = msg_page_soup.find('input', attrs={'id': 'Konu'})['value']
                    message_content = msg_page_soup.find('textarea', attrs={'id': 'Icerik'}).text
                    file.seek(0)
                    if message_content.strip() not in file.read():
                        file.write(f"<p><b>From:</b> {sender}</p>\n")
                        file.write(f"<p><b>Subject:</b> {subject} </p>\n")
                        file.write(f"<p><b>Date:</b> {inbox_msgs_df['date'][index]}</p>\n")
                        file.write(f"<b>Message:</b> {message_content.strip()}\n")
                        file.write(f"<p><b>{'*' * 200}</b></p>\n")

                    wait_time = random.uniform(1.0, 2.8)
                    info = f'Waiting for {wait_time:.2f} seconds before the next request...'
                    pbar.set_postfix(info=info)
                    time.sleep(wait_time)
        except Exception as e:
            raise SaveError(f'Failed to save ATACS inbox messages: {e}')

    @staticmethod
    def save_atacs_financial_pay_table() -> NoReturn:
        session = Atacs.login()
        session.headers.update({'Referer': Config.atacs_student_finance_url})
        financial_table_page = session.post(Config.atacs_financial_table_url, data={'ogr_no': ''})
        try:
            financial_frame = pd.read_html(StringIO(financial_table_page.text))[2]
            financial_frame.rename(columns={financial_frame.columns[-3]: 'Collection'}, inplace=True)
            financial_frame.to_csv(Config.get_atacs_financial_table_filepath(), index=False)
        except Exception as e:
            raise SaveError(f'Failed to save ATACS financial pay table: {e}')

    @staticmethod
    def fetch_atacs_financial_information() -> NoReturn:
        if not Config.get_atacs_financial_table_filepath().exists():
            Profile.save_atacs_financial_pay_table()

        financial_frame = pd.read_csv(Config.get_atacs_financial_table_filepath())
        amount_column = financial_frame[financial_frame.columns[-1]]

        currency_map = {
            '₺': '\u20ba',
            '€': '\u20ac',
            '$': '\u0024',
        }

        currency = None
        for currency_symbol, sign in currency_map.items():
            if amount_column.str.contains(sign).any():
                amount_column = amount_column.str.replace(sign, '').str.strip().str.replace(',', '.')
                currency = currency_symbol
                break

        amount_column = amount_column.astype(float)
        financial_frame[financial_frame.columns[-1]] = amount_column
        collection = financial_frame['Tutar']
        total_paid_money = collection.sum()
        print(f'Total paid money: {total_paid_money} {currency}')

    @staticmethod
    def save_kvkk_form() -> NoReturn:
        session = Atacs.login()
        form_webpage = session.get(Config.atacs_kvkk_form_url)
        soup = BeautifulSoup(form_webpage.content, 'html.parser')
        form_content = soup.find('div', attrs={'class': 'content'})
        try:
            with open(Config.get_atacs_kvkk_form_filepath(), 'w', encoding='utf-8') as kvkk_file:
                kvkk_file.write(str(form_content))
            print('Kvkk form has been saved.')
        except Exception as e:
            raise SaveError(f'Failed to save ATACS KVKK form: {e}')
