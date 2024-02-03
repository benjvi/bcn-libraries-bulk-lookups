import csv
import requests
import json
import re
from bs4 import BeautifulSoup
from dataclasses import dataclass,asdict
from bcnlibrarylookup.http import rate_limited_request
from bcnlibrarylookup.model import BookEdition
from bcnlibrarylookup.parse import get_canonical_link

SNAPSHOT_DIR="snapshot-2024-02-03"



books = []
with open(f'{SNAPSHOT_DIR}/author-search-books.csv', 'r') as csvfile:
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
    if i > 1000:
        break
    print(f'Scraping Title: {book.title}, Link: {book.link}')

    # Canonical book page doesn't have a complete list of all copies, so we need to scrape the book copies listing page
    # The format of that URL is different biut we can build it from the canonical URL by extracting the book ID
    # The canonical URL is in the form: https://aladi.diba.cat/record=b1234567~S10*spi
    # The book copies listing URL is in the form: https://aladi.diba.cat/search~S10*spi?/.b1234567/.b1234567/1,1,1,B/holdings~1234567&FF=&1,0,
    book_id_result = re.search(r'record=b(\d+)~', book.link)
    if not book_id_result:
        print(f"Found non-canonical link for book {book.title}, will lookup canonical url for link: \"{book.link}\"")
        response = rate_limited_request(book.link.strip())
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            book_result = get_canonical_link(soup)
            book_id_result = re.search(r'record=b(\d+)~', book_result.link.strip())

        else:
            print(f"ERROR: couldn't get canonical link for book {book.title}")
            continue
    book_id = book_id_result.group(1)
    print(f"Found book_id {book_id}, proceeding to lookup copies available")
    all_holdings_page = f'https://aladi.diba.cat/search~S10*spi?/.b{book_id}/.b{book_id}/1,1,1,B/holdings~{book_id}&FF=&1,0'

    # Get the book copies listing page
    response = rate_limited_request(all_holdings_page)

    # Check for a successful response
    if response.status_code == 200:
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all 'tr' elements with the class 'bibItemsEntry'
        rows = soup.find_all('tr', {'class': 'bibItemsEntry'})
        
        for row in rows:
            # Find the 'td' within the 'tr'
            tds = row.find_all('td')
            
            
            # Find the 'a' (link) within the 'td', if it exists
            if tds[0]:
                library_td = tds[0]
                link = library_td.find('a')
                
                # Extract the link text if the link exists and is in Barcelona
                if link and link.text.startswith('BCN'):
                    if link.text not in books_by_library:
                        books_by_library[link.text] = []

                    # TODO: extract link and save in a list of libraries

                    # Need to convert dataclass to dict for json serialization
                    # We also take this as a chance to enrich the data
                    book_copy = asdict(book)
                    book_copy['num_copies_global'] = len(rows)
                    
                    # If library is found, we can also look for the state of the copy
                    if tds[2]:
                        state_td = tds[2]
                        state = state_td.text.strip()
                        book_copy['state'] = state
                    
                    books_by_library[link.text].append(book_copy)
                    
                    

count_num_avaialble_copies = lambda item: len([book_copy for book_copy in item[1] if book_copy['state'] == "Disponible"])
sorted_books_by_library = {k: v for k, v in sorted(books_by_library.items(), key=count_num_avaialble_copies, reverse=True)}

# Pretty print the results and write to JSON file
print(json.dumps(sorted_books_by_library, indent=4))
with open(f'{SNAPSHOT_DIR}/books_by_library.json', 'w') as outfile:
    json.dump(sorted_books_by_library, outfile, indent=4)


    
