from bs4 import BeautifulSoup
from itertools import repeat
from tqdm import tqdm
from pathlib import Path
import requests
import json
import csv


class Curriculum:

    def __init__(self, curriculum_web_uri: str):
        self.web_uri = curriculum_web_uri
        assert "mufredat" in self.web_uri.split("/"), "(Wrong Page) The webpage url is not the curriculum page."

        user_agent: str = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.207.132.170 "
                           "Safari/537.36")
        header = {
            "Connection": "keep-alive",
            "user-agent": user_agent,
            "referer": "https://www.atilim.edu.tr",
        }
        r = requests.get(self.web_uri, headers=header)
        self.soup = BeautifulSoup(r.content, "html.parser")
        self.department = self.soup.find("h2", attrs={"class": "colorWhite p-0 m-b-15 m-t-0 font-400"})

    @staticmethod
    def save_curriculum(
        _id: list,
        department_id: list,
        name: list,
        code: list,
        precondition: list,
        is_elective: list,
        is_area_elective: list,
        is_selective: list,
        curriculum: list,
    ):
        Path('atilim_data').mkdir(parents=True, exist_ok=True)
        file_path = Path("atilim_data/curriculum_lessons_data.csv")
        try:
            with open(file_path, "r", encoding="utf-8") as csf:
                reader = csv.reader(csf, delimiter=",")
                column_name = [column[0] for column in reader]
        except FileNotFoundError:
            column_name = []

        with open(
            file_path, "a", newline="", encoding="utf-8"
        ) as csvfile:
            writer = csv.writer(csvfile)
            if "lesson_id" not in column_name:
                writer.writerow(
                    [
                        "lesson_id",
                        "department_id",
                        "lesson_name",
                        "lesson_code",
                        "lesson_precondition",
                        "isElective",
                        "isAreaElective",
                        "isSelective",
                        "curriculum_name",
                    ]
                )
            for row in tqdm(zip(
                _id,
                department_id,
                name,
                code,
                precondition,
                is_elective,
                is_area_elective,
                is_selective,
                curriculum,
            ), desc="Saving data", total=len(_id)):
                if str(row[0]) not in column_name:
                    writer.writerow(row)

    def lessons(self):
        lessons = self.soup.find_all("a", attrs={"class": "lesson_card"})

        lesson_ids = []
        department_ids = []
        lesson_codes = []
        lesson_preconditions = []
        lesson_names = []
        is_elective = []
        is_area_elective = []
        is_selective = []

        for lesson in lessons:
            lesson_data = json.loads(lesson["data-lesson-data"])
            lesson_id = lesson_data["id"]
            department_id = lesson_data["department_id"]
            lesson_code = lesson_data["code"]
            lesson_precondition = lesson_data["precondition"]
            lesson_name = lesson_data["name_eng"]

            lesson_ids.append(lesson_id)
            department_ids.append(department_id)
            lesson_codes.append(lesson_code)
            lesson_preconditions.append(lesson_precondition)
            lesson_names.append(lesson_name)
            is_elective.append(False)
            is_area_elective.append(False)
            is_selective.append(False)

        Curriculum.save_curriculum(
            lesson_ids,
            department_ids,
            lesson_names,
            lesson_codes,
            lesson_preconditions,
            is_elective,
            is_area_elective,
            is_selective,
            list(repeat(self.department.text.strip(), len(is_elective))),
        )

    def area_elective_lessons(self):
        technical = self.soup.find_all("tr", attrs={"class": "technical"})

        area_elective_ids = []
        area_elective_department_ids = []
        area_elective_codes = []
        area_elective_preconditions = []
        area_elective_names = []
        is_elective = []
        is_area_elective = []
        is_selective = []

        for tech in technical:
            data_lessons = json.loads(tech.a["data-lessons"])
            for data_lesson in data_lessons:
                area_elective_lesson_id = data_lesson["id"]
                area_elective_lesson_department_id = data_lesson["department_id"]
                area_elective_lesson_code = data_lesson["code"]
                area_elective_lesson_precondition = data_lesson["precondition"]
                area_elective_name = data_lesson["name_eng"]

                if area_elective_lesson_id not in area_elective_ids:
                    area_elective_ids.append(area_elective_lesson_id)
                    area_elective_department_ids.append(
                        area_elective_lesson_department_id
                    )
                    if area_elective_lesson_code == "MFGE482":
                        area_elective_lesson_code = "ME482"
                    area_elective_codes.append(area_elective_lesson_code)
                    area_elective_preconditions.append(
                        area_elective_lesson_precondition
                    )
                    area_elective_names.append(area_elective_name)
                    is_area_elective.append(True)
                    is_elective.append(True)
                    is_selective.append(False)

        Curriculum.save_curriculum(
            area_elective_ids,
            area_elective_department_ids,
            area_elective_names,
            area_elective_codes,
            area_elective_preconditions,
            is_elective,
            is_area_elective,
            is_selective,
            list(repeat(self.department.text.strip(), len(is_elective))),
        )

    def selective_lessons(self):
        selective = self.soup.find_all("tr", attrs={"class": "selective"})

        selective_ids = []
        selective_department_ids = []
        selective_codes = []
        selective_preconditions = []
        selective_names = []
        is_elective = []
        is_area_elective = []
        is_selective = []

        for select in selective:
            selective_data_lessons = json.loads(select.a["data-lessons"])
            for selective_data_lesson in selective_data_lessons:
                selective_id = selective_data_lesson["id"]
                selective_department_id = selective_data_lesson["department_id"]
                selective_code = selective_data_lesson["code"]
                selective_precondition = selective_data_lesson["precondition"]
                selective_name = selective_data_lesson["name_eng"]

                if selective_id not in selective_ids:
                    if "GET" not in selective_code:
                        selective_ids.append(selective_id)
                        selective_department_ids.append(selective_department_id)
                        selective_codes.append(selective_code)
                        selective_preconditions.append(selective_precondition)
                        selective_names.append(selective_name)
                        is_area_elective.append(False)
                        is_elective.append(True)
                        is_selective.append(True)

        Curriculum.save_curriculum(
            selective_ids,
            selective_department_ids,
            selective_names,
            selective_codes,
            selective_preconditions,
            is_elective,
            is_area_elective,
            is_selective,
            list(repeat(self.department.text.strip(), len(is_elective))),
        )

    def run_all(self):
        self.lessons()
        self.area_elective_lessons()
        self.selective_lessons()


if __name__ == "__main__":
    # Example webpage format
    uri = "https://www.atilim.edu.tr/tr/mechatronics/page/2263/mufredat"
    cur = Curriculum(uri)
    cur.run_all()
