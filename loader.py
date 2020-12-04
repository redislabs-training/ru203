import csv
import os
import random
from datetime import date, datetime, timedelta

AUTHOR_HMSET_COMMAND = 'HMSET {key} author_id {author_id} name "{name}"'
USER_HMSET_COMMAND = 'HMSET {key} user_id {user_id} first_name "{first_name}" last_name "{last_name}" email "{email}"'
CATEGORY_HMSET_COMMAND = 'HMSET {key} category_id {category_id} name "{name}"'
AUTHORS_BOOKS_SADD_COMMAND = 'SADD {key} {book_isbn13}'
CATEGORIES_BOOKS_SADD_COMMAND = 'SADD {key} {book_isbn13}'
CHECKOUT_HMSET_COMMAND = "HMSET {key} user_id {user_id} book_isbn13 {book_isbn13} checkout_date {checkout_date} return_date {return_date} checkout_length_days {checkout_length_days}"
BOOK_HMSET_COMMAND = 'HMSET {key} isbn13 "{isbn13}" title "{title}" subtitle "{subtitle}" thumbnail "{thumbnail}" description "{description}" published_year "{published_year}" average_rating "{average_rating}"'

PREFIX = "ru203"


class Keys:
    def __init__(self, prefix):
        self.prefix = prefix

    def book(self, book_isbn13):
        return f"ru203:book:details:{book_isbn13}"

    def author(self, author_id):
        return f"{self.prefix}:author:details:{author_id}"

    def author_books(self, author_id):
        return f"{self.prefix}:author:books:{author_id}"

    def category(self, category_id):
        return f"{self.prefix}:category:details:{category_id}"

    def category_books(self, category_id):
        return f"{self.prefix}:category:books:{category_id}"

    def user(self, user_id):
        return f"{self.prefix}:user:details:{user_id}"

    def checkout(self, user_id, book_isbn13):
        return f"{self.prefix}:book:checkout:{user_id}-{book_isbn13}"


class DataGenerator:
    def __init__(self):
        self.commands = []
        self.authors = {}
        self.categories = {}
        self.users = {}
        self.book_isbn13s = []
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

        author_books_key = self.keys.author_books(author_id)
        self.commands += [
            AUTHORS_BOOKS_SADD_COMMAND.format(key=author_books_key, book_isbn13=book['isbn13'])
        ]

    def add_category(self, book, category):
        category_id = self.categories.get(category)
        new_category = False

        if not category_id:
            new_category = True
            category_id = len(self.categories) + 1
            self.categories[category] = category_id

        category_key = self.keys.category(category_id)
        if new_category:
            self.commands += [
                CATEGORY_HMSET_COMMAND.format(key=category_key,
                                              category_id=category_id,
                                              name=category)
            ]

        category_books_key = self.keys.category_books(category_id)
        self.commands += [
            CATEGORIES_BOOKS_SADD_COMMAND.format(key=category_books_key, book_isbn13=book['isbn13'])
        ]

    def add_book(self, book):
        book_key = self.keys.book(book['isbn13'])
        title = book.pop('title').replace('"', '\\"').replace("'", "\\'")
        description = book.pop('description').replace('"', '\\"').replace("'", "\\'")
        subtitle = book.pop('subtitle').replace('"', '\\"').replace("'", "\\'")
        book_authors = book.pop('authors').replace('"', '\\"').replace("'", "\\'").split(';')
        book_categories = book.pop('categories').replace('"', '\\"').replace("'", "\\'").split(';')
        self.commands += [
            BOOK_HMSET_COMMAND.format(key=book_key,
                                      title=title,
                                      description=description,
                                      subtitle=subtitle,
                                      **book)
        ]
        self.book_isbn13s += [book['isbn13']]

        # Add authors and establish book -> author relationship
        for author in book_authors:
            self.add_author(book, author)

        # Add categories and establish book -> category relationships
        for category in book_categories:
            self.add_category(book, category)

    def add_user(self, user_id, user):
        user_key = self.keys.user(user_id)
        self.commands += [USER_HMSET_COMMAND.format(key=user_key, user_id=user_id, **user)]
        self.users[user_id] = user

    def generate_checkout_data(self):
        # Late checkouts
        checkout_length_days = 30
        for user_id in range(0, 12):
            book_isbn13 = random.choice(self.book_isbn13s)
            key = self.keys.checkout(user_id, book_isbn13)
            checkout_date = date.today() - timedelta(days=35)
            self.commands += [
                CHECKOUT_HMSET_COMMAND.format(key=key,
                                              user_id=user_id,
                                              book_isbn13=book_isbn13,
                                              return_date="\"\"",
                                              checkout_date=datetime.combine(
                                                  checkout_date, datetime.min.time()).timestamp(),
                                              checkout_length_days=checkout_length_days)
            ]

        # On-time checkouts
        for user_id in range(12, len(self.users) - 1):
            book_isbn13 = random.choice(self.book_isbn13s)
            key = self.keys.checkout(user_id, book_isbn13)
            checkout_date = date.today() - timedelta(days=14)
            self.commands += [
                CHECKOUT_HMSET_COMMAND.format(key=key,
                                              user_id=user_id,
                                              book_isbn13=book_isbn13,
                                              return_date="\"\"",
                                              checkout_date=datetime.combine(
                                                  checkout_date,
                                                  datetime.min.tgtgtime()).timestamp(),
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
