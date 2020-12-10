# ru203-redisearch

Example data and queries for the Redis University course [RU203: Querying, Indexing, and Full-Text Search with Redis](https://university.redislabs.com/courses/ru203/).

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

The queries in this repository rely on a data model comprised of Redis
hashes. The entities in this data model include books, authors, library
checkouts, and users. The following diagram represents this data model:

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
 |  isbn        |--------+  |  geopoint              |
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

Check the "output" file; you shouldn't have any "Invalid" responses. These
may indicate that you do not have RediSearch installed properly. If you have
any problems, find us on [our Discord
channel](https://discord.gg/wYQJsk5c4A).

## Building indexes

This data ships without RediSearch indexes, so you need to create them yourself.

We're going to give you all the commands you need to create these indexes, but
before you run these index commands, make sure you're in the redis CLI:

    $ redis-cli

Then run the following commands:

    FT.CREATE books-idx ON HASH PREFIX 1 ru203:book:details: SCHEMA isbn TAG SORTABLE title TEXT WEIGHT 2.0 SORTABLE subtitle TEXT SORTABLE thumbnail TAG NOINDEX description TEXT SORTABLE published_year NUMERIC SORTABLE average_rating NUMERIC SORTABLE authors TEXT SORTABLE categories TAG SEPARATOR ";" author_ids TAG SEPARATOR ";"

    FT.CREATE users-idx ON HASH PREFIX 1 ru203:user:details: SCHEMA first_name TEXT SORTABLE last_name TEXT SORTABLE email TAG SORTABLE escaped_email TEXT NOSTEM SORTABLE user_id TAG SORTABLE

    FT.CREATE authors-idx ON HASH PREFIX 1 ru203:author:details: SCHEMA name TEXT SORTABLE author_id TAG SORTABLE

    FT.CREATE authors-books-idx ON HASH PREFIX 1 ru203:author:books: SCHEMA book_isbn TAG SORTABLE author_id TAG SORTABLE

    FT.CREATE checkouts-idx ON HASH PREFIX 1 ru203:book:checkout: SCHEMA user_id TAG SORTABLE book_isbn TAG SORTABLE checkout_date NUMERIC SORTABLE return_date NUMERIC SORTABLE checkout_period_days NUMERIC SORTABLE geopoint GEO

## Querying structured data

### Querying versus full-text search

For the purposes of this course, we organize concepts based on whether you are querying structured data or doing full-text search. The reality is that full-text search is a kind of query, and in fact, you use the same RediSearch command for both: `FT.SEARCH`.

However, there are important differences. When you query, you are probably looking for a known value, or set of values, in structured data. Imagine data such as the following:

- IDs
- Email address
- Dates
- Numbers

So, you might query for a specific date, an ID, or a range of numbers.

When you perform a full-text search, on the other hand, you may not know the exact value you want to find. And the fields you're searching may contain unstructured data, like product descriptions or user reviews. Full-text search therefore includes techniques like stemming (searching for the "stems" of words, e.g. "run" instead of "running"), prefix matching (finding strings that start with a given string), and fuzzy-matching, which finds related, or alternate spellings of a term, using Levenshtein distance.

This section will talk about querying, and later in this document you can find examples of full-text searches.

### Finding exact string matches

If you know that you will only ever query a field for exact string matches
like IDs, categories, or email addresses, then the most efficient field
type is TAG. This field type isn't tokenized or stemmed, making it ideal for
exact string matches.

Run the following query to find books with a specific [ISBN](https://en.wikipedia.org/wiki/International_Standard_Book_Number):

    FT.SEARCH checkouts-idx "@book_isbn:{9780393059168}"

---
**A note on querying specific fields:** This example and all others in the "querying" section of this course use field-specific searches. You specify that a term in the query -- here, the term is `{9780393059168}` -- applies to a specific field by prefixing it with the `@` symbol and the field name. In the prior example, `@book_isbn` tells RediSearch to look in the `book_isbn` field within the index. When we talk about full-text search, you'll see examples of searching across fields.

---

Another example: Finding all books by a specific author, when author ID is stored as a tag. This query searches for books by J. R. R. Tolkien, the author with the ID 34:

    FT.SEARCH books-idx "@author_ids:{34}"

TAG fields can have multiple values, and so you can query for documents that contain more than one expected TAG value. This is a boolean `AND` operation. Querying this way is useful when tag fields store data like categories. Here, we use this feature to query for books written by _both_ Astre Mithrandir and Galadriel Waters (books they co-authored):

    FT.SEARCH books-idx "@author_ids:{3569} @author_ids:{3570}"

You can also use the boolean `OR` operator -- but this can occur within the curly braces that delimit a tag query. See what I mean in this query that searches for books by Tolkien or J. K. Rowling:

    FT.SEARCH books-idx "@author_ids:{34 | 1811}"
---
**A note on querying with punctuation:** To query for a tag that includes punctuation, like an email address, you need to escape the punctuation (the data in the underlying Hash does not need to be escaped). For example, if we had a tag for "j. r. r. tolkien" instead of author ID, to query it you would need to write `@authors:{j\\. r\\. r\\. tolkien}`.

Because of this, as a general rule you should always escape the following punctuation in queries:

    ,.<>{}[]"':;!@#$%^&*()-+=~
---

### Numbers and numeric ranges

NUMERIC index types are useful for doing number range queries, and if you want to write aggregations (covered elsewhere in this document) that use numeric functions.

One thing to note about NUMERIC fields is that querying them always requires a range, even if you query for a single value. For example, to find all books published in 1955, you specify 1955 as the lower and upper bound of a numeric range:

    FT.SEARCH books-idx "@published_year:[1955 1955]"

To instead to query for books published between 2018 and 2020, doing so looks like this:

    FT.SEARCH books-idx "@published_year:[2018 2020]"

You can use the value `+inf` for an unbounded end value. For example, this query finds all books published from 2018 to the highest year in the index:

    FT.SEARCH books-idx "@published_year:[2018 +inf]"

Using `-inf` specifies an unbounded start value the same way. Here we get all
books published from the earliest year in the index until 1925:

    FT.SEARCH books-idx "@published_year:[-inf 1925]"

### Working with dates and times

To work with dates in RediSearch, you must store them as UNIX timestamps in a NUMERIC field.

Finding checkouts between December 1, 2020 and January 1, 2021 looks like the following:

    FT.SEARCH checkouts-idx "@checkout_date:[1606780800 1609459200]"

The same rules about the `-inf` and `+inf` values that apply to other NUMERIC
fields apply here. For example, finding all checkouts of books made since
January 1 looks like this:

    FT.SEARCH checkouts-idx "@checkout_date:[1609459200 +inf]"

To find a specific date, you have to pass the same timestamp in as both the
lower and upper bound of the number.  Here, we search for all checkouts _on_
January 1, 2021:

    FT.SEARCH checkouts-idx "@checkout_date:[1609459200 1609459200]"

### Searching geographic areas

You can search within a geographic radius by storing coordinates in Hashes
and indexing them as GEO fields.

Here's how you'd find book checkouts near New York City:

    FT.SEARCH checkouts-idx "@geopoint:[-73.935242 40.730610 1 mi]"

And here's how you'd find checkouts near Seattle:

    FT.SEARCH checkouts-idx "@geopoint:[-122.335167 47.608013 1 mi]"

Note that when storing coordinates in a hash, and when querying, the coordinates should appear in (longitude, latitude) order.

Thus the HMSET command for one of these checkout hashes should look like this:

    HMSET ru203:book:checkout:48-9780007130313 user_id 48 book_isbn 9780007130313 checkout_date 1608278400.0 checkout_length_days 30 geopoint -73.935242,40.730610

### Binary logic

You can use binary logic to connect multiple terms in a query.

AND is implied by specifying multiple terms -- here we find all full-text search
matches of "rowling" in the `authors` field and "goblet" in the `title` field:

    FT.SEARCH books-idx "@authors:rowling @title:goblet"

Specify OR logic with a pipe, such as in the following query in which we find
books whose authors include "rowling" OR "tolkien":

    FT.SEARCH books-idx "@authors:rowling | @authors:tolkien"

Use the dash (`-`) character for a NOT query, as in this query in which we
search for books by with the string "tolkien" in the `authors` field and NOT
the string "silmarillion" in the `title` field:

    FT.SEARCH books-idx "@authors:tolkien' -@title:silmarillion"

### Sorting results

You can sort query results with the `SORTBY` option to `FT.SEARCH`.

Here we query for all books published from 2018 and later, sorted by the
published year (ascending):

    FT.SEARCH books-idx "@published_year:[2018 +inf]" SORTBY published_year ASC

And then the same query, sorted descending:

    FT.SEARCH books-idx "@published_year:[2018 +inf]" SORTBY published_year DESC

### Limiting results

You can use the `LIMIT` option to `FT.SEARCH` to limit the number of results
returned by a query. This option takes two arguments: the offset and the
limit, in that order.

Here we query for one book published in 1955:

    FT.SEARCH books-idx "@published_year:[1955 1955]" SORTBY published_year LIMIT 0 1

As you can see, the offset is zero-based.

You can use offset argument to `LIMIT` for pagination. Thus, to get the first
Harry Potter books ordered by publication date, you might write:

    FT.SEARCH books-idx "harry potter @authors:rowling" SORTBY published_year LIMIT 0 5

## Full-text search

Returning to the distinction we made earlier between querying and full-text search in this course: full-text search is most useful when you don't know the exact value you want to find, or you are searching unstructured data.

### Standard full-text search

This query searches for the terms "harry" and "potter" in all the TEXT fields in the index (e.g., title, subtitle, and description). Both terms in the query are stemmed, as are the terms stored in the index.

    FT.SEARCH books-idx harry potter

### Prefix matching

You can also use "prefix-matching" to compare an input string as a prefix against _all_ terms in the index, for all TEXT fields. Here we search for documents that have a term in any indexed TEXT field that starts with "pott":

    FT.SEARCH books-idx "pott*"

### Binary logic, field-specific searches, sorting, and limiting

All of the techniques mentioned in this document for binary logic, field-specific
searches, sorting, and limiting also work for full-text searches.

For example, we can use a field-specific full-text search for the term "wizard" in the `description` field of books, excluding any books that mention "Harry" in _any_ TEXT field, sort the results by title, and return only the first book found:

    FT.SEARCH books-idx "@description:wizard -harry"  SORTBY "title" LIMIT 0 1

### Highlighting and summarization

Returning HTML "highlights" around term matches in full-text search results is a standard feature of search engines, and you can do it with RediSearch.

Here's how you'd search for "potter" and highlight any matches found in the description, title, or subtitle fields:

    FT.SEARCH books-idx potter HIGHLIGHT FIELDS 3 description title subtitle

Summarizing refers to the practice of returning small snippets of text around terms that matched a query, rather than the entire field. This query returns a maximum of three "fragments" (the default) of 25 words each for hits of the term "agamemnon":

    FT.SEARCH books-idx agamemnon SUMMARIZE FIELDS 1 description FRAGS 3 LEN 25

## Aggregations

### Grouping results

A common use of aggregations is to group results. You do that in
RediSearch with the `GROUPBY` option to the `FT.AGGREGATE` command.

Here, we get all the years in which someone published a book that mentioned Tolkien:

    FT.AGGREGATE books-idx Tolkien GROUPBY 1 "@published_year"

### Sorting aggregate results

You can sort aggregate query results with the `SORTBY` option. To build on the last query, we now retrieve the years that someone published a book mentioning Tolkien _sorted by the publication year_:

    FT.AGGREGATE books-idx Tolkien GROUPBY 1 "@published_year" SORTBY 1 @published_year

### Reducing

The typical use of grouping results is to "reduce" them, which means run each group through a function. To continue our Tolkien example, say we want to count the number of titles published each year that mentioned Tolkien, sorted by year:

    FT.AGGREGATE books-idx Tolkien GROUPBY 1 "@published_year" REDUCE COUNT 1 @title AS titles_published SORTBY 1 @published_year

### Transforming values

Use the `APPLY` option to `FT.AGGREGATE` to transform values in the index. This is useful to break up multiple values in a TAG field and transform dates from UNIX timestamps to human-readable date strings.

Here's an example -- we find the number of books authored or co-authored by J. K. Rowling by splitting the `authors` TAG field and reducing the resulting groups down to a count of each author's books:

    FT.AGGREGATE books-idx "@authors:rowling" APPLY "split(@authors, ';')" AS author GROUPBY 1 "@author" REDUCE COUNT 1 "@author" AS book_count FILTER "@author=='rowling, j.k.' || @author=='j. k. rowling'" GROUPBY 2 @book_count @author

Or, here's a timestamp example. This query looks at all book checkouts and returns the number of checkouts on each date, but instead of returning UNIX timestamps, returns formatted date strings -- thanks to the `timefmt()` function:

    FT.AGGREGATE checkouts-idx * APPLY "timefmt(@checkout_date)" as checkout_formatted GROUPBY 1 @checkout_formatted REDUCE COUNT 1 @checkout_date as num_checkouts

### Counting query results

A common use of aggregations in relational databases is to return how
many records match a query by using `SELECT COUNT`. With RediSearch, you don't
actually use an aggregation for this -- you use `LIMIT` -- but we've included
this topic in the aggregations section because "aggregations" is where you
might look for this feature.

If you want to return the number of books that mention Tolkien, but not the actual results, you can do so like this:

    FT.SEARCH books-idx Tolkien limit 0 0

## Advanced Topics

Sign up for the course to learn about advanced topics, like:

* Creating partial indexes
* Adjusting the score of a single term within a query
* Getting all documents in an index
* Exact-matching punctuation in a TEXT field
* Handling spelling errors

Visit the [course signup page](https://university.redislabs.com/courses/ru203/) to register!



### Partial Indexes

Like partial indexes in a relational database, you can use the `FILTER` option to `FT.CREATE`. Use the that option in the following command create an index on checkouts of a specific book:

    FT.CREATE sherlock-checkouts-idx ON HASH PREFIX 1 ru203:book:checkout: FILTER "@book_isbn=='9780393059168'" SCHEMA user_id TEXT NOSTEM SORTABLE book_isbn TEXT NOSTEM SORTABLE checkout_date NUMERIC SORTABLE return_date NUMERIC SORTABLE checkout_period_days NUMERIC SORTABLE geopoint GEO

Now you can query for only users who've checked out this book:

    FT.SEARCH sherlock-checkouts-idx *

### Adjusting the Score of a Term

Adjusting the score of a single term in the query -- this should return _Harry Potter and the Goblet of Fire_ as the first result:

    FT.SEARCH books-idx "potter (goblet) => { $weight: 10.0}"

### Getting All Documents in an Index

Wildcard queries -- all documents in the index:

    FT.SEARCH books-idx *

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

### Handling Spelling Errors

Fuzzy-matching (Levenshtein distance) query -- searching across all indexed TEXT fields using Levenshtein distance (transparently handle some spelling errors in a query):

    FT.SEARCH books-idx "%pott%"

Explicitly find potential misspellings:

    FT.SPELLCHECK books-idx wizrds
