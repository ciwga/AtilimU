from tools import *
from art import tprint
import os
import sys


def clean_terminal():
    if os.name == 'posix':
        os.system('clear')
    elif os.name == 'nt':
        os.system('cls')
    else:
        pass


def feedback():
    return_menu = 'Return to Menu (r): '
    q = input(return_menu)
    if q == 'r':
        clean_terminal()
        menu()


def menu():
    clean_terminal()
    tprint("ATILIM\nUNIVERSITY", font="small")

    print(
        " 1. Save Your Information\n",
        "2. Save Your All Atacs Messages\n",
        "3. Save Your Announcements of Moodle Lessons\n",
        "4. Check the Opened Area Elective Courses\n",
        "5. Save Your Financial Pay Table\n",
        "6. Save Your KVKK Form\n",
        "7. Download Moodle Main Course Page Documents\n",
        "8. Exit"
    )

    client_dict = {
        1: AtilimProfile().save_profile_data,
        2: Atacs().save_atacs_messages,
        3: AtilimMoodle().save_ann_messages,
        4: UniversityAcademicSystem().get_opened_area_elective_courses,
        5: Atacs().save_financial_pay_table,
        6: Atacs().save_kvkk_form,
        7: AtilimMoodle().download_files_from_course_page,
        8: sys.exit
    }

    query = int(input(r'Choose One (1/2/3/4/5/6/7/8): '))
    if query == 3:
        save_all = input("Do you want to save all course announcements? (y/n): ")
        if save_all.lower() == 'y':
            AtilimMoodle().save_ann_messages(save_all=True)
            feedback()
        elif save_all.lower() == 'n':
            AtilimMoodle().save_ann_messages()
            feedback()
        else:
            print("Wrong input!")
            feedback()

    client_dict[query]()
    feedback()


if __name__ == '__main__':
    menu()
