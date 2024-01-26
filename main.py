from tools import *
from art import tprint
import os
import sys


def feedback():
    return_menu = 'Return to Menu (r): '
    q = input(return_menu)
    if q == 'r':
        if os.name == 'posix':
            os.system('clear')
        os.system('cls')
        menu()


def menu():
    tprint("ATILIM\nUNIVERSITY", font="small")

    print(
        " 1. Save Your Information\n",
        "2. Save Your All Atacs Messages\n",
        "3. Save Your Announcements of Moodle Lessons\n",
        "4. Check the Opened Area Elective Courses\n",
        "5. Save Your Financial Pay Table\n",
        "6. Save Your KVKK Form\n",
        "7. Exit"
    )

    client_dict = {
        1: AtilimProfile().save_profile_data,
        2: Atacs().save_atacs_messages,
        3: AtilimMoodle().save_ann_messages,
        4: UniversityAcademicSystem().get_opened_area_elective_courses,
        5: Atacs().save_financial_pay_table,
        6: Atacs().save_kvkk_form,
        7: sys.exit
    }

    query = int(input(r'Choose One (1/2/3/4/5/6/7): '))
    client_dict[query]()
    feedback()


if __name__ == '__main__':
    menu()
