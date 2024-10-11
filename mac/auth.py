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
