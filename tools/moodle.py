from tools.atilim_profile import AtilimAuth
from datetime import datetime
from bs4 import BeautifulSoup
from pathlib import Path
from tqdm import tqdm
import json
import os
import re
import random
import time


class AtilimMoodle:
    path = Path(__file__).parent.parent

    def __init__(self):
        self.userid_container = []
        self.uri = f"https://moodle.{AtilimAuth.domain}"
        Path(f"{self.path}/atilim_data/moodle").mkdir(parents=True, exist_ok=True)

    def auth_moodle(self):
        login_page = f"{self.uri}/auth/saml2/sp/saml2-acs.php/moodle.atilim.edu.tr"
        resume = f"{AtilimAuth.referer}/saml2/sso"
        session = AtilimAuth().login()

        local_time = datetime.now()
        timestamp = datetime.timestamp(local_time) * 1000

        payload = {
            "spentityid": f"{self.uri}/auth/saml2/sp/metadata.php",
            "RelayState": f"{self.uri}/login/index.php",
            "cookieTime": timestamp,
        }

        submit = session.post(resume, data=payload)
        soup = BeautifulSoup(submit.content, "html.parser")
        saml_r = soup.find("input", attrs={"name": "SAMLResponse"})["value"]
        relay_s = soup.find("input", attrs={"name": "RelayState"})["value"]

        pay_login = {"SAMLResponse": saml_r, "RelayState": relay_s}

        main_p = session.post(login_page, data=pay_login)
        soup2 = BeautifulSoup(main_p.content, "html.parser")
        href = soup2.find("a", attrs={"data-title": "logout,moodle"})["href"]
        sesskey = href.split("=")[1]

        div = soup2.find("div", attrs={"class": "logininfo"}).a
        userid = div["href"].split("=")[1]
        self.userid_container.append(userid)

        return session, sesskey

    def taken_courses(self, user_id=None, check=False):
        service = f"{self.uri}/lib/ajax/service.php"
        session, sesskey = self.auth_moodle()

        userid = user_id if user_id is not None else self.userid_container[0]

        params = {
            "sesskey": sesskey,
            "info": "core_course_get_recent_courses",
        }

        payload = [
            {
                "index": "0",
                "methodname": "core_course_get_recent_courses",
                "args": {"userid": userid},
            }
        ]

        my_courses = session.post(service, params=params, json=payload)
        jsonobject = json.loads(my_courses.content)
        courses_json_file_path = Path(f"{self.path}/atilim_data/moodle/{userid}_courses.json")
        with open(courses_json_file_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(jsonobject, indent=4, ensure_ascii=False))
        print("Fetched your taken courses database!")
        if check:
            self.save_ann_messages()

    @staticmethod
    def retriever(data: list) -> tuple:
        store = {idx["fullname"]: idx["viewurl"] for idx in data}
        indexed_store = {ix: name for ix, name in enumerate(store.keys(), 1)}
        store_shorts = {idx["fullname"]: idx["shortname"] for idx in data}
        for i, j in indexed_store.items():
            print("*" * 70)
            print(i, j)
        print("*" * 70)

        while True:
            try:
                i_input = int(input("Enter the index number of the course: "))
                selected_link = [store[indexed_store[i_input]]]
                shortname = store_shorts[indexed_store[i_input]]
                break
            except KeyError:
                print("Out of index !!")

        if os.name == "nt":
            os.system("cls")
        elif os.name == "posix":
            os.system("clear")
        else:
            pass
        return selected_link, shortname

    def save_ann_messages(self, save_all=False):
        """Save all course announcements that you enrolled in with
        :save_all=True"""
        session, sesskey = self.auth_moodle()

        jsonfile = Path(f"{self.path}/atilim_data/moodle/{self.userid_container[0]}_courses.json")
        if os.path.exists(jsonfile):
            with open(jsonfile, "r", encoding="utf-8") as j:
                jfile = json.loads(j.read())
                data = jfile[0]["data"]
                if save_all:
                    urls = [idx["viewurl"] for idx in data]
                    filename = Path(f"{self.path}/atilim_data/moodle/my_moodle_course_announcements.html")
                else:
                    urls, shortname = AtilimMoodle.retriever(data)
                    filename = Path(f"{self.path}/atilim_data/moodle/{urls[0].split('=')[1]}_{shortname}.html")

            with open(filename, "w", encoding="utf-8") as af:
                for url in urls:
                    page = session.get(url)
                    s = BeautifulSoup(page.content, "html.parser")

                    wait_time = random.uniform(1.0, 2)
                    info = str(f"Waiting for {wait_time:.2f} seconds before the next request...")
                    tqdm.write(info, end="")
                    time.sleep(wait_time)

                    try:
                        an = s.find_all("a", attrs={"class": "aalink"})
                        raw = r"https://moodle.atilim.edu.tr/mod/forum/view.php\?id="
                        for i in an:
                            raw = raw.strip()
                            regx = re.search(fr"{raw}(\d+)", str(i))
                            if regx:
                                ann_h = regx.group(0)
                                messages = session.get(ann_h)
                                s2 = BeautifulSoup(messages.content, "html.parser")
                                forum = s2.find_all(
                                    "a", attrs={"class": "w-100 h-100 d-block"}
                                )
                                anns = [x["href"] for x in forum]

                                wait_time = random.uniform(1.0, 2.4)
                                info = str(f"Waiting for {wait_time:.2f} seconds before the next request...")
                                tqdm.write(info, end="")
                                time.sleep(wait_time)

                                for ann in tqdm(anns, desc='Announcements'):
                                    msg = session.get(ann)
                                    s3 = BeautifulSoup(msg.content, "html.parser")
                                    d = s3.find(
                                        "div",
                                        attrs={"class": "d-flex flex-column w-100"},
                                    )
                                    af.write(str(d))
                                    af.write("*" * 85)

                                    wait_time = random.uniform(1.0, 3.4)
                                    info = str(f"\tWaiting for {wait_time:.2f} seconds before the next request...")
                                    tqdm.write(info, end="")
                                    time.sleep(wait_time)

                    except AttributeError:
                        pass
        else:
            self.taken_courses(check=True)


if __name__ == "__main__":
    moodle = AtilimMoodle()
    moodle.save_ann_messages()
