import csv
from bs4 import BeautifulSoup
import requests
import time
import urllib.parse
import sys


authors = {}
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

            # to get the most possible results, we will use a simplified author name, removing any middle names
            author = row[author_index]
            name_array = author.split(' ')
            if len(name_array) > 2:
                author = name_array[0] + ' ' + name_array[-1]
                print(f'Original Author Name: {row[author_index]}, Simplified Name: {author}, Book: {row[title_index]}')
            else:
                print(f'Author: {author}, Book: {row[title_index]}')

            if author in authors:
                authors[author].append(row[title_index])
            else:
                authors[author] = [row[title_index]]


i = 0
for author,titles in authors.items():
    i += 1
    if i < 100:
        # url-safe encoding for author in query string
        author_escaped = urllib.parse.quote(author)

        print(f'Scraping with Author query: {author_escaped}')

        # Call library catalog search, by building URL
        # searchscope=10 is the code for all libraries in Barcelona
        retries = 1
        success = False
        response = None
        while not success:
            try:
                response = requests.get(f'https://aladi.diba.cat/search~S1*spi/X?SEARCH=a:({author_escaped})&searchscope=10&SORT=AX')
                success = True
            except Exception as e:
                wait = retries * 10;
                print(f'Error! Waiting {wait} secs and re-trying...')
                sys.stdout.flush()
                time.sleep(wait)
                retries += 1
        
        
        # site is using rate-limiting, so we wait 1 second between requests
        time.sleep(1)

        # Parse the HTML response
        # Check for a successful response
        if response.status_code == 200:
            empty_results = False

            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the specific div by its class
            target_div = soup.find('div', {'class': 'pageContentColumn'})
            
            # Check if the div exists
            if target_div:
                 # Find all 'h2' elements directly underneath the target div
                h2_elements = target_div.find_all_next('h2', limit=2)  # Limit to 2 to find just the first two
                
                # Check if at least two 'h2' elements are found
                if len(h2_elements) >= 2:
                    # Extract the text from the second 'h2' element
                    second_h2_text = h2_elements[1].text.strip()
                    
                    # Check for the particular string indicating empty results
                    # NB that if this element doesn't exist, we assume we have  results
                    if second_h2_text == 'NO HAY RESULTADOS':
                        empty_results = True
                        print(f'Results are empty for author "{author}"')
                    
            if not empty_results:
                print(f'Found results at URL: {response.url} for titles: {titles}')
                
        else:
            print(f'Failed to fetch the page for author. HTTP Status Code: {response.status_code}')
        