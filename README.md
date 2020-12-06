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

    FT.CREATE books-idx ON HASH PREFIX 1 ru203:book:details: SCHEMA isbn13 TEXT NOSTEM SORTABLE title TEXT WEIGHT 2.0 SORTABLE subtitle TEXT SORTABLE thumbnail TEXT NOSTEM NOINDEX description TEXT SORTABLE published_year NUMERIC SORTABLE average_rating NUMERIC SORTABLE authors TEXT SORTABLE categories TAG SEPARATOR ";" author_ids TAG SEPARATOR ";"

    FT.CREATE users-idx ON HASH PREFIX 1 ru203:user:details: SCHEMA first_name TEXT SORTABLE last_name TEXT SORTABLE email TEXT NOSTEM SORTABLE

    FT.CREATE authors-idx ON HASH PREFIX 1 ru203:author:details: SCHEMA name TEXT SORTABLE

    FT.CREATE authors-books-idx ON HASH PREFIX 1 ru203:author:books: SCHEMA book_isbn13 TEXT NOSTEM SORTABLE author_id TEXT NOSTEM SORTABLE

    FT.CREATE checkouts-idx ON HASH PREFIX 1 ru203:book:checkout: SCHEMA user_id TEXT NOSTEM SORTABLE book_isbn13 TEXT NOSTEM SORTABLE checkout_date NUMERIC SORTABLE return_date NUMERIC SORTABLE checkout_period_days NUMERIC SORTABLE

<!-- TODO: This doesn't work. Why not? I asked in #redisearch. -->

If you wanted to make an index of a partial set of Hashes, like a partial index in a relational database, you can use the `FILTER` option to `FT.CREATE`. Here we'll use that option to create an index on checkouts of books of a specific book:

    FT.CREATE sherlock-checkouts-idx ON HASH PREFIX 1 ru203:book:checkout: FILTER "@book_isbn13==9780553212419"  SCHEMA user_id TEXT NOSTEM SORTABLE book_isbn13 TEXT NOSTEM SORTABLE checkout_date NUMERIC SORTABLE return_date NUMERIC SORTABLE checkout_period_days NUMERIC SORTABLE

## Queries

### Exact matches in a field

Run the following query to find books with a specific ISBN:

    FT.SEARCH checkouts-idx "@book_isbn13:9780192840509"

### Boolean logic

AND is implied by multiple fields:
    FT.SEARCH books-idx "@authors:rowling @title:goblet"

OR:
    FT.SEARCH books-idx "@authors:rowling | @authors:tolkien"

NOT:
    FT.SEARCH books-idx "@authors:tolkien' -@title:silmarillion"

### Numbers and numeric ranges

NUMERIC values are only really useful if you plan on doing number range queries. If you don't, index the value as TEXT NOSTEM, and you'll be able to do exact-phrase queries to find specific values.

If you index as NUMERIC and want to find a specific value, you need to use the range syntax, specifying that value as the lower and upper range. For example, all books published in 1955:

    FT.SEARCH books-idx "@published_year:[1955 1955]"

With a known end value:

    FT.SEARCH books-idx "@published_year:[2018 2020]"

 With an infinite end value:

    FT.SEARCH books-idx "@published_year:[2018 +inf]"

Infinite start value:

    FT.SEARCH books-idx "@published_year:[-inf 1925]"

### Dates and date ranges

To work with dates in RediSearch, you must treat them as numbers. The easiest way is using UNIX timestamps and the UTC timezone.

Finding checkouts between January 1, 2021 and February 1, 2021:

    FT.SEARCH checkouts-idx "@:[1609459200 1612137600]"

The same rules about "inf" apply here. Finding all checkouts since January 1:

    FT.SEARCH checkouts-idx "@:[1609459200 +inf]"

To find a specific date, you have to pass the same timestamp in as both the lower and upper bound of the number:

    FT.SEARCH checkouts-idx "@:[1609459200 1609459200]"

### Geo radius

TODO. Update data model. Location of checkout.

### Sorting results

    FT.SEARCH books-idx "@published_year:[2018 +inf]" SORTBY published_year ASC
    
    FT.SEARCH books-idx "@published_year:[2018 +inf]" SORTBY published_year DESC
    
