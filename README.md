# ATILIM UNIVERSITY STUDENT SYSTEM

## Features

1. Save your personal information.
2. Save all ATACS messages.
3. Save announcements from Moodle lessons.
4. Check opened area elective courses.
5. Save your financial pay table.
6. Save your KVKK form.
7. Download Moodle main course page documents.
8. Download graduation photos.

## Installation

To use this tool, clone the repository and install the required dependencies:

```bash
git clone https://github.com/ciwga/AtilimU.git
cd AtilimU
pip install -r requirements.txt
```

## Usage

Run the main program using:

```bash
python main.py
```

### Descriptions of Operations

<details>
<summary>1. Save your personal information</summary>

This option saves your personal information, such as your name, surname, student number, and department, to a file.
Saves in `atilim_data/university_profile` directory.

</details>

<details>
<summary>2. Save all ATACS messages</summary>

This option saves all of your Atacs messages to a file.
Saves in `atilim_data/atacs` directory.

</details>

<details>
<summary>3. Save announcements from Moodle lessons</summary>

This option saves all of the announcements for your Moodle lessons to a file.
Saves in `atilim_data/moodle` directory.

</details>

<details>
<summary>4. Check opened area elective courses</summary>

This option checks and saves the opened area elective courses.
Saves in `atilim_data/unacs` directory.

</details>

<details>
<summary>5. Save your financial pay table</summary>

This option saves your financial pay table to a file. The option also prints the total amount of money you have paid to date.
Saves in `atilim_data/atacs` directory.

</details>

<details>
<summary>6. Save your KVKK form</summary>

This option saves your KVKK form to a file.
Saves in `atilim_data/atacs` directory.

</details>

<details>
<summary>7. Download Moodle main course page documents</summary>

This option downloads course documents from the Moodle course main page.
Supported file formats include pdf, xlsx, docx, txt, pptx, zip, and html.
Saves in `atilim_data/moodle` directory.

</details>

<details>
<summary>8. Download graduation photos</summary>

This option downloads graduation photos if you have already participated in the ceremony.
Saves in `atilim_data/unacs/graduation_photos` directory.

</details>


## Version History

### Version 1.8

- Fixed login errors.
- Added cookie management for improved session handling.
- Refactored code for a more modular structure.
