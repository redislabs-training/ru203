# ru203-redisearch

Example code for the Redis University course RU203.

## Data

Run the following commands to load example data -- you will need Python 3.8 or higher:

    $ python loader.py
    $ redis-cli < commands.redis > output

Check the "output" file: you shouldn't have any "Invalid" responses.

## Building Indexes

Run the following command to index book checkout data:

    $ redis-cli

    127.0.0.1:6379> ft.create checkouts-idx on hash prefix 1 ru203:book:checkout: schema user_id TEXT NOSTEM SORTABLE book_isbn13 TEXT NOSTEM SORTABLE checkout_date NUMERIC SORTABLE return_date NUMERIC SORTABLE checkout_period_days NUMERIC SORTABLE

## Queries

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
