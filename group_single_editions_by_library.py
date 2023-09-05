import csv
import requests
import json
from bs4 import BeautifulSoup
from dataclasses import dataclass,asdict
import re

SNAPSHOT_DIR="snapshot-2023-09-05"

@dataclass
class BookEdition:
    title: str
    link: str

books = []
with open(f'{SNAPSHOT_DIR}/single-edition-books-found.csv', 'r') as csvfile:
    csvreader = csv.reader(csvfile, quotechar='"')
    header = next(csvreader)  # Skip the header row


    # Find the indexes of the csv fields we want, based on header values
    title_index = header.index("Title") 
    link_index = header.index("Link")



    for row in csvreader:
        print(row)
        books.append(BookEdition(row[title_index], row[link_index]))

books_by_library = {}
# Lookup the librarys for each book, by scraping the book's link
i = 0
for book in books:
    i += 1
    if i > 100000:
        break
    print(f'Scraping Title: {book.title}, Link: {book.link}')

    # Canonical book page doesn't have a complete list of all copies, so we need to scrape the book copies listing page
    # The format of that URL is different biut we can build it from the canonical URL by extracting the book ID
    # The canonical URL is in the form: https://aladi.diba.cat/record=b1234567~S10*spi
    # The book copies listing URL is in the form: https://aladi.diba.cat/search~S10*spi?/.b1234567/.b1234567/1,1,1,B/holdings~1234567&FF=&1,0,
    book_id = re.search(r'record=b(\d+)~', book.link).group(1)
    all_holdings_page = f'https://aladi.diba.cat/search~S10*spi?/.b{book_id}/.b{book_id}/1,1,1,B/holdings~{book_id}&FF=&1,0'

    # Get the book copies listing page
    response = requests.get(all_holdings_page)


    # Check for a successful response
    if response.status_code == 200:
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all 'tr' elements with the class 'bibItemsEntry'
        rows = soup.find_all('tr', {'class': 'bibItemsEntry'})
        
        for row in rows:
            # Find the 'td' within the 'tr'
            td = row.find('td')
            
            # Find the 'a' (link) within the 'td', if it exists
            if td:
                link = td.find('a')
                
                # Extract the link text if the link exists and is in Barcelona
                if link and link.text.startswith('BCN'):
                    if link.text not in books_by_library:
                        books_by_library[link.text] = []
                    entry = asdict(book)
                    entry['num_copies_global'] = len(rows)

                    books_by_library[link.text].append(entry)

sorted_books_by_library = {k: v for k, v in sorted(books_by_library.items(), key=lambda item: len(item[1]), reverse=True)}

# Pretty print the results and write to JSON file
print(json.dumps(sorted_books_by_library, indent=4))
with open(f'{SNAPSHOT_DIR}/books_by_library.json', 'w') as outfile:
    json.dump(sorted_books_by_library, outfile, indent=4)


    