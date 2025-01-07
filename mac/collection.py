from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from mac.auth import login_required
from mac.db import get_database

import xml.etree.ElementTree as ET
import urllib.request

import re

blueprint = Blueprint("collection", __name__)

@blueprint.route("/")
@login_required
def index():
    """Displays the user's anime collection."""

    # Get connection to database
    database = get_database()

    # Get list of release titles, ids, and images of shows that the user has added to their collection
    collection = database.execute("SELECT release_title, release_id, image "
                                  "FROM anime_releases "
                                  "WHERE release_id in ("
                                  "    SELECT release_id"
                                  "    FROM anime_collections"
                                  "    WHERE user_id = ?"
                                  ") AND anime_id in ("
                                  "    SELECT anime_id"
                                  "    FROM anime_collections"
                                  "    WHERE user_id = ?"
                                  ") ORDER BY release_title",
                                  [g.user["user_id"], g.user["user_id"]]).fetchall()

    # Create list to hold anime information about each anime in collection
    anime_collection = []

    # Add anime information for each anime and add to anime_collection list
    for anime in collection:
        anime = dict(anime)

        # Add link to each release's ANN page
        anime["link"] = f"https://www.animenewsnetwork.com/encyclopedia/releases.php?id={anime.get('release_id')}"

        # Get more information for each anime in collection from database
        anime_information = database.execute("SELECT price_bought, date_bought, comment "
                                             "FROM anime_collections "
                                             "WHERE release_id = ? AND user_id = ?",
                                             [anime.get("release_id"), g.user["user_id"]]).fetchone()

        # Add anime information to anime dict
        anime["price_bought"] = anime_information["price_bought"]
        anime["date_bought"] = anime_information["date_bought"]
        anime["comment"] = anime_information["comment"]

        anime_collection.append(anime)

    # Will contain a message if user doesn't have a collection yet
    message = None

    # Add message if collection is empty
    if not collection:
        message = ("This is where your anime collection will be displayed once "
                   "you add some shows to your collection!")

    return render_template("collection/index.html", message=message, collection=anime_collection)


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


@blueprint.route("/<int:id>/details", methods=["GET", "POST"])
@login_required
def details(id):
    """Get more details about an anime's different releases.
    The info is first retrieved through the AnimeNewsNetwork (ANN) API, then is
    stored in the database for any successive searches.
    """

    # Get connection to database
    database = get_database()

    # Keep track of any errors that may occur
    error = None

    # Retrieve anime data from the anime_releases table
    anime_data = database.execute("SELECT * FROM anime_releases WHERE anime_id = ?",
                                  [id]).fetchall()

    # Create list to store data about the anime's different releases
    releases = []

    # If anime data is not in anime_releases yet, retrieve the anime's info from the ANN API
    if not anime_data:
        # Call ANN API
        releases = retrieve_anime_data(database, id)

    # Otherwise, use the data retrieved from the database
    else:
        for release in anime_data:
            # Convert release data from database into a dict
            release = dict(release)

            # Generate link to the release's page on ANN based on its release_id
            release["link"] = f"https://www.animenewsnetwork.com/encyclopedia/releases.php?id={release.get('release_id')}"

            # Add release data to list of releases
            releases.append(release)

    # Display message if a show has no releases
    if not releases:
        title = database.execute("SELECT title FROM anime_shows WHERE anime_id = ?",
                                 [id]).fetchone()["title"]

        error = f"{title} has no releases."

        flash(error)

    # Display list of releases
    return render_template("collection/details.html", releases=releases)


def retrieve_anime_data(database, id):
    """Use the AnimeNewsNetwork API to retrieve data about an anime
    based on its id.
    """

    # Get info from the AnimeNewsNetwork API XML url
    with urllib.request.urlopen(f"https://cdn.animenewsnetwork.com/encyclopedia/api.xml?anime={id}") as response:
        xml = response.read()

    # Parse XML file obtained from the ANN API
    root = ET.fromstring(xml)

    # Get the anime element from the XML file
    anime = root.find("anime")

    # Create list to store data on the anime's releases
    releases = []

    # Get data on all the different releases found in the XML file for that anime's data
    for release in anime.findall("release"):
        anime_id = id
        link = release.get("href")
        release_date = release.get("date")
        release_id = link[link.find("=") + 1:]
        release_title = release.text

        # Generate link to release's image from its ANN page
        image = f"https://cdn.animenewsnetwork.com/thumbnails/area200x300/releases/{release_id}.jpg"

        # Release's disc type is always at the end of the release_title, inside
        # of parentheses. This regex extracts the type from the title
        type = re.findall("\(([^)]+)", release_title)[-1]

        # Check for release being a special edition
        if "edition" in release_title.lower():
            # Get substring that comes before the word "edition" in the release_title
            title = release_title.lower().split("edition")[0]

            # Split first substring into different words
            title = title.split()

            # Get the last word from the list, which is that release's edition type
            edition = title[-1]

            # Remove first character of word if it's not a letter
            if not edition[0].isalpha():
                edition = edition[1:]

            # Capitalize the word
            edition = edition.capitalize()

            # Maintain consistency in spelling of "Collector's Edition"
            if edition == "Collectors":
                edition = "Collector's"

        # If release is not any kind of special edition, then default to "Standard"
        else:
            edition = "Standard"

        # Create dict of anime data
        release_info = {"anime_id": anime_id,
                        "edition": edition,
                        "image": image,
                        "link": link,
                        "release_date": release_date,
                        "release_id": release_id,
                        "release_title": release_title,
                        "type": type}

        # Add release to list of releases
        releases.append(release_info)

        # Insert anime data into database to avoid having to call API each time
        database.execute("INSERT INTO anime_releases (release_id, anime_id, release_title, disc_type, edition, release_date, image) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?)",
                        [release_id, anime_id, release_title, type, edition, release_date, image])
        database.commit()

    return releases


@blueprint.route("/add")
@login_required
def add():
    """Add anime release to anime collection."""

    # Get query parameters
    release_id = request.args.get("release_id")
    anime_id = request.args.get("anime_id")

    # Get connection to database
    database = get_database()

    # Keep track of any errors that may occur
    error = None

    # Insert release into anime_collections database for a user's collection
    try:
        database.execute("INSERT INTO anime_collections (user_id, anime_id, release_id) "
                        "VALUES (?, ?, ?)",
                        [g.user["user_id"], anime_id, release_id])
        database.commit()
    # Display error if release has already been added to user's collection
    except database.IntegrityError:
        anime = database.execute("SELECT release_title FROM anime_releases WHERE release_id = ?",
                                 [release_id]).fetchone()["release_title"]
        error = f"{anime} is already in your collection."

        flash(error)

        return redirect(url_for("collection.details", id=anime_id))

    # Redirect to homepage to show user's anime collection
    return redirect(url_for("collection.edit", release_id=release_id))


@blueprint.route("/<int:release_id>/edit", methods=["GET", "POST"])
@login_required
def edit(release_id):
    """Edit anime information for a release added to user's collection."""

    # Get connection to database
    database = get_database()

    # User reached view via a POST request
    if request.method == "POST":

        # Get user data submission
        price_bought = request.form.get("price-bought")
        date_bought = request.form.get("date-bought")
        comment = request.form.get("comment")

        # Format date into mm/dd/yyyy format
        date_bought = format_date(date_bought)

        # Insert user submitted information for anime collection into database
        database.execute("UPDATE anime_collections "
                         "SET price_bought = ?, date_bought = ?, comment = ? "
                         "WHERE user_id = ? AND release_id = ?",
                         [price_bought, date_bought, comment, g.user["user_id"], release_id])
        database.commit()

        return redirect(url_for("index"))

    # Keep track of any errors that may occur
    error = None

    # Create dict to store information about anime release
    release = {}

    # Get information about anime in collection from database
    release["release_title"] = database.execute("SELECT release_title "
                                                "FROM anime_releases "
                                                "WHERE release_id = ?",
                                                [release_id]).fetchone()["release_title"]

    release_info = database.execute("SELECT price_bought, date_bought, comment "
                                    "FROM anime_collections "
                                    "WHERE release_id = ?",
                                    [release_id]).fetchone()

    release["price_bought"] = release_info["price_bought"]
    release["date_bought"] = release_info["date_bought"]
    release["comment"] = release_info["comment"]

    return render_template("collection/edit.html", release=release)


@blueprint.route("/remove")
@login_required
def remove():
    """Remove anime release from anime collection."""

    # Get query parameters
    release_id = request.args.get("release_id")

    # Get connection to database
    database = get_database()

    # Remove anime release from the user's collection
    database.execute("DELETE FROM anime_collections WHERE user_id = ? AND release_id = ?",
                     [g.user["user_id"], release_id])
    database.commit()

    # Redirect back to homepage to show user's updated anime collection
    return redirect(url_for("index"))


def format_date(date):
    """Format date from yyyy-mm-dd to mm/dd/yyyy."""

    # Separate date from format of yyyy-mm-dd into list holding year, month, and day
    date = date.split("-")

    # Swap location of year from beginning to end of list
    year = date.pop(0)
    date.append(year)

    # Join elements of list with / as a separator
    date = "/".join(date)

    return date
