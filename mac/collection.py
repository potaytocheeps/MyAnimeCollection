from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from mac.auth import login_required
from mac.db import get_database

blueprint = Blueprint("collection", __name__)

@blueprint.route("/")
@login_required
def index():
    """Displays the user's anime collection."""

    # Get connection to database
    database = get_database()

    # Get list of titles of shows that the user has added to their collection
    collection = database.execute("SELECT title "
                                  "FROM anime_shows "
                                  "WHERE id in ("
                                  "    SELECT anime_id"
                                  "    FROM anime_collections"
                                  "    WHERE user_id = ?"
                                  ")",
                                  [g.user["id"]]).fetchall()

    # Will contain a message if user doesn't have a collection yet
    message = None

    # Add message if collection is empty
    if not collection:
        message = ("This is where your anime collection will be displayed once "
                   "you add some shows to your collection!")

    return render_template("collection/index.html", message=message, collection=collection)


@blueprint.route("/search", methods=["GET", "POST"])
@login_required
def search():
    """Allow user to search the database for an anime by its title."""

    # User reached this view via a POST request
    if request.method == "POST":
        # Get user data submission
        title = request.form.get("title")

        # Get connection to database
        database = get_database()

        # Keep track of any errors that may occur
        error = None

        # Search if title is in the anime_shows table of the database
        anime_list = database.execute("SELECT * FROM anime_shows WHERE title LIKE ?",
                                      ["%" + title + "%"]).fetchall()

        # Check that title matches any shows in database
        if not anime_list:
            error = "No anime matches that name."

        if error is None:
            return render_template("collection/searched.html", anime_list=anime_list)

        flash(error)

    return render_template("collection/search.html")
