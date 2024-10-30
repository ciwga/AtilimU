import csv
import time
import json
import requests
import pandas as pd
from tqdm import tqdm
from pathlib import Path
from typing import NoReturn
from bs4 import BeautifulSoup
from tools.config import Config
from tools.exceptions import WrongPageError


class Curriculum:
    def __init__(self, curriculum_url: str):
        # Example webpage format
        # url = "https://www.atilim.edu.tr/tr/mechatronics/page/2263/mufredat"
        self.curriculum_url = curriculum_url.replace('/tr/', '/en/')
        if 'mufredat' not in self.curriculum_url.split('/'):
            raise WrongPageError('The URL is not an ATILIM University Curriculum Page.')

        headers = {
            'Connection': 'keep-alive',
            'user-agent': Config.user_agent,
            'referer': Config.atilim_website,
        }
        curriculum_webpage = requests.get(self.curriculum_url, headers=headers)
        self.curriculum_webpage_tree = BeautifulSoup(curriculum_webpage.content, 'html.parser')
        self.department = self.curriculum_webpage_tree.find('h2', attrs={
            'class': 'colorWhite p-0 m-b-15 m-t-0 font-400'}).text.strip()

    def get_department_name(self) -> str:
        return self.department

    def save_curriculum(
            self,
            course_ids: list,
            course_department_ids: list,
            course_names: list,
            course_codes: list,
            course_preconditions: list,
            is_elective: list,
            is_area_elective: list,
            is_selective: list,
            curriculum_name: list,
    ) -> NoReturn:
        file = Config.get_curriculum_filepath(self.department)
        try:
            with open(file, 'r', encoding='utf-8') as curr_file:
                reader = csv.reader(curr_file, delimiter=',')
                column_name = {column[0] for column in reader}
        except FileNotFoundError:
            column_name = set()

        with open(file, 'a', encoding='utf-8', newline='') as csvfile:
            writer = csv.writer(csvfile)
            if 'course_id' not in column_name:
                writer.writerow(
                    [
                        "course_id",
                        "course_department_id",
                        "course_name",
                        "course_code",
                        "course_precondition",
                        "isElective",
                        "isAreaElective",
                        "isSelective",
                        "curriculum_name",
                    ]
                )

            for course_data in tqdm(zip(
                    course_ids,
                    course_department_ids,
                    course_names,
                    course_codes,
                    course_preconditions,
                    is_elective,
                    is_area_elective,
                    is_selective,
                    curriculum_name,
            ), desc="Saving data", total=len(course_ids)):
                if str(course_data[0]) not in column_name:
                    writer.writerow(course_data)

    def extract_courses(
            self,
            class_name: str = None,
            is_elective_value=False,
            is_area_elective_value=False,
            is_selective_value=False
    ) -> NoReturn:
        if class_name:
            course_cards = self.curriculum_webpage_tree.find_all('tr', attrs={'class': class_name})
            course_card_key = 'data-lessons'
        else:
            course_cards = self.curriculum_webpage_tree.find_all('a', attrs={'class': 'lesson_card'})
            course_card_key = 'data-lesson-data'

        course_ids = []
        course_department_ids = []
        course_names = []
        course_codes = []
        course_preconditions = []
        is_elective = []
        is_area_elective = []
        is_selective = []

        for course_card in course_cards:
            if class_name:
                courses_data = json.loads(course_card.a[course_card_key])
                for course in courses_data:
                    if course['id'] not in course_ids:
                        course_id = course['id']
                        course_department_id = course['department_id']
                        course_name = course['name_eng']
                        course_code = course['code']
                        course_precondition = course['precondition']

                        course_ids.append(course_id)
                        course_department_ids.append(course_department_id)
                        course_names.append(course_name)
                        course_codes.append(course_code)
                        course_preconditions.append(course_precondition)
                        is_elective.append(is_elective_value)
                        is_area_elective.append(is_area_elective_value)
                        is_selective.append(is_selective_value)
            else:
                course_data = json.loads(course_card[course_card_key])
                if course_data['id'] not in course_ids:
                    course_id = course_data['id']
                    course_department_id = course_data['department_id']
                    course_name = course_data['name_eng']
                    course_code = course_data['code']
                    course_precondition = course_data['precondition']

                    course_ids.append(course_id)
                    course_department_ids.append(course_department_id)
                    course_names.append(course_name)
                    course_codes.append(course_code)
                    course_preconditions.append(course_precondition)
                    is_elective.append(is_elective_value)
                    is_area_elective.append(is_area_elective_value)
                    is_selective.append(is_selective_value)

        self.save_curriculum(
            course_ids,
            course_department_ids,
            course_names,
            course_codes,
            course_preconditions,
            is_elective,
            is_area_elective,
            is_selective,
            [self.department] * len(is_elective)
        )

    def main_courses(self):
        self.extract_courses()

    def area_elective_courses(self):
        self.extract_courses("technical", True, True, False)

    def selective_courses(self):
        self.extract_courses("selective", True, False, True)

    def download(self):
        self.main_courses()
        self.area_elective_courses()
        self.selective_courses()

    @staticmethod
    def load_curriculum_data(curriculum_filepath):
        curriculum_data = pd.read_csv(curriculum_filepath)
        department_name = curriculum_data["curriculum_name"][0]
        area_elective_courses = curriculum_data[curriculum_data["isAreaElective"] == True]
        area_elective_courses_ids = list(set(area_elective_courses["course_id"]))
        return department_name, area_elective_courses_ids
