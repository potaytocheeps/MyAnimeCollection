# Authentication blueprint and views set up taken directly from:
# https://flask.palletsprojects.com/en/3.0.x/tutorial/views/

import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from mac.db import get_database

# Create "auth" blueprint for user authentication
blueprint = Blueprint("auth", __name__, url_prefix="/auth")


@blueprint.route("/register", methods=["GET", "POST"])
def register():
    """Registers users in database."""

    # User reached this view via a POST request, by submitting a form
    if request.method == "POST":
        # Get user data submission
        username = request.form.get("username")
        password = request.form.get("password")

        # Get connection to database
        database = get_database()

        # Keep track of any errors that may occur during user registration
        error = None

        # Ensure user submitted data
        if not username:
            error = "Username is required."
        elif not password:
            error = "Password is required."

        # If user submitted data successfully, register the user in the database
        if error is None:
            try:
                database.execute(
                    "INSERT INTO users (username, password) VALUES (?, ?)",
                    [username, generate_password_hash(password)]
                )
                database.commit()
            except database.IntegrityError:
                error = f"User {username} is already registered."
            else:
                return redirect(url_for("auth.login"))

        # Store any errors that may have occurred during registration
        flash(error)

    # Render registration form
    return render_template("auth/register.html")
