import sys
from art import tprint
from tools.atacs import Atacs
from tools.unacs import Unacs
from tools.moodle import Moodle
from tools.profile import Profile
from tools.helpers import clean_terminal


def return_menu():
    menu = 'Return to Menu (r): '
    q = input(menu)
    if q == 'r':
        clean_terminal()
        main()


def main():
    clean_terminal()
    tprint("ATILIM\nUNIVERSITY", font="small")

    print(
        ' 1. Save Your Information\n',
        '2. Save Your All Atacs Messages\n',
        '3. Save Your Announcements of Moodle Lessons\n',
        '4. Check the Opened Area Elective Courses\n',
        '5. Save Your Financial Pay Table\n',
        '6. Save Your KVKK Form\n',
        '7. Download Moodle Main Course Page Documents\n',
        '8. Download Graduation Photos\n',
        '9. Exit'
    )

    client_dict = {
        1: Profile.save_profile_data,
        2: Atacs.save_atacs_inbox_messages,
        3: Moodle().save_moodle_course_announcements,
        4: Unacs.get_opened_area_elective_courses,
        5: Atacs.fetch_atacs_financial_information,
        6: Atacs.save_kvkk_form,
        7: Moodle().download_moodle_course_files,
        8: Unacs.download_graduation_photos,
        9: sys.exit
    }

    query = int(input(r'Choose One (1/2/3/4/5/6/7/8/9): '))
    if query == 3:
        save_all = input('Do you want to save all course announcements? (y/n): ')
        if save_all.lower() == 'y':
            Moodle().save_moodle_course_announcements(save_all=True)
            return_menu()
        elif save_all.lower() == 'n':
            Moodle().save_moodle_course_announcements()
            return_menu()
        else:
            print('Wrong option!')
            return_menu()
    try:
        client_dict[query]()
    except KeyError:
        clean_terminal()
        main()
    return_menu()


if __name__ == '__main__':
    __version__ = '1.9'
    main()
