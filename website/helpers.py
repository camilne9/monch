import os
import requests
import urllib.parse

from datetime import datetime
from cs50 import SQL
from flask import redirect, render_template, request, session
from functools import wraps

db = SQL("sqlite:///monch.db")


def apology(message, userhouse, code=400):
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
    if userhouse is None:
        return render_template("apology.html", top=code, bottom=escape(message)), code
    else:
        return render_template("apology.html", top=code, bottom=escape(message), house=userhouse), code


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


def checkIfDuplicates(listOfElems):
    ''' Check if given list contains any duplicates '''
    # This helper function checks in there are any dublicates in a list. set() removes any duplicates so if the lengths of the list
    # with and without the set() function are the same then there are no duplicates and otherwise there are duplicates.
    if len(listOfElems) == len(set(listOfElems)):
        return False
    else:
        return True


def order_by_preference(list_of_strings):
    # This function takes a list of strings that we will order.
    user_id = session["user_id"]
    # First we get the user_id from the session. (If there is not user, there are no preferences so we cannot order the list
    # so we need not consider that case.)
    if len(list_of_strings) == 0:
        return list_of_strings
    # If the given list is empty, there is no ordering to do so we return the empty list.
    houses = db.execute(f"SELECT house FROM dhallpreferences WHERE user_id IS {user_id} ORDER BY rank")
    # Here we generate a dictionary from the database that has all of the houses listed in order of their rank.
    # We use the user_id to ensure we are only looking at the user's preferences specifically.
    houses2 = []
    # We will store the houses in a list so we initialize an empty list for storage.
    for house in houses:
        houses2.append(house["house"])
        # We loop through the dictionary and place all of the house names in python list.
        # We have now effectively created a list of the user's preferences in order. Now we need to isolate the houses that
        # are actually open to the user by comparing to list_of_strings
    names = []
    # Again we create a list for storage.
    for house in houses2:
        if house == "First-Year" and "Annenberg" in list_of_strings:
            names.append("Annenberg")
            # This resolves the difference is the naming of the freshman dhall vs the freshman student.
        elif house in list_of_strings:
            names.append(house)
            # We append the list with all of the houses that are open to them, but the order is preserved so we have reordered the dhalls.
    if len(names) == 0:
        # If names is empty then the user must have put in no preferences (because we already verified that list_of_strings is not empty).
        # In this case we have no basis for ordering the houses, so we simply return the houses in alphabetical order.
        list_of_strings.sort(key=str.lower)
        return list_of_strings
    return names
    # We return the ordered list of open houses.


def get_current_value():
    now = datetime.now()
    # Here we get the current timestamp.
    hour = now.hour
    minute = now.minute
    # Here we find the hour and minute of the current timestamp for the sake of converting this time to
    # a time "value" of the same form as the times values in our SQL database "all_days".
    value = ((hour-5) % 24)*60 + minute
    # The value is the number of minutes into the day we are, so mulitply hours by 60 and add the minutes. Also we subtract 5 from hours
    # because timestamp gives the time in England and we want the time in cambridge so we shift it 5 hours. Since we want to be able to handle
    # negative values from the -5, we take the difference mod 24.
    return value


def current_time():
    now = datetime.now()
    minute = now.minute
    hour = (now.hour - 5) % 24
    # Here we get the current timestamp and we isolate the minute and the hour.
    # Since the timestamp is for England, we adjust it to Cambridge MA time by subracting 5 and we resolve the
    # potential for negative numbers by taking mod 24.
    pm = False
    if hour > 12:
        hour = hour - 12
        pm = True
        # Since the time is "military time", pm times have hours greater than 12. To match normal time conventions, we subtract 12 to
        # get the normal pm hour and indicate that it is pm.
    if hour == 12:
        pm = True
    if minute < 10:
        # To deal with the missing 0 of single digit minutes, we handle this case separately.
        if pm:
            return str(f"{hour}:0{minute} P.M.")
        else:
            return str(f"{hour}:0{minute} A.M.")
        # Here we return the formated string with the hour minute and either AM or PM depending on whether pm is True.
    if pm:
        return str(f"{hour}:{minute} P.M.")
    else:
        return str(f"{hour}:{minute} A.M.")
        # In the case where the minute is two digits we apply the same strategy without the extra 0.


def current_day():
    weekdays = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
    # We create a list of the weekdays.
    day = datetime.today().strftime("%A").lower()
    # This stores the current day of the week as a string. We cast it to lowercase for consistency.
    if get_current_value() >= 1140:
        # Since the timestamp is for England, if it is after 7pm then the day will be wrong so we need to go back a day.
        # (Otherwise day is all we want.)
        index = weekdays.index(day)
        # Here we find the index in the weekdays list that is is in england.
        index2 = (index - 1) % 7
        # Since England is ahead, we subtract 1 to get the actual index. We take mod 7 to avoid negatives when we go back to saturday.
        day = weekdays[index2]
        # We set day equal to the value in weekddays 1 day prior.
    return day
    # We retrun the day of the week.