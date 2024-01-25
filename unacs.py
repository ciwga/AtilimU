from atilim_kimlik import AtilimAuth
from atilim_curriculum import Curriculum
from pathlib import Path
from bs4 import BeautifulSoup
from tqdm import tqdm
import pandas as pd
import json
import re
import sys
import time
import random


class UniversityAcademicSystem:
    main_uri: str = "https://unacs.atilim.edu.tr"
    api: str = "https://unacs-api.atilim.edu.tr/api"
    token: str = ""

    def login(self):
        unacs_login_uri = f"{self.api}/Identity/Auth/Login?returnUrl={self.api}/Identity/Auth/AssertionConsumerService"
        auth_uri = f"{self.api}/Identity/Auth/AssertionConsumerService"

        session = AtilimAuth().login()
        session.headers.update(
            {
                "origin": "https://kimlik.atilim.edu.tr",
                "referer": "https://kimlik.atilim.edu.tr/",
            }
        )
        del session.headers["Connection"]

        saml = session.get(unacs_login_uri)
        soup = BeautifulSoup(saml.content, "html.parser")
        saml_response = soup.find("input", attrs={"name": "SAMLResponse"})["value"]
        relay_state = soup.find("input", attrs={"name": "RelayState"})["value"]

        payload = {"SAMLResponse": saml_response, "RelayState": relay_state}
        auth_response = session.post(auth_uri, data=payload, allow_redirects=False)
        token_header = auth_response.headers["Location"]

        self.token = re.sub(pattern=r"^.*tokenreader\?t=", repl="", string=token_header)
        session.headers.update({"Authorization": f"Bearer {self.token}"})

        return session

    def get_opened_area_elective_courses(self):
        Path("atilim_data").mkdir(parents=True, exist_ok=True)
        curriculum_file_path = Path("atilim_data/curriculum_lessons_data.csv")
        if not curriculum_file_path.exists():
            webpage = input("Enter Curriculum Webpage URL: ")
            Curriculum(webpage).run_all()

        cur_data = pd.read_csv(curriculum_file_path)
        department_name = cur_data["curriculum_name"][0]
        area_elective_courses = cur_data[cur_data["isAreaElective"] == bool(True)]
        area_elective_courses_ids = list(set(area_elective_courses["lesson_id"]))

        session = self.login()
        session.headers["referer"] = f"{self.main_uri}/acilan-dersler-report"
        course_uri = f"{self.api}/AcilanDerslerRaporu/GetAcilanDerslerReport"
        term_uri = f"{self.api}/Common/Get2016AfterDonemList"
        current_term = session.get(term_uri).json()["responseData"][0]["id"]
        temp_file_name = Path(f"atilim_data/temp_{current_term}_opened_courses.json")

        with (tqdm(total=len(area_elective_courses_ids),
                   desc=f"Fetching Courses") as pbar):
            for course_id in area_elective_courses_ids:
                payload = {
                    "BOLUM_ID": -1,
                    "DERS_ID": course_id,
                    "DONEM_ID": current_term,
                    "FAKULTE_ID": -1,
                }
                course = session.post(course_uri, json=payload)

                if course.status_code == 200:
                    course = course.json()["responseData"]

                    if course:
                        with open(temp_file_name, "a+", encoding="utf-8") as f:
                            json.dump(course, f, ensure_ascii=False, indent=4)

                wait_time = random.uniform(2.0, 5.5)
                info = str(f"\tWaiting for {wait_time:.2f} seconds before the next request...")
                tqdm.write(info, end="")
                time.sleep(wait_time)
                pbar.update()

        area_elective_csv_file = Path("atilim_data/area_elective_opened_courses.csv")
        textfile_name = Path(f"atilim_data/area_elective_courses{current_term}.txt")

        if area_elective_csv_file.exists():
            Path(area_elective_csv_file).unlink()
            textfile_name.unlink(missing_ok=True)

        with open(temp_file_name, "r", encoding="utf-8") as f:
            course = re.sub(pattern=r"\]\[", repl=",", string=f.read())
            opened_courses = json.loads(course)
            df = pd.DataFrame(opened_courses)
            df.to_csv(area_elective_csv_file, index=False)
            course_codes = df["derS_KODU"]
            course_names = df["derS_ADI"]
            sections = df["subE_NO"]
            teachers = df["ogretiM_UYELER"]
            teacher_type = df["ogretiM_UYE_PERSONEL_TUR"]
            teacher_email = df["oU_EMAIL"]
            quotas = df["toplaM_KONTENJAN"]
            course_credits = df["kredi"]
            course_ects_credits = df["akts"]

            for (
                course_code,
                course_name,
                section,
                teacher,
                teacher_type,
                teacher_email,
                quota,
                course_credit,
                course_ects_credit,
            ) in zip(
                course_codes,
                course_names,
                sections,
                teachers,
                teacher_type,
                teacher_email,
                quotas,
                course_credits,
                course_ects_credits,
            ):
                if department_name in str(quota):
                    try:
                        pattern = (
                            rf"{department_name}\(Lisans\)\(İngilizce\) : (\d+) / (\d+)"
                        )
                        kota = re.search(pattern, quota).group(0)
                        kota = kota.split("/")[1].strip()
                        output_opened = (
                            f"{course_code}|{course_name}|0/{kota}|{section}|{teacher}|{teacher_type}|"
                            f"{teacher_email}|{course_credit} credit|{course_ects_credit} akts/ects"
                        )
                        with open(
                            textfile_name, "a+", encoding="utf-8"
                        ) as textfile_true:
                            textfile_true.write("-" * len(output_opened) + "\n")
                            textfile_true.write(output_opened + "\n")
                            textfile_true.write("-" * len(output_opened) + "\n")
                    except Exception as e:
                        print(
                            f"Skipping Exception: {e} in {__file__} line {sys.exc_info()[-1].tb_lineno}"
                        )
                        pass
                else:
                    output_not_opened = (
                        f"Opened without Quotas for your Department: {course_code}|{course_name}|"
                        f"{section}|{teacher}|"
                        f"{teacher_type}|{teacher_email}|{course_credit} "
                        f"credit|{course_ects_credit} akts/ects"
                    )
                    with open(textfile_name, "a+", encoding="utf-8") as textfile_false:
                        textfile_false.write(output_not_opened + "\n")
        Path(temp_file_name).unlink()


if __name__ == "__main__":
    UniversityAcademicSystem().get_opened_area_elective_courses()
