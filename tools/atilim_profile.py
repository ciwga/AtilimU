import json
from bs4 import BeautifulSoup
from tools.atilim_kimlik import AtilimAuth
from pathlib import Path

profile_url: str = f"https://profil.{AtilimAuth.domain}"
profile_page_url: str = f"{profile_url}/profilim"
saml2_url: str = f"{profile_url}/saml2/acs"


class AtilimProfile:
    path = Path(__file__).parent.parent

    def __init__(self):
        Path(f"{self.path}/atilim_data").mkdir(parents=True, exist_ok=True)

    @staticmethod
    def login2profile():
        user_session = AtilimAuth().login()
        saml2_page = user_session.get(profile_url)
        soup = BeautifulSoup(saml2_page.content, features="html.parser")
        saml2_value = soup.find(name="input", attrs={"name": "SAMLResponse"})["value"]
        payload = {"SAMLResponse": saml2_value}
        user_session.post(saml2_url, data=payload)
        return user_session

    @staticmethod
    def get_profile_data() -> tuple:
        user_session = AtilimProfile.login2profile()
        profile_page = user_session.get(profile_page_url)
        soup = BeautifulSoup(profile_page.content, features="html.parser")
        # '//*[@id="kt_post"]/div[1]/div/div/div[2]\
        #  /div/div/div[2]/span/text()')[3]
        status_temp = soup.select("#kt_post > div:nth-child(1) > div > div > div:nth-child(2) "
                                  "> div > div > div:nth-child(2) > span")[0].text
        status = str(status_temp).strip()
        # '//*[@id="kt_post"]/div[1]/div/div/div[2]/\
        #  div/div/div[3]/span/text()')[1]
        department_temp = soup.select("#kt_post > div:nth-child(1) > div > div "
                                      "> div:nth-child(2) > div > div > div:nth-child(3) > span")[0].text
        department = str(department_temp).strip()
        info_spans = soup.find_all(name="span", attrs={"class": "fw-bolder fs-6 text-gray-800"})
        info_values = [info_value.text for info_value in info_spans]
        del info_values[0]

        return info_values, status, department

    def save_profile_data(self):

        variables = AtilimProfile.get_profile_data()
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
            "status": status,
            "department": department,
            "first_name": name,
            "last_name": surname,
            "student_number": student_number,
            "student_email": student_email,
            "personal_phone": phone_number,
            "personal_email": personal_email,
        }
        profile_file_path = Path(f"{self.path}/atilim_data/{student_number}_profile.json")
        with open(profile_file_path, "w", encoding="utf-8") as profile:
            json.dump(obj=profile_data, fp=profile, indent=4, ensure_ascii=False)
            print(f"{student_number}_profile.json created")


if __name__ == "__main__":
    AtilimProfile().save_profile_data()
