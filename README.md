# RU203: Querying, Indexing, and Full-text Search with Redis

## Introduction

This repository contains example data and setup instructions for the Redis University course [RU203: Querying, Indexing, and Full-Text Search with Redis](https://university.redislabs.com/courses/ru203/).

Follow the steps in this document to get ready to run the example queries from the course.

## Getting help

Need help getting started? Stop by the [Redis University Discord server](https://discord.gg/wYQJsk5c4A).

## Getting RediSearch

You can get a free, cloud-hosted instance of Redis with RediSearch by creating a [Redis Cloud Essentials](https://redislabs.com/try-free/) account.

To run RediSearch locally, you have a couple of options:

* [Run the RediSearch Docker container](https://redislabs.com/blog/getting-started-with-redisearch-2-0/)
* [Build RediSearch from source](https://oss.redislabs.com/redisearch/Quick_Start/?_gl=1*v4bgp*_gcl_aw*R0NMLjE2MDc3MjIwMDIuQ2owS0NRaUF6c3otQlJDQ0FSSXNBTm90RmdNUnl6NXZQMk9lSzYyTXR2OXZJY0JRNXlZUDRBMnNSTXVrc2RQVDdfZkhtRG9JdThsUmdBZ2FBa2g3RUFMd193Y0I.#building_and_running_from_source)

## The Data Model

The queries in this repository rely on a data model composed of Redis
hashes. The entities in this data model include books, authors, library
checkouts, and users. The following diagram represents this data model:

```
    Authors
+--------------+
|  name        |               Author-Books
|              |            +----------------+
|  author_id   +------------+  author_id     |
|              |            |                |
+--------------+        +---+  book_isbn     |
                        |   |                |
    Users               |   +----------------+
+--------------+        |
|  first_name  |        |
|              |        |
|  last_name   |        |       Checkouts
|              |        |  +------------------------+
|  email       |   +----|--+  user_id               |
|              |   |    |  |                        |
|  user_id     +---+    +--+  book_isbn             |
|              |        |  |                        |
|  last_login  |        |  |  checkout_date         |
|              |        |  |                        |
+--------------+        |  |  checkout_length_days  |
                        |  |                        |
    Books               |  |  geopoint              |
+--------------+        |  |                        |
|  isbn        +--------+  +------------------------+
|              |
|  title       |
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

    FT.CREATE books-idx ON HASH PREFIX 1 ru203:book:details: SCHEMA isbn TAG SORTABLE title TEXT WEIGHT 2.0 subtitle TEXT SORTABLE thumbnail TAG NOINDEX description TEXT SORTABLE published_year NUMERIC SORTABLE average_rating NUMERIC SORTABLE authors TEXT SORTABLE categories TAG SEPARATOR ";" author_ids TAG SEPARATOR ";"

    FT.CREATE users-idx ON HASH PREFIX 1 ru203:user:details: SCHEMA first_name TEXT SORTABLE last_name TEXT SORTABLE email TAG SORTABLE escaped_email TEXT NOSTEM SORTABLE user_id TAG SORTABLE last_login NUMERIC SORTABLE

    FT.CREATE authors-idx ON HASH PREFIX 1 ru203:author:details: SCHEMA name TEXT SORTABLE author_id TAG SORTABLE

    FT.CREATE authors-books-idx ON HASH PREFIX 1 ru203:author:books: SCHEMA book_isbn TAG SORTABLE author_id TAG SORTABLE

    FT.CREATE checkouts-idx ON HASH PREFIX 1 ru203:book:checkout: SCHEMA user_id TAG SORTABLE book_isbn TAG SORTABLE checkout_date NUMERIC SORTABLE return_date NUMERIC SORTABLE checkout_period_days NUMERIC SORTABLE geopoint GEO

## You're Ready!

Now, you're ready to take the course.

If you aren't signed up yet, visit the [course signup page](https://university.redislabs.com/courses/ru203/) to register!
