from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from mac.auth import login_required
from mac.db import get_database

blueprint = Blueprint("collection", __name__)
