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
