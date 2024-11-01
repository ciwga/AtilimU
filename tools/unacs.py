import re
import sys
import json
import time
import random
import asyncio
import aiohttp
import aiofiles
import requests
import pandas as pd
from tqdm import tqdm
from pathlib import Path
from bs4 import BeautifulSoup
from tools.config import Config
from tools.profile import Profile
from tools.curriculum import Curriculum
from tools.kiyos_auth import AtilimAuth
from tqdm.asyncio import tqdm as async_tqdm
from tools.helpers import user_interactions, select_from_response_data
from tools.exceptions import NoCoursesAvailableError, NotGraduatedError


class Unacs:

    @staticmethod
    def login():
        session = AtilimAuth().login()
        AtilimAuth().load_cookies(session, Config.unacs_cookie_keys, 'unacs')
        session.headers.update(
            {
                'origin': Config.kiyos_url,
                'referer': Config.kiyos_url
            }
        )
        if 'Connection' in session.headers:
            del session.headers['Connection']

        saml_page = session.get(Config.unacs_login_url)
        saml_page_tree = BeautifulSoup(saml_page.content, 'html.parser')
        saml_value = saml_page_tree.find('input', attrs={'name': 'SAMLResponse'})['value']
        relay_state_value = saml_page_tree.find('input', attrs={'name': 'RelayState'})['value']

        payload = {'SAMLResponse': saml_value, 'RelayState': relay_state_value}
        unacs_auth_page = session.post(Config.unacs_auth_url, data=payload, allow_redirects=False)
        auth_token_url = unacs_auth_page.headers['Location']
        token = re.sub(pattern=r'^.*tokenreader\?t=', repl='', string=auth_token_url)
        session.headers.update({'Authorization': f'Bearer {token}'})
        AtilimAuth().save_cookies(session, Config.unacs_cookie_keys, 'unacs')
        return session

    @staticmethod
    def get_opened_area_elective_courses():
        _, __, department = Profile.get_profile_data()
        department = ' '.join(department.split()[:2])
        print(f'You are studying in {department}. Do you want to keep going with that?')
        action = user_interactions()

        if action == 0:
            major_curr_filepath = Config.get_curriculum_filepath(department)
            if major_curr_filepath.exists():
                print(f'\nCurriculum file found at {major_curr_filepath}. Do you want to update it?')
                major_action = user_interactions()
                if major_action == 0:
                    curriculum_webpage = str(input('Enter Curriculum Webpage URL: '))
                    Curriculum(curriculum_webpage).download()
            else:
                curriculum_webpage = str(input('Enter Curriculum Webpage URL: '))
                Curriculum(curriculum_webpage).download()

            department_name, area_elective_courses_ids = Curriculum.load_curriculum_data(major_curr_filepath)

        else:
            curriculum_webpage = str(input('Enter Curriculum Webpage URL: '))
            user_req_department = Curriculum(curriculum_webpage).get_department_name()
            curriculum_filepath = Config.get_curriculum_filepath(user_req_department)

            if curriculum_filepath.exists():
                print(f'Curriculum file found at {curriculum_filepath}. Do you want to update it?')
                alter_action = user_interactions()
                if alter_action == 0:
                    Curriculum(curriculum_webpage).download()
            else:
                Curriculum(curriculum_webpage).download()

            department_name, area_elective_courses_ids = Curriculum.load_curriculum_data(curriculum_filepath)

        session = Unacs.login()
        session.headers['referer'] = Config.unacs_opened_courses_referer_url
        terms_list = session.get(Config.unacs_term_courses_url)
        if terms_list.status_code == 403:
            raise ConnectionError('Have you graduated? If your answer is yes, you cannot reach the website.')
        if terms_list.json()['success'] is False:
            raise ConnectionError('Something goes wrong. Try again...')
        current_term_card = terms_list.json()['responseData']
        # current_term_name_tr = 'ad'
        current_term_name_en, current_term = select_from_response_data(current_term_card, 'aD_EN', 'id')
        temp_file = Config.get_unacs_current_term_opened_courses_temporary_filepath(department_name, current_term)
        if temp_file.exists():
            temp_file.unlink(missing_ok=True)

        test_payload = {
            'BOLUM_ID': 141,    #  mechatronics
            'DERS_ID': -1,
            'DONEM_ID': current_term,
            'FAKULTE_ID': 2,    #  engineering
        }
        test_request = session.post(Config.unacs_opened_courses_url, json=test_payload)
        if not test_request.json()['responseData']:
            raise NoCoursesAvailableError(f'There are no available courses in {current_term_name_en}') 
        
        with (tqdm(total=len(area_elective_courses_ids),
                   desc=f'Fetching Courses', position=0) as pbar):
            for course_id in area_elective_courses_ids:
                payload = {
                    'BOLUM_ID': -1,
                    'DERS_ID': course_id,
                    'DONEM_ID': current_term,
                    'FAKULTE_ID': -1,
                }
                course = session.post(Config.unacs_opened_courses_url, json=payload)

                if course.status_code == 200:
                    course = course.json()['responseData']           

                    if course:
                        with open(temp_file, 'a+', encoding='utf-8') as f:
                            json.dump(course, f, ensure_ascii=False, indent=4)

                wait_time = random.uniform(1.0, 1.8)
                info = f'Waiting for {wait_time:.2f} seconds before the next request...'
                pbar.set_postfix(info=info)
                time.sleep(wait_time)
                pbar.update()

        area_elective_csv_file = Config.get_unacs_area_elective_opened_courses_csv_filepath(department_name,
                                                                                            current_term)
        textfile_name = Config.get_unacs_area_elective_opened_courses_txt_filepath(department_name, current_term)

        if area_elective_csv_file.exists():
            area_elective_csv_file.unlink(missing_ok=True)
            textfile_name.unlink(missing_ok=True)

        with open(temp_file, 'r', encoding='utf-8') as f:
            course = re.sub(pattern=r'\]\[', repl=',', string=f.read())
            opened_courses = json.loads(course)
            df = pd.DataFrame(opened_courses)
            df.to_csv(area_elective_csv_file, index=False)
            course_codes = df['derS_KODU']
            course_names = df['derS_ADI']
            sections = df['subE_NO']
            teachers = df['ogretiM_UYELER']
            teacher_type = df['ogretiM_UYE_PERSONEL_TUR']
            teacher_email = df['oU_EMAIL']
            quotas = df['toplaM_KONTENJAN']
            course_credits = df['kredi']
            course_ects_credits = df['akts']

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
                            rf'{department_name}\(Lisans\)\(İngilizce\) : (\d+) / (\d+)'
                        )
                        kota = re.search(pattern, quota).group(0)
                        kota = kota.split('/')[1].strip()
                        output_opened = (
                            f'{course_code}|{course_name}|0/{kota}|{section}|{teacher}|{teacher_type}|'
                            f'{teacher_email}|{course_credit} credit|{course_ects_credit} akts/ects'
                        )
                        with open(
                                textfile_name, 'a+', encoding='utf-8'
                        ) as textfile_true:
                            textfile_true.write('-' * len(output_opened) + '\n')
                            textfile_true.write(output_opened + '\n')
                            textfile_true.write('-' * len(output_opened) + '\n')
                    except Exception as e:
                        print(
                            f'Skipping Exception: {e} in {__file__} line {sys.exc_info()[-1].tb_lineno}'
                        )
                        pass
                else:
                    output_not_opened = (
                        f'Opened without Quotas for your Department: {course_code}|{course_name}|'
                        f'{section}|{teacher}|'
                        f'{teacher_type}|{teacher_email}|{course_credit} '
                        f'credit|{course_ects_credit} akts/ects'
                    )
                    with open(textfile_name, 'a+', encoding='utf-8') as textfile_false:
                        textfile_false.write(output_not_opened + '\n')
        print('You can find the available area elective courses in the files mentioned below.')
        print(f'TXT File Created at {textfile_name}')
        print(f'CSV File Created at {area_elective_csv_file}')
        temp_file.unlink()

    @classmethod
    def download_graduation_photos(cls):
        filepath = Config.get_unacs_graduation_photos_folderpath()
        session = cls.login()
        session.headers.update(
            {
                'origin': Config.unacs_url,
                'referer': Config.unacs_url,
                'priority': 'u=1, i',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept': 'application/json, text/plain, */*'
            }
        )
        check_graduate = session.get(Config.unacs_check_graduation_student_url)
        if check_graduate.status_code == 200:
            is_graduate = check_graduate.json()['responseData']
            if is_graduate is False:
                raise NotGraduatedError('You must have attended the graduation ceremony to download photos !')
        file_names_server = session.get(Config.unacs_graduation_photos_thumbnails_url)
        if file_names_server.status_code != 200:
            raise ConnectionError(f'Failed to fetch thumbnail urls with {file_names_server.status_code} status code')
        if file_names_server.json()['success'] is False:
            raise ConnectionError('Something goes wrong. Try Again...')

        file_name_list = file_names_server.json()['responseData']

        #  Delete already downloaded files from server response
        existing_files = {f.name for f in filepath.iterdir() if f.is_file()}
        file_names = [file for file in file_name_list if Path(file).name not in existing_files]

        if len(file_names) == 0:
            print('All photos have been downloaded!')
            return

        async def download_links(url: str, a_session, progress_bar, semaphore):
            async with semaphore:
                a_session.headers.update({'referer': '/mezuniyet-fotograf'})
                filename = url.split('/')[-1]

                response = await a_session.get(url)

                if response.status == 401:
                    async_tqdm.write('Session expired. Re-logging...')
                    session = cls.login()
                    a_session.headers.update(session.headers)

                    response = await a_session.get(url)

                if response.status == 429:
                    async_tqdm.write('Too many requests. Waiting for a while...')
                    await asyncio.sleep(random.uniform(4, 7))
                    response = await a_session.get(url)

                try:
                    if response.status == 200:
                        image_data = await response.read()

                        async with aiofiles.open(f'{filepath}/{filename}', 'wb') as file:
                            await file.write(image_data)

                        wait_time = random.uniform(1, 2)
                        info = f'Waiting for {wait_time:.2f} seconds before the next request...'
                        progress_bar.set_postfix(info=info)
                        progress_bar.update(1)
                        await asyncio.sleep(wait_time)
                    else:
                        async_tqdm.write(f'Failed to download image from {url} with status {response.status}')
                except Exception as e:
                    async_tqdm.write(f"Error fetching {url}: {e}")
   
        async def get_graduation_photos():
            semaphore = asyncio.Semaphore(8)
            async with aiohttp.ClientSession() as async_session:
                sync_sess_headers = session.headers
                async_session.headers.update(sync_sess_headers)
                tasks = []
                with async_tqdm(total=len(file_names)) as pbar:
                    for file_name in file_names:
                        url = f'{Config.unacs_graduation_photo_by_name_url}{file_name}'
                        task = asyncio.create_task(download_links(url, async_session, pbar, semaphore))
                        tasks.append(task)

                    await asyncio.gather(*tasks)

        asyncio.run(get_graduation_photos())

