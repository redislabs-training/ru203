import csv
import re
import os
import random
from datetime import datetime, timedelta, timezone

AUTHOR_HMSET_COMMAND = 'HMSET {key} name "{name}" author_id "{author_id}"'
USER_HMSET_COMMAND = 'HMSET {key} first_name "{first_name}" last_name "{last_name}" email "{email}" escaped_email "{escaped_email}" user_id "{user_id}" last_login "{last_login}"'
CHECKOUT_HMSET_COMMAND = "HMSET {key} user_id {user_id} book_isbn {book_isbn} checkout_date {checkout_date} checkout_length_days {checkout_length_days} geopoint {geopoint}"
BOOK_HMSET_COMMAND = 'HMSET {key} isbn "{isbn}" title "{title}" thumbnail "{thumbnail}" description "{description}" categories "{categories}" authors "{authors}" author_ids "{author_ids}"'
AUTHORS_BOOKS_HMSET_COMMAND = 'HMSET {key} book_isbn {book_isbn} author_id {author_id}'

PREFIX = "ru203"

NEW_YORK = "-73.9{},40.7{}"

PUNCTUATION = re.compile(r"([,.<>{}\[\]\"':;!@#$%^&*()-+=~])")
JANUARY_1 = datetime(year=2021, month=1, day=1, hour=0, minute=0, second=0,
                     tzinfo=timezone.utc)


def escape_quotes(string):
    return string.replace('"', '\\"').replace("'", "\\'")


def escape_punctuation(string):
    return PUNCTUATION.sub(r'\\\\\1', string)


def random_coordinate():
    return NEW_YORK.format(random.randint(10000, 90000), random.randint(10000, 90000))


class Keys:
    def __init__(self, prefix):
        self.prefix = prefix

    def book(self, book_isbn):
        return f"{self.prefix}:book:details:{book_isbn}"

    def author(self, author_id):
        return f"{self.prefix}:author:details:{author_id}"

    def author_books(self, author_id, book_isbn):
        return f"{self.prefix}:author:books:{author_id}-{book_isbn}"

    def user(self, user_id):
        return f"{self.prefix}:user:details:{user_id}"

    def checkout(self, user_id, book_isbn):
        return f"{self.prefix}:book:checkout:{user_id}-{book_isbn}"


class DataGenerator:
    def __init__(self):
        self.commands = []
        self.authors = {}
        self.categories = {}
        self.users = {}
        self.book_isbns = []
        self.keys = Keys(prefix=PREFIX)

    def add_author(self, book, author):
        author_id = self.authors.get(author)
        new_author = False

        if not author_id:
            new_author = True
            author_id = len(self.authors) + 1
            self.authors[author] = author_id

        author_key = self.keys.author(author_id)
        if new_author:
            self.commands += [
                AUTHOR_HMSET_COMMAND.format(key=author_key, author_id=author_id, name=author)
            ]

        author_books_key = self.keys.author_books(author_id, book['isbn'])
        self.commands += [
            AUTHORS_BOOKS_HMSET_COMMAND.format(key=author_books_key, author_id=author_id, book_isbn=book['isbn'])
        ]

        return author_id

    def add_book(self, book):
        isbn = book['isbn']
        book_key = self.keys.book(isbn)
        title = escape_quotes(book.pop('title'))
        description = escape_quotes(book.pop('description'))
        book_authors = escape_quotes(book.pop('authors'))
        command = BOOK_HMSET_COMMAND

        # Add authors and establish book -> author relationship
        author_ids = ';'.join(
            [str(self.add_author(book, author)) for author in book_authors.split(";")])

        # Fields with null values (empty strings) should not appear in hashes
        # we will index with RediSearch.
        if book['published_year']:
            command += ' published_year "{published_year}"'
        if book['average_rating']:
            command += ' average_rating "{average_rating}"'

        self.commands += [
            command.format(key=book_key,
                           isbn=isbn,
                           title=title,
                           description=description,
                           author_ids=author_ids,
                           authors=book_authors,
                           **book)
        ]
        self.book_isbns += [isbn]

    def add_user(self, user_id, user):
        user_key = self.keys.user(user_id)
        escaped_email = escape_punctuation(user['email'])
        last_login = JANUARY_1 - timedelta(days=random.randint(0, 30),
                                           hours=random.randint(0, 24))
        self.commands += [USER_HMSET_COMMAND.format(key=user_key, user_id=user_id,
                                                    last_login=last_login.timestamp(),
                                                    escaped_email=escaped_email, **user)]
        self.users[user_id] = user

    def generate_checkout_data(self):
        # Late checkouts
        checkout_length_days = 30
        for user_id in range(0, 12):
            book_isbn = "9780393059168"  # Sherlock Holmes
            key = self.keys.checkout(user_id, book_isbn)
            checkout_date = JANUARY_1 - timedelta(days=35)
            self.commands += [
                CHECKOUT_HMSET_COMMAND.format(key=key,
                                              geopoint=random_coordinate(),
                                              user_id=user_id,
                                              book_isbn=book_isbn,
                                              return_date="\"\"",
                                              checkout_date=datetime.combine(
                                                  checkout_date, datetime.min.time()).timestamp(),
                                              checkout_length_days=checkout_length_days)
            ]

        # On-time checkouts
        for user_id in range(12, len(self.users) - 1):
            book_isbn = random.choice(self.book_isbns)
            key = self.keys.checkout(user_id, book_isbn)
            checkout_date = JANUARY_1
            self.commands += [
                CHECKOUT_HMSET_COMMAND.format(key=key,
                                              geopoint=random_coordinate(),
                                              user_id=user_id,
                                              book_isbn=book_isbn,
                                              return_date="\"\"",
                                              checkout_date=checkout_date.timestamp(),
                                              checkout_length_days=checkout_length_days)
            ]

    def write_commands(self):
        with open('commands.redis', 'w') as f:
            f.write('\n'.join(self.commands))


def main():
    data_generator = DataGenerator()

    with open(os.path.join('data', 'books.csv')) as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            data_generator.add_book(row)

    with open(os.path.join('data', 'users.csv')) as users_csv_file:
        reader = csv.DictReader(users_csv_file)
        for user_id, user in enumerate(reader):
            data_generator.add_user(user_id, user)

    data_generator.generate_checkout_data()
    data_generator.write_commands()


if __name__ == "__main__":
    main()
