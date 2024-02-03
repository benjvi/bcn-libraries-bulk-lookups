import csv

from bcnlibrarylookup.http import rate_limited_request
from bcnlibrarylookup.model import Book, BookResult
from bcnlibrarylookup.parse import get_canonical_link
from bs4 import BeautifulSoup

import urllib.parse
import pprint


def get_books_by_author_from_goodreads_export() -> dict[str, list[Book]]:
    books_by_author = {}
    with open('goodreads_library_export.csv', 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        header = next(csvreader)  # Skip the header row

        # Find the indexes of the csv fields we want, based on header values
        title_index = header.index("Title")
        author_index = header.index("Author")
        shelf_index = header.index("Exclusive Shelf")

        i = 0
        max_authors = 1000
        for row in csvreader:
            if row[shelf_index] == 'to-read' and i < max_authors:
                i += 1

                title = row[title_index]
                author = row[author_index]

                # to get the most possible results, we will use a simplified author name, removing any middle names
                author_full = None
                name_array = author.split(' ')
                if len(name_array) > 2:
                    simplified_author = name_array[0] + ' ' + name_array[-1]
                    author_full = author
                    print(f'Original Author Name: {author_full}, Simplified Name: {simplified_author}, Book: {title}')
                else:
                    simplified_author = author
                    print(f'Author: {author}, Book: {title}')

                book = Book(title, author_full, simplified_author, 'to-read')
                if author in books_by_author:
                    books_by_author[author].append(book)
                else:
                    books_by_author[author] = [book]

    return books_by_author


def search_authors_in_bcn_libraries(books_by_author: dict[str, list[Book]], max_searches: int = 200) -> dict[str, list[BookResult]]:
    i = 0
    bookresults_by_author = {}
    for author,books in books_by_author.items():
        i += 1
        if i < max_searches:
            # url-safe encoding for author in query string
            author_escaped = urllib.parse.quote(author)

            print(f'Scraping with Author query: {author_escaped}')

            response = rate_limited_request(f'https://aladi.diba.cat/search~S1*spi/X?SEARCH=a:({author_escaped})&searchscope=10&SORT=AX')

            # Parse the HTML response
            # Check for a successful response
            if response.status_code == 200:
                empty_results = False

                # Parse the HTML content
                soup = BeautifulSoup(response.text, 'html.parser')

                # Find the specific div by its class
                target_div = soup.find('div', {'class': 'pageContentColumn'})

                # Check if the div exists
                author_bookresults = []
                if target_div:
                     # Find all 'h2' elements directly underneath the target div
                    h2_elements = target_div.find_all_next('h2', limit=2)  # Limit to 2 to find just the first two

                    # Check if at least two 'h2' elements are found
                    if len(h2_elements) >= 2:
                        # Extract the text from the second 'h2' element
                        second_h2_text = h2_elements[1].text.strip()

                        # Check for the particular string indicating empty results
                        # NB that if this element doesn't exist, we assume we have results
                        if second_h2_text == 'NO HAY RESULTADOS':
                            empty_results = True
                            print(f'Results are empty for author "{author}"')
                        else:
                            print('ERROR: Found search summary in unexpected format')
                    else:
                        print("Didn't find two h2 elements, containing search summary, usually means search succeeded so we'll look at results")
                        # TODO:
                        book_divs = soup.find_all('div', {'class': 'descript'})
                        print(f'Found {len(book_divs)} book sections in results page')
                        for div in book_divs:
                            book_link = div.find('span', {'class': 'titular'}) \
                                .find('a')  # book is the first link
                            if not book_link:
                                print(f'ERROR: link not found in book_div')
                            else:
                                # not empty, so get list of books in page
                                # TODO: need to paginate to get all author books
                                author_bookresults.append(BookResult(book_link.text, book_link['href']))

                        if len(book_divs) == 0:
                            # if only one book is found, the book page is returned directly, so check for book page title item
                            book_result = get_canonical_link(soup)
                            if book_result:
                                author_bookresults.append(book_result)

                else:
                    print('target div with context is not found')

                if not empty_results:
                    print(f'Found results at URL: {response.url} for author: {author}: {[b.title for b in author_bookresults]}')
                    bookresults_by_author[author] = author_bookresults

            else:
                print(f'Failed to fetch the page for author. HTTP Status Code: {response.status_code}')

    return bookresults_by_author



if __name__ == '__main__':
    books_by_author = get_books_by_author_from_goodreads_export()
    bookresults_by_author = search_authors_in_bcn_libraries(books_by_author)
    pprint.pprint(bookresults_by_author)
    # files will only show results from the case when author has multiple results in the library catalog
    bookresults_by_author_to_books_csv(bookresults_by_author, 'book_search_results_by_author.csv')
    bookresults_by_author_to_author_csv(bookresults_by_author, 'author_search_results_info.csv')
