from pathlib import Path
from typing import NoReturn


class Config:
    domain: str = 'atilim.edu.tr'
    atilim_website: str = f'https://www.{domain}'

    #  Atılım University Identity Service
    kiyos_url: str = f'https://kimlik.{domain}'
    kiyos_auth_token_url: str = f'{kiyos_url}/resume'
    kiyos_login_url: str = f'{kiyos_url}/ui/login'

    #  Atılım University Student Profile
    profile_info_url: str = f'https://profil.{domain}'
    profile_saml2_redirect_url: str = f'{profile_info_url}/saml2/acs'
    profile_page_url: str = f'{profile_info_url}/profilim'

    #  Atılım Academic System (ATACS)
    atacs_url: str = f'https://atacs.{domain}'
    atacs_auth_url: str = f'{atacs_url}/Auth/AssertionConsumerService'
    atacs_inbox_url: str = f'{atacs_url}/OgrenciMesaj/Ogrenci_Gelenkutusu'
    atacs_inbox_msg_view_url: str = f'{atacs_url}/OgrenciMesaj/Ogrenci_MesajGoruntule'
    atacs_student_adress_url: str = f'{atacs_url}//OgrenciAdres'
    atacs_student_finance_url: str = f'{atacs_url}/OgrenciFinans'
    atacs_financial_table_url: str = f'{atacs_student_finance_url}/Ogr_Bilgi_getir'
    atacs_kvkk_form_url: str = f'{atacs_url}/Kvkk/ReviewForm'

    #  Moodle
    moodle_url: str = f'https://moodle.{domain}'
    moodle_login_url: str = f'{moodle_url}/login/index.php'
    moodle_saml_base_path: str = f'auth/saml2/sp'
    moodle_saml_acs_path: str = f'{moodle_saml_base_path}/saml2-acs.php'
    moodle_saml_metadata_path: str = f'{moodle_saml_base_path}/metadata.php'
    moodle_metadata_url: str = f'{moodle_url}/{moodle_saml_metadata_path}'
    moodle_auth_page_url: str = f'{moodle_url}/{moodle_saml_acs_path}/moodle.{domain}'
    moodle_sso_url: str = f'{kiyos_url}/saml2/sso'
    moodle_taken_courses_page_url: str = f'{moodle_url}/lib/ajax/service.php'

    #  University Academic System (UNACS)
    unacs_url: str = f'https://unacs.{domain}'
    unacs_api: str = f'https://unacs-api.{domain}/api'
    unacs_login_endpoint_url: str = f'{unacs_api}/Identity/Auth/Login'
    unacs_auth_url: str = f'{unacs_api}/Identity/Auth/AssertionConsumerService'
    unacs_login_url: str = f'{unacs_login_endpoint_url}?returnUrl={unacs_auth_url}'
    unacs_opened_courses_referer_url: str = f'{unacs_url}/acilan-dersler-report'
    unacs_opened_courses_url: str = f'{unacs_api}/AcilanDerslerRaporu/GetAcilanDerslerReport'
    unacs_term_courses_url: str = f'{unacs_api}/Common/Get2016AfterDonemList'
    unacs_graduation_photos_url: str = f'{unacs_api}/MezuniyetFotograf'
    unacs_check_graduation_student_url: str = f'{unacs_graduation_photos_url}/CheckOgrenciGoruntuleme'
    unacs_graduation_photos_thumbnails_url: str = f'{unacs_graduation_photos_url}/GetMezuniyetThumbnail?bucketPath=ogrenci'
    unacs_graduation_photo_by_name_url: str = f'{unacs_graduation_photos_url}/GetMezuniyetFotografByName?name='

    #  Web Config
    user_agent: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'

    #   Cookie Key Names
    kiyos_cookie_key: list = ['KimliqSID', 'KimliqAuthToken']
    profile_cookie_keys: list = ['KIMLIQ_PROFILE', 'KimliqAdmin', 'KimliqAuthToken']
    unacs_cookie_keys: list = ['.AspNetCore.saml2', 'KimliqAuthToken']
    atacs_cookie_keys: list = ['ASP.NET_SessionId', 'language', 'KimliqAuthToken', 'KimliqSID', '.ASPXAUTH', 'FedAuth',
                               'FedAuth1', '__RequestVerificationToken']
    moodle_cookie_keys: list = ['MoodleSession', 'MDL_SSP_SessID', 'KimliqAuthToken', 'KimliqSID', 'MDL_SSP_AuthToken',
                                'MOODLEID1_']

    #  < --- Assistant Functions --->
    @staticmethod
    def create_directory(path: Path) -> NoReturn:
        path.mkdir(exist_ok=True, parents=True)

    @staticmethod
    def create_subdirectory(base_path: Path, subdirectory_name: str) -> Path:
        try:
            subdirectory_path = base_path / subdirectory_name
            Config.create_directory(subdirectory_path)
            return subdirectory_path
        except Exception as e:
            print(f"Error creating directory {subdirectory_path}: {e}")

    #  < --- Base Paths --- >
    @staticmethod
    def get_calling_script_path() -> Path:
        return Path(__file__)

    @staticmethod
    def get_main_path() -> Path:
        return Config.get_calling_script_path().parent.parent

    @staticmethod
    def get_data_path() -> Path:
        return Config.create_subdirectory(Config.get_main_path(), 'atilim_data')

    #  < --- Credentials --- >
    @staticmethod
    def get_credentials_path() -> Path:
        return Config.create_subdirectory(Config.get_data_path(), 'credentials')

    @staticmethod
    def get_session_filepath() -> Path:
        return Config.get_credentials_path() / 'atilim-session-file'

    @staticmethod
    def get_auth_data_filepath() -> Path:
        return Config.get_credentials_path() / 'atilim-auth.ini'

    @staticmethod
    def get_cookie_filepath() -> Path:
        return Config.get_credentials_path() / 'atilim-cookies.json'

    #  < --- Curriculum --->
    @staticmethod
    def get_curriculum_path() -> Path:
        return Config.create_subdirectory(Config.get_data_path(), 'curriculum')

    @staticmethod
    def get_curriculum_filepath(department: str) -> Path:
        curriculum_filepath = Config.get_curriculum_path() / f'{department}_curriculum-data.csv'
        # with open(f'{Config.get_curriculum_path()}/{department}_log.txt', 'w', encoding='utf-8') as logfile:
        #     logfile.write(department)
        return curriculum_filepath

    #  < --- Atılım University Student Profile --->
    @staticmethod
    def get_student_profile_path() -> Path:
        return Config.create_subdirectory(Config.get_data_path(), 'university_profile')

    @staticmethod
    def get_student_profile_filepath(student_number: str) -> Path:
        return Config.get_student_profile_path() / f'profile-info_{student_number}.json'

    #  < --- ATACS --- >
    @staticmethod
    def get_atacs_path() -> Path:
        return Config.create_subdirectory(Config.get_data_path(), 'atacs')

    @staticmethod
    def get_atacs_inbox_messages_filepath() -> Path:
        return Config.get_atacs_path() / 'atacs-inbox_messages.html'

    @staticmethod
    def get_atacs_financial_table_filepath() -> Path:
        return Config.get_atacs_path() / 'student_financial-pay-table.csv'

    @staticmethod
    def get_atacs_kvkk_form_filepath() -> Path:
        return Config.get_atacs_path() / 'atilim_kvkk-form.html'

    @classmethod
    def get_atacs_inbox_message_view_link(cls, messages: 'pandas.DataFrame', msg_index: int) -> str:
        return f'{cls.atacs_inbox_msg_view_url}/{messages[msg_index]}'

    #  < --- MOODLE --- >
    @staticmethod
    def get_moodle_path() -> Path:
        return Config.create_subdirectory(Config.get_data_path(), 'moodle')

    @staticmethod
    def get_moodle_documents_path() -> Path:
        return Config.create_subdirectory(Config.get_moodle_path(), 'course_documents')

    @staticmethod
    def get_moodle_documents_folderpath(folder_name: str) -> Path:
        return Config.create_subdirectory(Config.get_moodle_documents_path(), folder_name)

    @staticmethod
    def get_moodle_taken_courses_filepath(user_id: str) -> Path:
        return Config.get_moodle_documents_path() / f'{user_id}_courses.json'

    @staticmethod
    def get_moodle_taken_all_course_announcements_filepath() -> Path:
        return Config.get_moodle_documents_path() / 'my_moodle_course_announcements.html'

    @staticmethod
    def get_moodle_course_announcement_filepath(course_id: str, course_shortname: str) -> Path:
        return Config.get_moodle_documents_folderpath(course_id) / f'{course_id}_{course_shortname}.html'

    #  < --- UNACS --- >
    @staticmethod
    def get_unacs_path() -> Path:
        return Config.create_subdirectory(Config.get_data_path(), 'unacs')

    @staticmethod
    def get_unacs_current_term_opened_courses_temporary_filepath(department: str, current_term: str) -> Path:
        return Config.get_unacs_path() / f'temp-{department}-opened-courses_{current_term}.json'

    @staticmethod
    def get_unacs_area_elective_opened_courses_csv_filepath(department: str, current_term: str) -> Path:
        return Config.get_unacs_path() / f'{department}-area_elective_opened_courses_{current_term}.csv'

    @staticmethod
    def get_unacs_area_elective_opened_courses_txt_filepath(department: str, current_term: str) -> Path:
        return Config.get_unacs_path() / f'{department}-area_elective_courses_{current_term}.txt'

    @staticmethod
    def get_unacs_graduation_photos_folderpath() -> Path:
        return Config.create_subdirectory(Config.get_unacs_path(), 'graduation_photos')
