import csv
import os

HMSET_COMMAND = 'HMSET {key} book_id "{bookID}" title "{title}" authors "{authors}" average_rating "{average_rating}" isbn "{isbn}" language_code "{language_code}" num_pages "{num_pages}" \n'

def main():
    authors = {}

    with open('commands.redis', 'w') as commands_file:
        with open(os.path.join('data', 'books.csv')) as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                key = f"ru203:book:{row['bookID']}"
                title = row.pop('title').replace('"', '\\"').replace("'", "\\'")
                authors = row.pop('authors').replace('"', '\\"').replace("'", "\\'")
                commands_file.write(HMSET_COMMAND.format(key=key, authors=authors, title=title, **row))


if __name__ == "__main__":
    main()
