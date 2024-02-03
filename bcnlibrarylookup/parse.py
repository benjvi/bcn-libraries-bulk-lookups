from typing import Optional

from bcnlibrarylookup.model import BookResult

# gets canonical book link from the book's page
def get_canonical_link(soup) -> Optional[BookResult]:
    title_elem = soup.find('td', {'class': 'bibInfoData'})
    if title_elem:
        self_link_elem = soup.find('a', {'id': 'recordnum'})
        return BookResult(title_elem.text.strip(), self_link_elem['href'])
    else:
        print("Book title from single book result page format not found")
        return None
