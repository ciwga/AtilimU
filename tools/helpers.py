import re
import os


def clean_filename(filename):
    invalid_chars = r'[<>:"/\\|?*]'
    cleaned_filename = re.sub(invalid_chars, '_', filename)
    cleaned_filename = re.sub(r'\s+', '_', cleaned_filename)
    cleaned_filename = cleaned_filename.strip('_')
    return cleaned_filename


def clean_terminal():
    if os.name == 'nt':
        os.system('cls')
    elif os.name == 'posix':
        os.system('clear')
    else:
        pass


def user_interactions() -> int:
    while True:
        print()
        request_response = str(input('Yes or No (Y/N): ')).lower()
        possible_positive_answers = ['yes', 'y']
        possible_negative_answers = ['no', 'n']
        if (request_response in possible_positive_answers) or (request_response in possible_negative_answers):
            if request_response in possible_positive_answers:
                return 0
            else:
                return 1
        else:
            print('Wrong option, try again...')
