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


def initialize_database():
    """Clear all existing data in database and create new tables."""

    # Get connection to database
    database = get_database()

    # Execute commands in "schema.sql" to create new database
    with current_app.open_resource("schema.sql") as file:
        database.executescript(file.read().decode("utf8"))


@click.command("initialize-database")
def initialize_database_command():
    """Create command line command to initialize the database."""

    initialize_database()
    click.echo("Initialized the database.")


def initialize_app(app):
    """Register database functions with application instance."""

    # Tell Flask to call close_database() when cleaning up after returning a response
    app.teardown_appcontext(close_database)
    # Add new command that can be called with the "flask" command
    app.cli.add_command(initialize_database_command)
