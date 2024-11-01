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


def file_format(file_signature: bytes):
    signatures = {
        b'\x25\x50\x44\x46': '.pdf',
        b'\x42\x4D': '.bmp',
        b'\x42\x5A\x68': '.bz2',
        b'\x4D\x5A': '.exe',
        b'\x47\x49\x46\x38': '.gif',
        b'\xFF\xD8\xFF': '.jpg',
        b'\x7B\x0A': '.json',
        b'\x89\x50\x4E\x47': '.png',
        b'\x4D\x4D\x00': '.tiff',
        b'\x52\x61\x72\x21': '.rar',
        b'\x75\x73\x74\x61': '.tar',
        b'\x37\x7A\xBC\xAF': '.7z',
        b'\x1F\x8B': '.gz',
        b'\xFD\x37\x7A\x58': '.xz',
        b'\x04\x22\x4D\x18': '.lz4',
        b'\x4C\x5A\x49\x50': '.lz',
        b'\x4D\x53\x43\x46': '.cab',
        b'\x7B\x5C\x72\x74': '.rtf',
    }
    for signature, extension in signatures.items():
        if file_signature.startswith(signature):
            return extension
    return None


def select_from_response_data(response: list, term_name_key: str, term_id_key: str):
    selection_dict = {term[term_name_key]: term[term_id_key] for term in response}
    
    for index, term_name in enumerate(selection_dict.keys()):
        print(f'{index}: {term_name}')

    while True:
        try:
            choice = int(input('Enter your choice number: '))
            if 0 <= choice < len(selection_dict):
                return str(list(selection_dict.keys())[choice]), int(list(selection_dict.values())[choice])
            else:
                print('Invalid selection! Please try again.')
        except ValueError:
            print('Invalid input! Please enter a number.')