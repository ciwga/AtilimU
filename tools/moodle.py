import re
import time
import json
import random
from tqdm import tqdm
from bs4 import BeautifulSoup
from datetime import datetime
from tools.config import Config
from tools.kiyos_auth import AtilimAuth
from typing import Tuple, NoReturn
from tools.helpers import clean_filename, clean_terminal, user_interactions, file_format


class Moodle:
    userid_container = []
    file_dict = {}

    @staticmethod
    def login():
        session = AtilimAuth().login()
        is_loaded = AtilimAuth().load_cookies(session, Config.moodle_cookie_keys, 'moodle')

        if is_loaded:
            return Moodle._process_login(session, loaded=True)

        local_time = datetime.now()
        timestamp = datetime.timestamp(local_time) * 1000
        payload = {
            'spentityid': Config.moodle_metadata_url,
            'RelayState': Config.moodle_login_url,
            'cookieTime': timestamp
        }
        saml_submit_btn = session.post(Config.moodle_sso_url, data=payload)
        soup = BeautifulSoup(saml_submit_btn.content, 'html.parser')
        saml_value = soup.find('input', attrs={'name': 'SAMLResponse'})['value']
        relay_state_value = soup.find('input', attrs={'name': 'RelayState'})['value']
        assertion_payload = {'SAMLResponse': saml_value, 'RelayState': relay_state_value}
        moodle_page = session.post(Config.moodle_auth_page_url, data=assertion_payload)

        return Moodle._process_login(session, moodle_page)

    @staticmethod
    def _process_login(session, moodle_page=None, loaded=None) -> Tuple:
        if moodle_page is None:
            moodle_page = session.get(Config.moodle_url)

        moodle_page_tree = BeautifulSoup(moodle_page.content, 'html.parser')
        target_sesskey_url = moodle_page_tree.find('a', attrs={'data-title': 'logout,moodle'})['href']
        sesskey = str(target_sesskey_url.split('=')[1])
        login_info = moodle_page_tree.find('div', attrs={'class': 'logininfo'}).a
        userid = login_info['href'].split('=')[1]
        Moodle.userid_container.append(userid)

        if not loaded:
            AtilimAuth().save_cookies(session, Config.moodle_cookie_keys, 'moodle')

        return session, sesskey

    def organize_files(self, file_ext: str, filename: str, file_url: str) -> NoReturn:
        if file_ext in self.file_dict:
            self.file_dict[file_ext].append({
                'filename': filename,
                'file_url': file_url
            })
        else:
            self.file_dict[file_ext] = [{
                'filename': filename,
                'file_url': file_url
            }]

    def download_moodle_course_files(self) -> NoReturn:
        self.file_dict.clear()
        course_url = str(input('Enter the moodle course url: '))
        course_name = str(course_url.split('=')[-1])

        session, _ = self.login()
        course_webpage = session.get(course_url)
        if course_webpage.status_code != 200:
            raise ConnectionError(f'Failed connection to {course_url}\nStatus {course_webpage.status_code} code')

        course_webpage_tree = BeautifulSoup(course_webpage.content, 'html.parser')
        activity_elements = course_webpage_tree.find_all('div', attrs={'class': 'activityinstance'})
        for element in activity_elements:
            img_tag = element.find('img')
            try:
                img_tag_name = element.find('span', attrs={'class': 'instancename'})
                filename = img_tag_name.text.strip()
                filetypes = {
                    'spreadsheet': '.xlsx',
                    'document': '.docx',
                    'powerpoint': '.pptx',
                    'text': '.txt',
                    'archive': '.zip',
                    'html': '.html'
                }
                file_url = element.find('a')['href']
                file_response = session.get(file_url)
                file_sign_header = file_response.content[:4]
                file_extension = file_format(file_sign_header)
                if file_extension:
                    self.organize_files(file_extension, filename, file_url)
                else:
                    filetype_icon_url = img_tag['src']
                    for key, extension in filetypes.items():
                        if key in filetype_icon_url:
                            self.organize_files(extension, filename, file_url)
                            break
            except Exception as e:
                tqdm.write(f"Error processing element: {e}")

        course_folder = Config.get_moodle_documents_folderpath(course_name)
        for extension, files in self.file_dict.items():
            with tqdm(total=len(files), desc=f'{extension.capitalize()} files downloading') as pbar:
                for index in range(len(files)):
                    cleaned_filename = clean_filename(f'{files[index]['filename']}{extension}')
                    filepath = course_folder / cleaned_filename
                    file_request = session.get(files[index]['file_url'])
                    if file_request.status_code == 200:
                        with filepath.open(mode='wb') as f:
                            f.write(file_request.content)
                        pbar.set_description(f'Downloading: {cleaned_filename}')
                        pbar.update(1)
                    else:
                        tqdm.write(f'Download Failed: {filepath.name} with status {file_request.status_code}')

                    wait_time = random.uniform(1.0, 2.5)
                    info = f'Waiting for {wait_time:.2f} seconds before the next request...'
                    pbar.set_postfix(info=info)
                    time.sleep(wait_time)

    def moodle_taken_courses(self, session, sesskey) -> NoReturn:
        params = {
            'sesskey': sesskey,
            'info': 'core_course_get_recent_courses',
        }

        payload = [
            {
                'index': '0',
                'methodname': 'core_course_get_recent_courses',
                'args': {'userid': self.userid_container[0]},
            }
        ]

        my_courses = session.post(Config.moodle_taken_courses_page_url, params=params, json=payload)
        jsonobject = json.loads(my_courses.content)
        with Config.get_moodle_taken_courses_filepath(self.userid_container[0]).open(mode='w',
                                                                                     encoding='utf-8') as jsonfile:
            jsonfile.write(json.dumps(jsonobject, indent=4, ensure_ascii=False))
        print('Fetched your taken moodle courses database!')
        self.save_moodle_course_announcements()

    @staticmethod
    def get_course_information(course_data: list) -> Tuple:
        store = {idx['fullname']: idx['viewurl'] for idx in course_data}
        indexed_store = {ix: name for ix, name in enumerate(store.keys(), 1)}
        store_shorts = {idx['fullname']: idx['shortname'] for idx in course_data}
        for i, j in indexed_store.items():
            print('*' * 70)
            print(i, j)
        print('*' * 70)

        while True:
            try:
                i_input = int(input('Enter the index number of the course: '))
                selected_link = [store[indexed_store[i_input]]]
                shortname = store_shorts[indexed_store[i_input]]
                break
            except KeyError:
                print('Out of index !!')

        clean_terminal()
        return selected_link, shortname

    def save_moodle_course_announcements(self, save_all: bool = False) -> NoReturn:
        session, sesskey = self.login()
        jsonfile = Config.get_moodle_taken_courses_filepath(self.userid_container[0])
        if jsonfile.exists():
            print(f'\nCourse database file found at {jsonfile}. Do you want to update it?')
            action = user_interactions()
            if action == 0:
                self.moodle_taken_courses(session, sesskey)
            else:
                with jsonfile.open(mode='r', encoding='utf-8') as file:
                    jfile = json.loads(file.read())
                    course_data = jfile[0]['data']
                    if save_all:
                        urls = [course_url['viewurl'] for course_url in course_data]
                        filename = Config.get_moodle_taken_all_course_announcements_filepath()
                    else:
                        urls, course_shortname = Moodle.get_course_information(course_data)
                        course_id = urls[0].split('=')[1]
                        filename = Config.get_moodle_course_announcement_filepath(course_id, course_shortname)
                with filename.open(mode='w', encoding='utf-8') as ann_file:
                    for url in urls:
                        ann_page = session.get(url)
                        ann_page_tree = BeautifulSoup(ann_page.content, 'html.parser')

                        wait_time = random.uniform(1.0, 2)
                        # info = f'Waiting for {wait_time:.2f} seconds before the next request...'
                        # tqdm.write(info)
                        time.sleep(wait_time)

                        try:
                            ann_links = ann_page_tree.find_all('a', attrs={'class': 'aalink'})
                            forum_url = r'https://moodle.atilim.edu.tr/mod/forum/view.php\?id='
                            for ann_link in ann_links:
                                regex = re.search(fr'{forum_url}(\d+)', str(ann_link))
                                if regex:
                                    ann_h = regex.group(0)
                                    ann_messages = session.get(ann_h)
                                    ann_messages_tree = BeautifulSoup(ann_messages.content, 'html.parser')
                                    forum = ann_messages_tree.find_all('a', attrs={'class': 'w-100 h-100 d-block'})
                                    announcement_urls = [announcement['href'] for announcement in forum]
                                    pbar = tqdm(announcement_urls, desc='Announcements')

                                    wait_time = random.uniform(1.0, 2.4)
                                    # info = f'Waiting for {wait_time:.2f} seconds before the next request...'
                                    # tqdm.write(info)
                                    time.sleep(wait_time)

                                    for ann_url in pbar:
                                        msg = session.get(ann_url)
                                        msg_tree = BeautifulSoup(msg.content, 'html.parser')
                                        msg_content = msg_tree.find('div', attrs={'class': 'd-flex flex-column w-100'})
                                        ann_file.write(str(msg_content))
                                        ann_file.write('*' * 85)

                                        wait_time = random.uniform(1.0, 2.5)
                                        info = f'Waiting for {wait_time:.2f} seconds before the next request...'
                                        pbar.set_postfix(info=info)
                                        time.sleep(wait_time)

                        except AttributeError:
                            pass
        else:
            self.moodle_taken_courses(session, sesskey)
