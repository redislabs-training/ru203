# ru203-redisearch

Example code for the Redis University course RU203.

## Data

Run the following commands to load example data -- you will need Python 3.8 or higher:

    $ python loader.py
    $ redis-cli < commands.redis > output

Check the "output" file: you shouldn't have any "Invalid" responses.

## Building Indexes

This data ships without RediSearch indexes, so you need to create them yourself.

We're going to give you all the commands you need to create these indexes, but
before you run them, make sure you're in the redis CLI:

    $ redis-cli

    FT.CREATE books-idx ON HASH PREFIX 1 ru203:book:details: SCHEMA book_isbn13 TEXT NOSTEM SORTABLE title TEXT WEIGHT 2.0 SORTABLE subtitle TEXT SORTABLE thumbnail TEXT NOSTEM NOINDEX description TEXT SORTABLE published_year NUMERIC SORTABLE average_rating NUMERIC SORTABLE authors TEXT SORTABLE categories TAG SEPARATOR ";" author_ids TAG SEPARATOR ";"

    FT.CREATE users-idx ON HASH PREFIX 1 ru203:user:details: SCHEMA first_name TEXT SORTABLE last_name TEXT SORTABLE email TEXT NOSTEM SORTABLE

    FT.CREATE authors-idx ON HASH PREFIX 1 ru203:author:details: SCHEMA name TEXT SORTABLE

    FT.CREATE authors-books-idx ON HASH PREFIX 1 ru203:author:books: SCHEMA book_isbn13 TEXT SORTABLE author_id TEXT SORTABLE

    FT.CREATE checkouts-idx ON HASH PREFIX 1 ru203:book:checkout: SCHEMA user_id TEXT NOSTEM SORTABLE book_isbn13 TEXT NOSTEM SORTABLE checkout_date NUMERIC SORTABLE return_date NUMERIC SORTABLE checkout_period_days NUMERIC SORTABLE

## Queries

### Exact matches in a field

Run the following query to find books with a specific ISBN:

    127.0.0.1:6379> ft.search checkouts-idx "@book_isbn13:9780192840509"
    1) (integer) 1
    2) "ru203:book:checkout:28-9780192840509"
    3) 1) "user_id"
       2) "28"
       3) "book_isbn13"
       4) "9780192840509"
       5) "checkout_date"
       6) "1605772800.0"
       7) "checkout_length_days"
       8) "30"

### Numeric ranges

Note that if you want to use a number value in a range during queries,
you will need to index these fields as NUMERIC. At that point, you must
always use a numeric range query -- even to find single values:

    127.0.0.1:6379> ft.search checkouts-idx "@book_isbn13:[9780192840509 9780192840509]"
    1) (integer) 1
    2) "ru203:book:checkout:28-9780192840509"
    3) 1) "user_id"
       2) "28"
       3) "book_isbn13"
       4) "9780192840509"
       5) "checkout_date"
       6) "1605772800.0"
       7) "checkout_length_days"
       8) "30"
