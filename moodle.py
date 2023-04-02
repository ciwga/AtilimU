from atilim_profile import atilim_kimlik
from datetime import datetime
from bs4 import BeautifulSoup
import json
import os


class Atilim_Moodle:

    def __init__(self):
        self.userid_container = []
        self.uri = f'https://moodle.{atilim_kimlik.domain}'

    def auth_moodle(self):
        loginP = f'{self.uri}/auth/saml2/sp/saml2-acs.php/moodle.atilim.edu.tr'
        resume = f'{atilim_kimlik.referer}/saml2/sso'
        session = atilim_kimlik().login()

        local_time = datetime.now()
        timestamp = datetime.timestamp(local_time) * 1000

        payload = {
            'spentityid': f'{self.uri}/auth/saml2/sp/metadata.php',
            'RelayState': f'{self.uri}/login/index.php',
            'cookieTime': timestamp
        }

        submit = session.post(resume, data=payload)
        soup = BeautifulSoup(submit.content, 'html.parser')
        samlR = soup.find('input', attrs={'name': 'SAMLResponse'})['value']
        relayS = soup.find('input', attrs={'name': 'RelayState'})['value']

        pay_login = {
            'SAMLResponse': samlR,
            'RelayState': relayS
        }

        mainP = session.post(loginP, data=pay_login)
        soup2 = BeautifulSoup(mainP.content, 'html.parser')
        href = soup2.find('a', attrs={'data-title': 'logout,moodle'})['href']
        sesskey = href.split('=')[1]

        div = soup2.find('div', attrs={'class': 'logininfo'}).a
        userid = div['href'].split('=')[1]
        self.userid_container.append(userid)

        return session, sesskey

    def taken_courses(self, user_id=None, check=False):
        service = f'{self.uri}/lib/ajax/service.php'
        session, sesskey = self.auth_moodle()

        if user_id is not None:
            userid = user_id
        userid = self.userid_container[0]

        params = {
            'sesskey': sesskey,
            'info': 'core_course_get_recent_courses',
        }

        payload = [{
                'index': '0',
                'methodname': 'core_course_get_recent_courses',
                'args': {
                    'userid': userid
                    }
                }
            ]

        my_courses = session.post(service, params=params, json=payload)
        jsonobject = json.loads(my_courses.content)
        with open(f'{userid}_courses.json', 'w', encoding='utf-8') as f:
            f.write(json.dumps(jsonobject, indent=4, ensure_ascii=False))
        print('Fetched your taken courses database!')
        if check:
            self.save_ann_messages()

    def retriever(self, data: list) -> tuple:
        store = {idx['fullname']: idx['viewurl'] for idx in data}
        indexed_store = {ix: name for ix, name in enumerate(store.keys(), 1)}
        store_shorts = {idx['fullname']: idx['shortname'] for idx in data}
        for i, j in indexed_store.items():
            print('*'*70)
            print(i, j)
        print('*'*70)

        while True:
            try:
                i_input = int(input('Enter the index number of the course: '))
                selected_link = [store[indexed_store[i_input]]]
                shortname = store_shorts[indexed_store[i_input]]
                break
            except KeyError:
                print('Out of index !!')

        if os.name == 'nt':
            os.system('cls')
        elif os.name == 'posix':
            os.system('clear')
        else:
            pass
        return selected_link, shortname

    def save_ann_messages(self, save_all=False):
        ''' Save all course announcements
            that you enrolled in'''
        session, sesskey = self.auth_moodle()

        jsonfile = f'{self.userid_container[0]}_courses.json'
        if os.path.exists(jsonfile):
            with open(jsonfile, 'r', encoding='utf-8') as j:
                jfile = json.loads(j.read())
                data = jfile[0]['data']
                if save_all:
                    urls = (idx['viewurl'] for idx in data)
                    filename = 'my_moodle_course_announcements.html'
                else:
                    urls, shortname = self.retriever(data)
                    filename = f"{urls[0].split('=')[1]}_{shortname}.html"
            count = 0
            with open(filename, 'w',
                      encoding='utf-8') as af:
                for url in urls:
                    page = session.get(url)
                    s = BeautifulSoup(page.content, 'html.parser')
                    try:
                        an = s.find('div', attrs={'class': 'activityinstance'})
                        ann_h = an.a['href']
                        if 'forum' in ann_h:
                            messages = session.get(ann_h)
                            s2 = BeautifulSoup(messages.content, 'html.parser')
                            forum = s2.find_all('a',
                                                attrs={'class':
                                                       'w-100 h-100 d-block'})
                            anns = (x['href'] for x in forum)
                            for ann in anns:
                                msg = session.get(ann)
                                s3 = BeautifulSoup(msg.content, 'html.parser')
                                d = s3.find('div',
                                            attrs={'class':
                                                   'd-flex flex-column w-100'})
                                af.write(str(d))
                                af.write('*'*85)
                                print(f'\r{count+1} announcement is saved',
                                      end='', flush=True)
                                count += 1
                    except AttributeError:
                        pass
            print('\nDone!')
        else:
            self.taken_courses(check=True)


if __name__ == '__main__':
    moodle = Atilim_Moodle()
    moodle.save_ann_messages()
