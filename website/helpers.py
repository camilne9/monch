import os
import requests
import urllib.parse

from datetime import datetime
from cs50 import SQL
from flask import redirect, render_template, request, session
from functools import wraps

db = SQL("sqlite:///monch.db")

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(symbol):
    """Look up quote for symbol."""

    # Contact API
    try:
        api_key = os.environ.get("API_KEY")
        response = requests.get(f"https://cloud-sse.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/quote?token={api_key}")
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        quote = response.json()
        return {
            "name": quote["companyName"],
            "price": float(quote["latestPrice"]),
            "symbol": quote["symbol"]
        }
    except (KeyError, TypeError, ValueError):
        return None


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"

def checkIfDuplicates(listOfElems):
    ''' Check if given list contains any duplicates '''
    if len(listOfElems) == len(set(listOfElems)):
        return False
    else:
        return True

def order_by_preference(list_of_strings):
    user_id = session["user_id"]
    if len(list_of_strings) == 0:
        return list_of_strings
    for house in list_of_strings:
        houses = db.execute(f"SELECT house FROM dhallpreferences WHERE user_id IS {user_id} ORDER BY rank")
    names = []
    for house in houses:
        names.append(house["house"])
    if len(names) == 0:
        return list_of_strings
    return names

def get_current_value():
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    value = ((hour-5)%24)*60 + minute
    return value