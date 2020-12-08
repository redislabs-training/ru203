# ru203-redisearch

Example code for the Redis University course RU203.

## Introduction

This repository contains example data and queries to help you learn [RediSearch](https://oss.redislabs.com/redisearch/), the querying, indexing, and full-text search engine for Redis.

You can load the sample dataset and then practice running RediSearch queries against that data.

## Getting help

Need help getting started? Stop by the #ru203-querying-indexing-and-full-text-search
channel in our Discord server: https://discord.gg/wYQJsk5c4A.

## Getting RediSearch

You can get free, cloud-hosted instance of Redis with RediSearch by creating a [Redis Cloud Essentials](https://redislabs.com/try-free/) account.

To run RediSearch locally, you have a couple of options:

* [Run the RediSearch Docker container](https://oss.redislabs.com/redisearch/Quick_Start.html#running_with_docker)
* [Build RediSearch from source](https://oss.redislabs.com/redisearch/Quick_Start.html#building_and_running_from_source).

## The Data Model

The queries in this repository rely on a data model comprised of Redis hashes. The entities in this data model include
books, authors, library checkouts, and users. The following diagram represents this data model:

```

      Authors
 +--------------+
 |  name        |               Author-Books
 |              |            +----------------+
 |  author_id   |------------|  author_id     |
 +--------------+            |                |
                         +---|  book_isbn     |
                         |   |                |
      Users              |   +----------------+
 +--------------+        |
 |  first_name  |        |
 |              |        |
 |  last_name   |        |       Checkouts
 |              |        |  +------------------------+
 |  email       |   +----|--|  user_id               |
 |              |   |    |  |                        |
 |  user_id     |---|    |--|  book_isbn             |
 +--------------+        |  |                        |
                         |  |  checkout_date         |
                         |  |                        |
      Books              |  |  checkout_length_days  |
 +--------------+        |  |                        |
 |  isbn        |--------+  |  geopoint                |
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

Run the following command to load the example dataset:

    $ redis-cli < commands.redis > output

Check the "output" file; you shouldn't have any "Invalid" responses. These may indicate that
you do not have RediSearch installed properly. If you have any problems, find us on [our Discord channel](https://discord.gg/wYQJsk5c4A).

## Building indexes

This data ships without RediSearch indexes, so you need to create them yourself.

We're going to give you all the commands you need to create these indexes, but
before you run these index commands, make sure you're in the redis CLI:

    $ redis-cli

Then run the following commands:

    FT.CREATE books-idx ON HASH PREFIX 1 ru203:book:details: SCHEMA isbn TEXT NOSTEM SORTABLE title TEXT WEIGHT 2.0 SORTABLE subtitle TEXT SORTABLE thumbnail TEXT NOSTEM NOINDEX description TEXT SORTABLE published_year NUMERIC SORTABLE average_rating NUMERIC SORTABLE authors TEXT SORTABLE categories TAG SEPARATOR ";" author_ids TAG SEPARATOR ";"

    FT.CREATE users-idx ON HASH PREFIX 1 ru203:user:details: SCHEMA first_name TEXT SORTABLE last_name TEXT SORTABLE email TAG SORTABLE escaped_email TEXT NOSTEM SORTABLE user_id TEXT NOSTEM SORTABLE

    FT.CREATE authors-idx ON HASH PREFIX 1 ru203:author:details: SCHEMA name TEXT SORTABLE author_id TEXT NOSTEM SORTABLE

    FT.CREATE authors-books-idx ON HASH PREFIX 1 ru203:author:books: SCHEMA book_isbn TEXT NOSTEM SORTABLE author_id TEXT NOSTEM SORTABLE

    FT.CREATE checkouts-idx ON HASH PREFIX 1 ru203:book:checkout: SCHEMA user_id TEXT NOSTEM SORTABLE book_isbn TEXT NOSTEM SORTABLE checkout_date NUMERIC SORTABLE return_date NUMERIC SORTABLE checkout_period_days NUMERIC SORTABLE geopoint GEO

## Querying

### Querying versus searching

For the purposes of this course, the difference between querying and searching is that querying often involves known values. That is, you might want to query for a specific date, an ID, or a range of numbers.

When you search, on the other hand, you may not know the exact value you want to find. Full-text search therefore includes techniques like prefix matching (finding strings that start with given string) and fuzzy-matching.

This section will talk about querying, and later in this document you can find examples of full-text searches.

### Exact text matches

Run the following query to find books with a specific [ISBN](https://en.wikipedia.org/wiki/International_Standard_Book_Number):

    FT.SEARCH checkouts-idx "@book_isbn:9780393059168"

The `books-idx` index stores the `book_isbn` field as `TEXT NOSTEM`, so the ISBN in this query is treated as a literal text value.

`NOSTEM` tells RediSearch not to apply any special stemming or tokenization rules when adding this term to the index.
Tokenization and stemming help with
full-text search but not with exact-phrase matches.

### Boolean logic

A boolean `AND` is implied by multiple fields:

    FT.SEARCH books-idx "@authors:rowling @title:goblet"

Here's a boolean `OR` (represented by the `|` character):

    FT.SEARCH books-idx "@authors:rowling | @authors:tolkien"

You represent a boolean `NOT` with the `-` character):

    FT.SEARCH books-idx "@authors:tolkien' -@title:silmarillion"

### Numbers and numeric ranges

`NUMERIC` index types are useful when you need numeric range queries. If you only plan to query these values as exact numeric matches, then you should index them as `TEXT NOSTEM`.

If you index as NUMERIC and want to find a specific value, you need to use the range syntax, specifying that value as the lower and upper range. For example, all books published in 1955:

    FT.SEARCH books-idx "@published_year:[1955 1955]"

With a known end value:

    FT.SEARCH books-idx "@published_year:[2018 2020]"

With an unbounded end value:

    FT.SEARCH books-idx "@published_year:[2018 +inf]"

With an unbounded start value:

    FT.SEARCH books-idx "@published_year:[-inf 1925]"

### Dates and date ranges

To work with dates in RediSearch, you must treat them as numbers. The easiest way is using UNIX timestamps and the UTC timezone.

Finding checkouts between December 1, 2020 and January 1, 2021:

    FT.SEARCH checkouts-idx "@checkout_date:[1606780800 1609459200]"

The same rules about "inf" apply here. Finding all checkouts since January 1:

    FT.SEARCH checkouts-idx "@checkout_date:[1609459200 +inf]"

To find a specific date, you have to pass the same timestamp in as both the lower and upper bound of the number.
Here we're searching for all checkouts _on_ January 1, 2021:

    FT.SEARCH checkouts-idx "@checkout_date:[1609459200 1609459200]"

### Geo radius

Checkouts near New York City:

    FT.SEARCH checkouts-idx "@geopoint:[-73.935242 40.730610 1 mi]"

Checkouts near Seattle:

    FT.SEARCH checkouts-idx "@geopoint:[-122.335167 47.608013 1 mi]"

Note that when storing coordinates in a hash, and when querying, the coordinates should appear in (longitude, latitude) order.

Thus the HMSET command for one of these checkout hashes should look like this:

    HMSET ru203:book:checkout:48-9780007130313 user_id 48 book_isbn 9780007130313 checkout_date 1608278400.0 checkout_length_days 30 geopoint -73.935242,40.730610

### Sorting results

    FT.SEARCH books-idx "@published_year:[2018 +inf]" SORTBY published_year ASC

    FT.SEARCH books-idx "@published_year:[2018 +inf]" SORTBY published_year DESC

### Tags

Finding all books by a specific author, when author ID is stored as a tag -- 34 is J. R. R. Tolkien:

    FT.SEARCH books-idx "@author_ids:{34}"

Tags accept the OR operator -- Tolkien or J. K. Rowling

    FT.SEARCH books-idx "@author_ids:{34 | 1811}"

NOTE: When tags contain spaces or punctuation, you need to escape them. If we had a tag for "j. r. r. tolkien" instead of author ID, to query it you would need to write "@authors:{j\\. r\\. r\\. tolkien" (we don't have such a tag).

Tag fields are also useful for doing exact matches on fields when you only ever want to make exact matches. In other words, you don't need RediSearch to tokenize the values. For example, if you store email addresses in a tag field, as the users-idx index does, then you can search for exact email addresses like so:

    FT.SEARCH users-idx "@email:{k\\.brown\\@example\\.com}"

Notice that you have to escape any punctuation in the query. As a general rule,
always escape the following punctuation in queries:

    ,.<>{}[]"':;!@#$%^&*()-+=~

## Aggregations

Find the number of books authored or co-authored by J. K. Rowling:

    FT.AGGREGATE books-idx * APPLY "split(@authors, ';')" AS authors GROUPBY 1 "@authors" REDUCE COUNT 1 "@authors" AS book_count FILTER "@authors=='rowling, j.k.' || @authors=='j. k. rowling'"

Count the number of book that reference "Harry Potter" and group them by publication year:

    FT.AGGREGATE books-idx "Harry Potter" GROUPBY 1 "@published_year" REDUCE COUNT 1 "@authors" AS book_count

## Full-text search

Prefix-matching query:

    FT.SEARCH books-idx "pott*"

Fuzzy-matching (Levenshtein distance) query:

    FT.SEARCH books-idx "%pott%"

Wildcard queries -- all documents in the index:

    FT.SEARCH books-idx *

Adjusting the score of a single clause in the query -- this should return _Harry Potter and the Goblet of Fire_ as the first result:

    FT.SEARCH books-idx "potter (goblet) => { $weight: 10.0}"

Getting highlights:

    FT.SEARCH books-idx "%pott%" HIGHLIGHT FIELDS 3 description title subtitle

Summarizing fields:

    FT.SEARCH books-idx agamemnon SUMMARIZE FIELDS 1 description FRAGS 3 LEN 25

## Advanced Topics

### Partial Indexes

Like partial indexes in a relational database, you can use the `FILTER` option to `FT.CREATE`. Use the that option in the following command create an index on checkouts of a specific book:

    FT.CREATE sherlock-checkouts-idx ON HASH PREFIX 1 ru203:book:checkout: FILTER "@book_isbn=='9780393059168'" SCHEMA user_id TEXT NOSTEM SORTABLE book_isbn TEXT NOSTEM SORTABLE checkout_date NUMERIC SORTABLE return_date NUMERIC SORTABLE checkout_period_days NUMERIC SORTABLE geopoint GEO

Now you can query for only users who've checked out this book:

    FT.SEARCH sherlock-checkouts-idx *

### Exact-matching Punctuation

If the values in a field will contain punctuation and you want to be able to search
for exact matches using that punctuation (e.g., email addresses), you'll need to
escape any punctuation in the values when you index. And then when you query,
you also need to escape punctuation.

As an example, the `users-idx` index stores email addresses as TEXT NOSTEM
fields _and_ as TAG fields, to provide examples for both. When we added the
email address that we planned to use as a TEXT field, we escaped all the
punctuation, like so:

    HMSET ru203:user:details:28 first_name "Kelvin" last_name "Brown" email "k.brown@example.com" escaped_email "k\\.brown\\@example\\.com" user_id "28"

To query this field later for an exact-match on an email address, we also need to
escape any punctuation in the query:

    FT.SEARCH users-idx "@escaped_email:k\\.brown\\@example\\.com"

If you want to find exact-matches on punctuation, the punctuation you need to
escape when indexing _and_ querying is:

    ,.<>{}[]"':;!@#$%^&*()-+=~
