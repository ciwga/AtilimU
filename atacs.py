from atilim_profile import atilim_kimlik
from atilim_curriculum import Curriculum
from bs4 import BeautifulSoup
import pandas as pd
import json
import os


class Atacs_Student:

    atacs_uri = f'https://atacs.{atilim_kimlik.domain}'

    def auth(self, uri=atacs_uri) -> atilim_kimlik.login:
        auth_uri = f'{uri}/Auth/AssertionConsumerService'
        session = atilim_kimlik().login()
        saml2 = session.get(uri)
        saml2Value = saml2.text[1098:13838]
        relaystate = saml2.text[13888:13901]

        payload = {
            'SAMLResponse': saml2Value,
            'RelayState': relaystate
        }
        session.post(auth_uri, data=payload)

        return session

    def report_open_courses(self, uri=atacs_uri) -> None:
        opc_uri = f'{uri}/DersAcmaReport'
        session = self.auth()

        session.headers.update({
            'Referer': opc_uri
        })

        tokenUri = session.get(opc_uri)
        soup = BeautifulSoup(tokenUri.content, 'html.parser')
        token = soup.find('input', attrs={'name': '__RequestVerificationToken'})

        select_term = soup.find('select', attrs={'id': 'DONEM_ID'})
        current_term = select_term.option['value']
        # soup2 = BeautifulSoup(str(select_term), 'html.parser')
        # option = soup2.find_all('option')
        # term_codes = [value['value'] for value in option]
        # term_names = [value.text for value in option]
        # terms_dict = {key: value for key, value in zip(term_codes, term_names)}

        payload = {
            '__RequestVerificationToken': token['value'],
            'DONEM_ID': current_term,
            'FAKULTE_ID': '-1',
            'BOLUM_ID': '-1',
            'DersAramaKey': None,
            'DERS_ID': '0',
            'DERS_ADI': '0'
        }

        print('Fetching the all opened lessons. It may take a while...')
        courses = session.post(opc_uri, data=payload)
        df = pd.read_html(courses.text)[1]
        df.to_csv('all_opened_courses.csv')
        print('Fetched all the lessons!')

    def opened_lessons_database(self, curriculum_uri=None) -> None:
        def compare_courses():
            df = pd.read_csv('all_opened_courses.csv')
            try:
                open_courses = df['Ders Kodu']
                sections = df['ŞUBE ADI']
                teachers = df['Öğretim Elemanları']
                quotas = df['Kayıtlı Öğrenci Sayısı/Şube Toplam Kontenjan']
            except KeyError:
                open_courses = df['Course Code']
                sections = df['SECTION NAME']
                teachers = df['Instructors']
                quotas = df['Number of Registered Students/Total Section Quota']

            if not os.path.isfile('curriculum_lessons_data.csv'):
                if curriculum_uri is None:
                    print('Curriculum data file is not found!')
                    w = str(input('Paste the curriculum webpage: '))
                    Curriculum(w).run_all()
                    print('Curriculum data file is created!')
            cur_data = pd.read_csv('curriculum_lessons_data.csv')

            area_courses = cur_data[cur_data['isAreaElective'] == bool(True)]
            selective_courses = cur_data[cur_data['isSelective'] == bool(True)]
            not_elective = cur_data[cur_data['isElective'] == bool(False)]
            temp = []
            print('Area Elective Courses as per your curriculum:')
            for course, section, teacher, quota in zip(open_courses, sections,
                                                       teachers, quotas):
                ldf = cur_data[cur_data['lesson_code'] == course]
                if course in set(area_courses['lesson_code']):
                    course_dict_a = {
                        'type': 'area_elective_course',
                        'id': ldf['lesson_id'].to_list()[0],
                        'department_id': ldf['department_id'].to_list()[0],
                        'lesson': course,
                        'section': section,
                        'teacher': teacher,
                        'quota': [quota]
                    }

                    print(course, section, teacher)
                    temp.append(course_dict_a)

                if course in set(selective_courses['lesson_code']):
                    course_dict_s = {
                        'type': 'selective_course',
                        'id': ldf['lesson_id'].to_list()[0],
                        'department_id': ldf['department_id'].to_list()[0],
                        'lesson': course,
                        'section': section,
                        'teacher': teacher,
                        'quota': [quota]
                    }
                    temp.append(course_dict_s)

                if course in set(not_elective['lesson_code']):
                    course_dict_o = {
                        'type': 'compulsory_course',
                        'id': ldf['lesson_id'].to_list()[0],
                        'department_id': ldf['department_id'].to_list()[0],
                        'lesson': course,
                        'section': section,
                        'teacher': teacher,
                        'quota': [quota]
                    }
                    temp.append(course_dict_o)

            with open('opened_curriculum_courses.json', 'w', encoding='utf-8') as aec:
                aec.write(json.dumps(temp, indent=4, ensure_ascii=False))

        if os.path.isfile('all_opened_courses.csv'):
            compare_courses()
        else:
            self.report_open_courses()
            compare_courses()

    def is_lesson_opened(self, *code: str) -> None:
        if not os.path.isfile('opened_curriculum_courses.json'):
            self.opened_lessons_database()
        with open('opened_curriculum_courses.json', 'r', encoding='utf-8') as f:
            reader = json.load(f)
            lessons = [lc['lesson'] for lc in reader]

        def check(*args):
            print('*'*50)
            for i in args[0]:
                if i in lessons:
                    print(f'{i} is opened')
        check(code)

    def received_messages(self, uri=atacs_uri) -> tuple:
        m_uri = f'{uri}/OgrenciMesaj/Ogrenci_Gelenkutusu'
        session = self.auth()
        session.headers.update({
            'Referer': uri
        })
        page = session.get(m_uri)
        soup = BeautifulSoup(page.content, 'html.parser')
        butt = soup.find_all('button', attrs={'class': 'btn btn-link'})
        onclick = (y['onclick'].split('/')[-1].replace("'", '') for y in butt)
        message_codes = [x for x in onclick if x.isnumeric()]
        p = pd.read_html(page.content)
        df = p[0]
        try:
            del df['SİL']
            del df['CEVAPLA']
        except KeyError:
            del df['DELETE']
            del df['REPLY']
        del df[df.columns[-1]]
        df.columns = ['name', 'surname', 'subject', 'date', 'id']
        df['id'] = pd.Series(message_codes)
        return df, session

    def save_all_messages(self, uri=atacs_uri) -> None:
        df, session = self.received_messages()

        payload = {
            'Tip': '1'
        }

        for ix in range(len(df['id'])):
            r_uri = f"{uri}/OgrenciMesaj/Ogrenci_MesajGoruntule/{df['id'][ix]}"
            h = session.get(r_uri, data=payload)
            soup = BeautifulSoup(h.content, 'html.parser')

            sender = soup.find('input', attrs={'id': 'Name'})['value']
            subject = soup.find('input', attrs={'id': 'Konu'})['value']
            message = soup.find('textarea', attrs={'id': 'Icerik'}).text
            with open('my_atacs_messages.html', 'a+', encoding='utf-8') as fh:
                fh.seek(0)
                if message.strip() not in fh.read():
                    fh.write(f'<p><b>From:</b> {sender}</p>\n')
                    fh.write(f'<p><b>Subject:</b> {subject} </p>\n')
                    fh.write(f"<p><b>Date:</b> {df['date'][ix]}</p>\n")
                    fh.write(f'<b>Message:</b> {message.strip()}\n')
                    fh.write(f"<p><b>{'*'*200}</b></p>\n")

    def get_financial_pay_table(self, uri=atacs_uri) -> None:
        pay_uri = f'{uri}/OgrenciFinans/Ogr_Bilgi_getir'
        session = self.auth()
        session.headers.update({
            'Referer': f'{uri}//OgrenciFinans'
        })
        payload = {
            'ogr_no': ''
        }
        fpage = session.post(pay_uri, data=payload)
        df = pd.read_html(fpage.text)[2]

        y = df[df.columns[-1]]
        y = y.str.replace('₺', '').str.strip().str.replace(',', '.')
        df[df.columns[-1]] = y
        df[df.columns[-1]] = df[df.columns[-1]].astype(float)
        df.to_csv('atilim_my_financial_pay_data.csv')
        collection = df[df[df.columns[-3]] == 'Tahsilat']
        total = collection[collection.columns[-1]].sum()
        print(f'Paid total money: {total}₺')

    def save_kvkk_form(self, uri=atacs_uri):
        kvkk_uri = f'{uri}/Kvkk/ReviewForm'
        session = self.auth()
        form = session.get(kvkk_uri)
        soup = BeautifulSoup(form.content, 'html.parser')
        texts = soup.find('div', attrs={'class': 'content'})
        with open('atilim_kvkk_form.html', 'w', encoding='utf-8') as kvkk:
            kvkk.write(str(texts))
