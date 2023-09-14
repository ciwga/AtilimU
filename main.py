import os
import sys
from atilim_profile import Atilim_Kimlik
from atacs import Atacs_Student
from moodle import Atilim_Moodle

def feedback():
    remenu = 'Return to Menu (r): '
    rq = input(remenu)
    if rq == 'r':
        if os.name == 'posix':
            os.system('clear')
        os.system('cls')
        menu()

def menu():
    print(
    """
    #################################################################################################################################
    #                                                                                                                               #
    #   ##    ######    ###   #        ###   #   #         #   #  #   #    ###   #   #  #####  #####   ####    ###   ######  #   #  #
    #  #  #      #       #    #         #    ## ##         #   #  ##  #     #    #   #  #      #   #  #         #       #     # #   #
    #  ####      #       #    #         #    # # #         #   #  # # #     #    #   #  #####  #####   ###      #       #      #    #
    # #    #     #       #    #         #    #   #         #   #  #  ##     #     # #   #      # #        #     #       #      #    #
    # #    #     #      ###   #####    ###   #   #          ###   #   #    ###     #    #####  #  ##  ####     ###      #      #    #
    #                                                                                                                               #
    #################################################################################################################################
    """, flush=True
    )

    print(
        " 1. Save Your Information\n",
        "2. Save Your All Atacs Messages\n",
        "3. Save Your Announcements of Moodle Lessons\n",
        "4. Check the Opened Elective Courses\n",
        "5. Check the Lesson is Opened or Not\n",
        "6. Save Your Financial Pay Table\n",
        "7. Save Your Term Notes\n",
        "8. Save Your KVKK Form\n",
        "9. Exit"
    )

    client_dict = {
        1: Atilim_Kimlik().save_profile_atilim,
        2: Atacs_Student().save_all_messages,
        3: Atilim_Moodle().save_ann_messages,
        4: Atacs_Student().opened_lessons_database,
        6: Atacs_Student().get_financial_pay_table,
        8: Atacs_Student().save_kvkk_form,
        9: sys.exit
    }
    
    query = int(input(r'Choose One (1/2/3/4/5/6/7/8/9): '))
    if query == 5:
        cc = input('Enter the course code(s): ')
        Atacs_Student().is_lesson_opened(cc)
        feedback()
    elif query == 7:
        tn = str(input('Enter Your Student Number: '))
        Atacs_Student().save_term_notes(tn)
        feedback()
    else:
        client_dict[query]()
        feedback()

menu()
