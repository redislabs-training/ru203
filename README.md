# ru203-redisearch

Example code for the Redis University course RU203.

## Introduction

This repository contains example data that you can load into an instance of Redis
running the RediSearch module, and RediSearch queries you can run against this
data.

## Getting RediSearch

You can run Redis with RediSearch for free with a Redis Cloud Essentials account:

https://redislabs.com/try-free/

You can also install Redis with RediSearch using Docker or by building from source.
For detailed instructions on how to do so, visit the
[RediSearch documentation](https://oss.redislabs.com/redisearch/).

## The Data Model

The queries in this repository work on a set of Redis Hashes that describe
books, authors, library checkouts, and users. The hashes look like the
following diagram.

```

      Authors
 +--------------+
 |  name        |               Author-Books
 |              |            +----------------+
 |  author_id   |------------|  author_id     |
 +--------------+            |                |
                         +---|  book_isbn13   |
                         |   |                |
      Users              |   +----------------+
 +--------------+        |
 |  first_name  |        |
 |              |        |
 |  last_name   |        |       Checkouts
 |              |        |  +------------------------+
 |  email       |   +----|--|  user_id               |
 |              |   |    |  |                        |
 |  user_id     |---|    |--|  book_isbn13           |
 +--------------+        |  | +                      |
                         |  |  checkout_date         |
                         |  |                        |
      Books              |  |  checkout_length_days  |
 +--------------+        |  |                        |
 |  isbn13      |--------+  |  geopoint              |
 |              |           |                        |
 |  title       |           +------------------------+
 |              |
 |  subtitle    |
 |              |
 |  thumbnail   |
 |              |
 |  description |
 |              |
 |  categories  |
 |              |
 |  authors     |
 |              |
 |  author_ids  |
 |              |
 +--------------+
```

By running the `FT.CREATE` commands in this document, you will create
a number of RediSearch indexes on this data and use those indexes to
write queries.

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

Then run the following commands, one at a time:

    FT.CREATE books-idx ON HASH PREFIX 1 ru203:book:details: SCHEMA isbn13 TEXT NOSTEM SORTABLE title TEXT WEIGHT 2.0 SORTABLE subtitle TEXT SORTABLE thumbnail TEXT NOSTEM NOINDEX description TEXT SORTABLE published_year NUMERIC SORTABLE average_rating NUMERIC SORTABLE authors TEXT SORTABLE categories TAG SEPARATOR ";" author_ids TAG SEPARATOR ";"

    FT.CREATE users-idx ON HASH PREFIX 1 ru203:user:details: SCHEMA first_name TEXT SORTABLE last_name TEXT SORTABLE email TAG SORTABLE

    FT.CREATE authors-idx ON HASH PREFIX 1 ru203:author:details: SCHEMA name TEXT SORTABLE

    FT.CREATE authors-books-idx ON HASH PREFIX 1 ru203:author:books: SCHEMA book_isbn13 TEXT NOSTEM SORTABLE author_id TEXT NOSTEM SORTABLE

    FT.CREATE checkouts-idx ON HASH PREFIX 1 ru203:book:checkout: SCHEMA user_id TEXT NOSTEM SORTABLE book_isbn13 TEXT NOSTEM SORTABLE checkout_date NUMERIC SORTABLE return_date NUMERIC SORTABLE checkout_period_days NUMERIC SORTABLE geopoint GEO

Like partial indexes in a relational database, you can use the `FILTER` option to `FT.CREATE`. Use the that option in the following command create an index on checkouts of a specific book:

    FT.CREATE sherlock-checkouts-idx ON HASH PREFIX 1 ru203:book:checkout: FILTER "@book_isbn13=='9780393059168'" SCHEMA user_id TEXT NOSTEM SORTABLE book_isbn13 TEXT NOSTEM SORTABLE checkout_date NUMERIC SORTABLE return_date NUMERIC SORTABLE checkout_period_days NUMERIC SORTABLE geopoint GEO

## Querying

### Querying versus searching

For the purposes of this course, the difference between querying and searching is that querying often involves known values. That is, you might want to query for a specific date, an ID, or a range of numbers.

When you search, on the other hand, you may not know the exact value you want to find. Full-text search therefore includes techniques like prefix matching (finding strings that start with given string) and fuzzy-matching.

This section will talk about querying, and later in this document you can find examples of full-text searches.

### Exact text matches

Run the following query to find books with a specific ISBN:

    FT.SEARCH checkouts-idx "@book_isbn13:9780393059168"

The books-idx indexes the `book_isbn13` field as `TEXT NOSTEM`, so the ISBN in this
query is treated as a text value. `NOSTEM` tells RediSearch that we don't need to
index terms for this field using "stemming," which is an approach that helps with
full-text search, but not with exact-phrase matches.

If the values in a field will contain punctuation and you want to be able to search
for exact matches using that punctuation (e.g., email addresses), you'll need to
escape any punctuation in the values when you index. And then when you query,
you also need to escape punctuation.

As an example, if the `users-idx` index stored email addresses as TEXT NOSTEM fields instead of TAG fields, a query for a specific address might look like this:

    FT.SEARCH users-idx "@email:k\\.brown\\@example\\.com"

Note that when we added the Redis Hash containing this email address, we would have
needed to escape any punctuation in the string -- in addition to escaping punctuation in this query.

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

Checkouts near New York City:

    FT.SEARCH checkouts-idx "@geopoint:[-73.935242 40.730610 1 mi]"

Checkouts near Seattle:

    FT.SEARCH checkouts-idx "@geopoint:[-122.335167 47.608013 1 mi]"

Note that when storing coordinates in a Hash, and when querying, the coordinates should appear in longitude, latitude order.

Thus the HMSET command for one of these checkout hashes should look like this:

    HMSET ru203:book:checkout:48-9780007130313 user_id 48 book_isbn13 9780007130313 checkout_date 1608278400.0 checkout_length_days 30 geopoint -73.935242,40.730610

### Sorting results

    FT.SEARCH books-idx "@published_year:[2018 +inf]" SORTBY published_year ASC

    FT.SEARCH books-idx "@published_year:[2018 +inf]" SORTBY published_year DESC

### Tags

Finding all books by a specific author, when author ID is stored as a tag -- 34 is J. R. R. Tolkien:

    FT.SEARCH books-idx "@author_ids:{34 }"

Tags accept the OR operator -- Tolkien or J. K. Rowling

    FT.SEARCH books-idx "@author_ids:{34 | 1811}"

NOTE: When tags contain spaces or punctuation, you need to escape them. If we had a tag for "j. r. r. tolkien" instead of author ID, to query it you would need to write "@authors:{j\\. r\\. r\\. tolkien" (we don't have such a tag).

Tag fields are also useful for doing exact-matches on fields when you only ever want to make exact-matches. In other words, you don't need RediSearch to tokenize the values. For example, if you store email addresses in a tag field, as the users-idx index does, then you can search for exact email addresses like so:

    FT.SEARCH users-idx "@email:{k\\.brown\\@example\\.com}"

Notice that you have to escape all punctuation in the email address.

## Aggregations

Find the number of books authored or co-authored by J. K. Rowling:

    FT.AGGREGATE books-idx * APPLY "split(@authors, ';')" AS authors GROUPBY 1 "@authors" REDUCE COUNT 1 "@authors" FILTER "@authors=='rowling, j.k.' || @authors=='j. k. rowling'"

Count the number of books with the title "Harry Potter":

Count the number of book that referenced "Harry Potter" grouped by publication year:

    FT.AGGREGATE books-idx "Harry Potter" GROUPBY 1 "@published_year" REDUCE COUNT 1 "@authors"

## Full-text search

Prefix-matching query:

    FT.SEARCH books-idx "pott*"

Fuzzy-matching (Levenshtein distance) query:

    FT.SEARCH books-idx "%pott%"

Wildcard queries -- all docsuments in the index:

    FT.SEARCH books-idx *

Adjusting the score of a single clause in the query -- this should return _Harry Potter and the Goblet of Fire_ as the first result:

    FT.SEARCH books-idx "potter" (goblet) => { $weight: 10.0}

Getting highlights:

    FT.SEARCH books-idx "%pott%" HIGHLIGHT FIELDS 3 description title subtitle

Summarizing fields:

    FT.SEARCH books-idx agamemnon SUMMARIZE FIELDS 1 description FRAGS 3 LEN 25
