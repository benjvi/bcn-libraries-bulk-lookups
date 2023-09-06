import json
import html
import os

EXTRACT_DATE="2023-09-05"
SNAPSHOT_DIR=f'snapshot-{EXTRACT_DATE}'
NOTES_DIR="notes"

# create one Markdown note with each of the libraries on a separate line, and a link to the library's website

# read the books json file
books_by_library = {}
with open(f'{SNAPSHOT_DIR}/books_by_library.json') as json_file:
    books_by_library = json.load(json_file)


libraries_note = """---
tags:
- autogenerated
---

"""
for library_name, books in books_by_library.items():

    # convert escaped unicode codes to characters
    unicode_library_name = html.unescape(library_name)

    num_book_copies = len(books)
    num_available_book_copies = len([book for book in books if book['state'] == "Disponible"])

    libraries_note += f'**{library_name}** - total copies: {num_book_copies}, available: {num_available_book_copies}'

    # create library-specific notes with links to books
    # only include libraries with many available books or in whitelist
    whitelist = ["Poblenou", "Gabriel García Márquez", "El Clot", "Francesca Bonnemaison", "Barceloneta La Fraternitat"]
    if num_available_book_copies > 6 or any(item in unicode_library_name for item in whitelist):
        print("Creating note for library: " + unicode_library_name)
        library_note_title = f'Book Availability In {unicode_library_name} {EXTRACT_DATE}'

        library_note = """---
tags:
- autogenerated
---

"""

        for book in books:
            # convert escaped unicode codes to characters
            unicode_book_title = html.unescape(book['title'])

            library_note += f'[**{unicode_book_title}**]({book["link"]}) {book["state"]} ({book["num_copies_global"]} global copies)\n\n'

            with open(f'{SNAPSHOT_DIR}/{NOTES_DIR}/{library_note_title}.md', 'w') as outfile:
                outfile.write(library_note)

        # also add link to note in main libraries note
        libraries_note += f' - see [[{library_note_title}]]\n\n'
    else:
        libraries_note += "\n\n"



# make sure notes directory exists, and if not create it (NB snapshot dir has to exist)
if not os.path.exists(f'{SNAPSHOT_DIR}/{NOTES_DIR}'):
    os.makedirs(f'{SNAPSHOT_DIR}/{NOTES_DIR}')

with open(f'{SNAPSHOT_DIR}/{NOTES_DIR}/BCN Libraries Book Availability {EXTRACT_DATE}.md', 'w') as outfile:
    outfile.write(libraries_note)
