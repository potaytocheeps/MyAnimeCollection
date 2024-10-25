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


@blueprint.before_app_request
def load_logged_in_user():
    """If user's id is stored in session, load user object from database
    into ``g.user``."""

    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
    else:
        g.user = get_database().execute(
            "SELECT * FROM users WHERE id = ?",
            [user_id]
        ).fetchone()


def login_required(view):
    """View decorator that requires users to be logged in to access the views
    to which this decorator is applied."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        # Redirect to login view if user is not logged in
        if g.user is None:
            return redirect(url_for("auth.login"))

        # Continue to request view normally
        return view(**kwargs)

    return wrapped_view


@blueprint.route("/register", methods=["GET", "POST"])
def register():
    """Registers users in database."""

    # User reached this view via a POST request, by submitting a form
    if request.method == "POST":
        # Get user data submission
        username = request.form.get("username")
        password = request.form.get("password")
        password_confirmation = request.form.get("password-confirmation")

        # Get connection to database
        database = get_database()

        # Keep track of any errors that may occur during user registration
        error = None

        # Ensure user submitted data
        if not username:
            error = "Username is required."
        elif not password:
            error = "Password is required."
        elif not password_confirmation:
            error = "Password confirmation is required."

        # Ensure that password and its confirmation match
        if password != password_confirmation:
            error = "Password and its confirmation do not match."

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


@blueprint.route("/login", methods=["GET", "POST"])
def login():
    """Log in registered user by adding their id to the session."""

    # User reached this view via submitting a form
    if request.method == "POST":
        # Get user data submission
        username = request.form.get("username")
        password = request.form.get("password")

        # Get connection to database
        database = get_database()

        # Track any errors that may occur during user log in
        error = None

        # Get user data from the database, based on submitted username
        user = database.execute("SELECT *"
                                "FROM users"
                                "WHERE username = ?",
                                [username]).fetchone()

        # Check that username exists and password is correct
        if user is None or not check_password_hash(user["password"], password):
            error = "Username or password is incorrect."

        # Create new user session on successful login and return to index page
        if error is None:
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for("index"))

        # Store any errors that may have occurred during log in
        flash(error)

    # Display login form for a GET request
    return render_template("auth.login.html")


@blueprint.route("/logout")
def logout():
    """Log user out by removing their id from session."""

    session.clear()
    return redirect(url_for("index"))
