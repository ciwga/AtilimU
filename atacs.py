from atilim_kimlik import AtilimAuth
from bs4 import BeautifulSoup
from pathlib import Path
from tqdm import tqdm
from io import StringIO
import pandas as pd
import random
import time


class Atacs:
    atacs_uri = f"https://atacs.{AtilimAuth.domain}"

    def __init__(self):
        Path("atilim_data").mkdir(parents=True, exist_ok=True)

    def login(self) -> AtilimAuth.login:
        auth_uri = f"{self.atacs_uri}/Auth/AssertionConsumerService"
        session = AtilimAuth().login()

        saml = session.get(self.atacs_uri)
        soup = BeautifulSoup(saml.content, "html.parser")
        saml_response = soup.find("input", attrs={"name": "SAMLResponse"})["value"]
        relay_state = soup.find("input", attrs={"name": "RelayState"})["value"]

        payload = {"SAMLResponse": saml_response, "RelayState": relay_state}
        session.post(auth_uri, data=payload)

        return session

    def save_atacs_messages(self) -> None:
        inbox_uri = f"{self.atacs_uri}/OgrenciMesaj/Ogrenci_Gelenkutusu"
        message_file_path = Path("atilim_data/atacs_messages.html")

        session = self.login()
        session.headers.update({"Referer": self.atacs_uri})

        inbox_page = session.get(inbox_uri)
        soup = BeautifulSoup(inbox_page.content, "html.parser")
        buttons = soup.find_all("button", attrs={"class": "btn btn-link"})
        click_buttons = (button["onclick"].split("/")[-1].replace("'", "") for button in buttons)
        message_codes = [code for code in click_buttons if code.isnumeric()]

        html_table = pd.read_html(StringIO(inbox_page.text))
        inbox_dataframe = html_table[0]
        try:
            del inbox_dataframe["SİL"]
            del inbox_dataframe["CEVAPLA"]
        except KeyError:
            del inbox_dataframe["DELETE"]
            del inbox_dataframe["REPLY"]
        del inbox_dataframe[inbox_dataframe.columns[-1]]

        inbox_dataframe.columns = ["name", "surname", "subject", "date", "id"]
        inbox_dataframe["id"] = pd.Series(message_codes)

        inbox_payload = {"Tip": "1"}

        with open(message_file_path, "a+", encoding="utf-8") as f:
            for index in tqdm(range(len(inbox_dataframe['id'])), desc="Fetched Msg", total=len(inbox_dataframe['id'])):
                msg_detail_uri = f"{self.atacs_uri}/OgrenciMesaj/Ogrenci_MesajGoruntule/{inbox_dataframe['id'][index]}"
                msg_detail_page = session.get(msg_detail_uri, data=inbox_payload)
                msg_detail_soup = BeautifulSoup(msg_detail_page.content, "html.parser")

                sender = msg_detail_soup.find("input", attrs={"id": "Name"})["value"]
                subject = msg_detail_soup.find("input", attrs={"id": "Konu"})["value"]
                message = msg_detail_soup.find("textarea", attrs={"id": "Icerik"}).text

                f.seek(0)
                if message.strip() not in f.read():
                    f.write(f"<p><b>From:</b> {sender}</p>\n")
                    f.write(f"<p><b>Subject:</b> {subject} </p>\n")
                    f.write(f"<p><b>Date:</b> {inbox_dataframe['date'][index]}</p>\n")
                    f.write(f"<b>Message:</b> {message.strip()}\n")
                    f.write(f"<p><b>{'*'*200}</b></p>\n")

                wait_time = random.uniform(1.0, 6.0)
                tqdm.write(f"\tWaiting for {wait_time:.2f} seconds before the next request...", end='')
                time.sleep(wait_time)

    def save_financial_pay_table(self) -> None:
        table_uri = f"{self.atacs_uri}/OgrenciFinans/Ogr_Bilgi_getir"
        pay_file_path = Path("atilim_data/atilim_financial_pay_table.csv")

        session = self.login()
        session.headers.update({"Referer": f"{self.atacs_uri}/OgrenciFinans"})

        table_payload = {"ogr_no": ""}
        table_page = session.post(table_uri, data=table_payload)
        pay_dataframe = pd.read_html(StringIO(table_page.text))[2]

        last_column = pay_dataframe[pay_dataframe.columns[-1]]
        if last_column.str.contains("\u20ba").any():
            last_column = last_column.str.replace("\u20ba", "").str.strip().str.replace(",", ".")
            currency = "\u20ba"
        else:
            last_column = last_column.str.replace("\u0024", "").str.strip().str.replace(",", ".")
            currency = "\u0024"
        
        pay_dataframe[pay_dataframe.columns[-1]] = last_column
        pay_dataframe[pay_dataframe.columns[-1]] = pay_dataframe[pay_dataframe.columns[-1]].astype(float)
        pay_dataframe.to_csv(pay_file_path, index=False)
        
        try:
            collection = pay_dataframe[pay_dataframe[pay_dataframe.columns[-3]] == "Tahsilat"]
        except KeyError:
            collection = pay_dataframe[pay_dataframe[pay_dataframe.columns[-3]] == "Collection"]

        total_paid_money = collection[collection.columns[-1]].sum()
        print(f"Total paid money: {total_paid_money} {currency}")

    def save_kvkk_form(self) -> None:
        kvkk_uri = f"{self.atacs_uri}/Kvkk/ReviewForm"
        kvkk_file_path = Path("atilim_data/atilim_kvkk_form.html")

        session = self.login()

        form = session.get(kvkk_uri)
        soup = BeautifulSoup(form.content, "html.parser")
        content = soup.find("div", attrs={"class": "content"})

        with open(kvkk_file_path, "w", encoding="utf-8") as kvkk:
            kvkk.write(str(content))


if __name__ == "__main__":
    Atacs().save_atacs_messages()
