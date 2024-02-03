import csv

from bcnlibrarylookup.model import BookResult


def bookresults_by_author_to_books_csv(bookresults_by_author: dict[str, list[BookResult]], csv_path: str) -> None:
    with open(csv_path, 'w+') as csvfile:
        csv_writer = csv.writer(csvfile, quotechar='"')

        # Write each row from the list to the CSV file
        for author, book_results in bookresults_by_author.items():
            for book in book_results:
                row = [author, book.title, book.link]
                csv_writer.writerow(row)
def bookresults_by_author_to_author_csv(bookresults_by_author: dict[str, list[BookResult]], csv_path: str) -> None:
    with open(csv_path, 'w+') as csvfile:
        csv_writer = csv.writer(csvfile, quotechar='"')

        # Write each row from the list to the CSV file
        for author, book_results in bookresults_by_author.items():
            row = [author, len(book_results)]
            csv_writer.writerow(row)
