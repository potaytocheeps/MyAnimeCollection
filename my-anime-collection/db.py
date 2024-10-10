import sqlite3

import click
from flask import current_app, g


def get_database():
    """Connect to the application's configured database. The connection is
    unique for each request and will be reused if this is called again during
    the same request.
    """

    # g is special object that is unique for each request, and is used to store
    # data that can be accessed by multiple functions for the duration of the request
    if "database" not in g:
        g.database = sqlite3.connect(
            # Establish a connection to the file pointed at by the "DATABASE" configuration key
            current_app.config["DATABASE"],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        # Tell the connection to return rows that behave like dicts, in order to access columns by name
        g.database.row_factory = sqlite3.Row

    return g.database


def close_database(e=None):
    """If this request connected to the database, close the connection before
    sending the response.
    """

    database = g.pop("database", None)

    if database is not None:
        database.close()
