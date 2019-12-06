import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
# here we load all of the necessary packages for the code

from helpers import apology, login_required, lookup, usd, checkIfDuplicates, order_by_preference, get_current_value, current_time, current_day
# This allows us to all any of the helper functions from helpers.py

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///monch.db")

houses = {"Adams", "Cabot", "Currier", "Dunster", "Eliot", "Kirkland", "Leverett",
          "Lowell", "Mather", "Pforzheimer", "Quincy", "Winthrop", "First-Year"}


@app.route("/")
def index():
    """ Homepage """
    # If currently no user, we will show all of the houses currently open and if there is a user then we will show all of the houses open to the user.
    time = get_current_value()
    currenttime = current_time()
    day_of_week = current_day()
    # Here we use our helper functions to get the current time, the current time value, and the current day of the week.
    houses = db.execute(f"SELECT house FROM all_days WHERE {time} >= start_time AND {time} <= end_time")
    # here we generate a dictionary of the houses that are open at the current time by querying into our database.
    if session.get("user_id") is None:
        # in the case where there is no user, we have no restrictions or preferences to worry about, we need only worry about what dhalls are open.
        output = []
        # we are going to pull the values from the dictionary houses and store them in a list so first we initialize an empty list
        for row in houses:
            # we loop through all of the entries in houses.
            if row["house"] == "freshman":
                output.append("Annenberg")
                # since the freshman dhall is called "Annenberg", if the house is freshman, we append the list with the dhall name.
            else:
                output.append(row["house"].capitalize())
                # Since all the upperclassman dhalls can be references with the house name, we simply append the list with the house
                # name, which we capitalize for better aesthetic.
        if len(output) == 0:
            output.append("None")
            # if the length of output is 0, then none of the dhalls are open so we add the word None to the list so that the html output will
            # indicate to the user that none of the houses are open rather than just having an uninformative blank space.
        output.sort(key=str.lower)
        return render_template("test.html", houses=output, time=currenttime, day=day_of_week.capitalize())
        # We render the desired html template to show the information we just collected. We pass the information to the rendering so that we can use
        # it in the html.
    else:
        # This else case handles the situation when there is a user, so we need to think about restrictions and preferences.
        user = db.execute("SELECT * FROM users WHERE id=:userid", userid=session["user_id"])
        # here we get the information about the user from the users SQL database.
        houses = db.execute(
            f"SELECT DISTINCT * FROM restrictions WHERE restriction_id IN (SELECT {day_of_week} FROM all_days WHERE {time} >= start_time AND {time} <= end_time)")
        output = []
        for row in houses:
            if row["open_to"] == user[0]["house"]:
                if row["house_in_question"] == "freshman":
                    output.append("Annenberg")
                else:
                    output.append(row["house_in_question"].capitalize())
        output2 = order_by_preference(output)
        if len(output) == 0:
            output.append("None")
            # if the length of output is 0, then none of the dhalls are open so we add the word None to the list so that the html output will
            # indicate to the user that none of the houses are open rather than just having an uninformative blank space.
        return render_template("test.html", username=user[0]["username"], house=user[0]["house"].capitalize(), houses=output, time=currenttime, day=day_of_week.capitalize())
        # We render the desired html template to show the information we just collected. We pass the information to the rendering so that we can use
        # it in the html.


@app.route("/inputtime", methods=["GET", "POST"])
@login_required
def inputtime():
    valid_hours = list(range(1, 13))
    # the hour can be any integer from 1 to 12 so we create a list of these values.
    valid_minutes = list(range(0, 60))
    # the minute can be any integer from 0 to 59 so we create a list of these values.
    valid_days = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
    # here we create a list of the possible days of the week.
    # We will pass these lists to the html we render to have these lists supply the possibilities in drop down menus.
    user = db.execute("SELECT * FROM users WHERE id=:userid", userid=session["user_id"])
    if request.method == "POST":
        # here we are looking at the case where the form is being submitted, ie the user has input a day they are interested in.
        if request.form.get("Hour") == None:
            return apology("Not a valid time")
        if request.form.get("Minute") == None:
            return apology("Not a valid time")
        if request.form.get("Meridia") == None:
            return apology("Not a valid time")
        if request.form.get("Day") == None:
            return apology("Not a valid day")
        # The above "if" statements verify that the user filled out all of the fields necessary to indicate a particular time and day.
        # In the event that the user left one of the fields blank, we supply an apology indicating the mistake made.
        hour = int(request.form.get("Hour"))
        minute = int(request.form.get("Minute"))
        day_of_week = request.form.get("Day")
        # Since we know the user input values in the fields, we store the inputs as variables so that we can call them more easily later.
        if request.form.get("Meridia") == "AM":
            value = (60*(hour % 12)) + minute
        else:
            value = 60 * ((hour % 12) + 12) + minute
        # In this if-else case we are converting the time input by the user to an integer for the sake of comparing it to the integers that represent
        # the start and end times of the dhall windows so that we can find the open dhalls in our query later. If the time is AM we think of the hour
        # as a number from 0 to 11 and otherwise we think of the hour in terms of its military time representation by adding 12. We use the mod 12 to
        # made 12am be hour 0.
        user_id = session["user_id"]
        # Here we store the user_id for the same of being able to query on it.
        user = db.execute(f"SELECT * FROM users WHERE id IS {user_id}")
        # We query into users database to find out everything we know about the user.
        user_house = user[0]["house"]
        # From the output of the above query, we draw out the users house so we know the users restrictions.
        houses = db.execute(
            f"SELECT DISTINCT * FROM restrictions WHERE restriction_id IN (SELECT {day_of_week} FROM all_days WHERE {value} >= start_time AND {value} <= end_time )")
        # Here we first collect all of the restriction numbers from the all_days databases where the time is in the entry window and the column is named for the day
        # of the week. Then we collect all of the distinct rows from restrictions where the restriction_id is in that set of restriction ids.
        output = []
        # we initialize an empty list in which to store the open houses.
        for row in houses:
            if row["open_to"] == user_house:
                # if the row indicates that the house is open to the user's house, then we will add the house in that row to the list.
                if row["house_in_question"] == "freshman":
                    output.append("Annenberg")
                    # As explained previously, the naming scheme for freshman is unusual, so we handle this case separately in adding it to
                    # the list of open houses.
                else:
                    output.append(row["house_in_question"].capitalize())
                    # if the house is not freshman, we add the capitalized house name to the list.
        if len(output) == 0:
            output = ["None"]
            # if the length of output is 0, then none of the dhalls are open so we add the word None to the list so that the html output will
            # indicate to the user that none of the houses are open rather than just having an uninformative blank space.
        return render_template("open.html", houses=order_by_preference(output), house=user[0]["house"].capitalize())
        # We render the desired html template to show the information we just collected. We pass the information to the rendering so that we can use
        # it in the html.
    else:
        # This else case means the user is trying to open the page rather than try to submit it.
        return render_template("arbitrary_time.html", valid_days=valid_days, valid_hours=valid_hours, valid_minutes=valid_minutes, house=user[0]["house"].capitalize())
        # We render the html that will prompt the user for the inputs. We pass the html the necessary variables for the drop down menus for the inputs.


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("loginmonch.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/createaccount", methods=["GET", "POST"])
def createaccount():
    if request.method == "POST":
        # if we are potsing, we get the output of the lookup function and store it.
        house = request.form.get("house")
        if house == "First-Year":
            house = "Freshman"
        house = house.lower()
        if house:
            # if the lookup doesn't return none, we use the lookup output to generate values that will allow us to update the necessary data.
            name = request.form.get("username")
            password = request.form.get("password")
            # Catch empty entries.
            if not request.form.get("username"):
                return apology("must provide username", 403)
            if not request.form.get("password"):
                return apology("must provide password", 403)
            users = db.execute(f"SELECT * FROM users WHERE username = :name", name=name)
            # Catch repeat usernames.
            if len(users) != 0:
                return apology("username already in use. Choose another.", 403)
            # Make sure confirmed passwords match
            if request.form.get("password") != request.form.get("confirmpassword"):
                return apology("passwords must match", 403)
            else:
                # Hash password and insert user into table.
                passwordhash = generate_password_hash(password)
                db.execute(f"INSERT INTO users (username,hash,house) VALUES(:username, :passwordhash, :house)",
                           username=name, passwordhash=passwordhash, house=house)
                user = db.execute(f"SELECT * FROM users WHERE username=:name", name=name)
                return redirect("/")
        else:
            return apology("must select house")
            # This else case means the user didn't select a house from the drop down menu so we return an apology explaining this.
    else:
        return render_template("createaccount.html", houses=houses)
        # This "else" case means the user is trying to


@app.route("/dhallranks", methods=["GET", "POST"])
@login_required
def dhallranks():
    """Sell shares of stock"""
    user = db.execute("SELECT * FROM users WHERE id=:userid", userid=session["user_id"])
    if request.method == "POST":
        # When we get preferences submitted we delete the old preferences first.
        db.execute("DELETE FROM dhallpreferences WHERE user_id=:userid", userid=user[0]["id"])
        # Below we store all the preferences in a python list.
        preferences = []
        for i in range(13):
            entry = request.form.get(f"pref{i+1}")
            preferences.append(f"{entry}")
        # Catch empty entries.
        if len(preferences) != 13:
            return apology("Empty rank")
        # Check for duplicates.
        if checkIfDuplicates(preferences):
            return apology("Cannot repeat Dining Halls")
        # We add the preferences to the SQL database.
        for j in range(13):
            db.execute(f"INSERT INTO dhallpreferences (user_id,house,rank) VALUES(:userid,:house,:rank)",
                       userid=user[0]["id"], house=preferences[int(j)], rank=int(j+1))
        # Redirect to homepage.
        return redirect("/")
    else:
        # If get method, we load the dhallranks page with the relevant variables.
        return render_template("dhallranks.html", houses=houses, house=user[0]["house"].capitalize())


@app.route("/passwordchange", methods=["GET", "POST"])
@login_required
def passwordchange():
    user = db.execute("SELECT * FROM users WHERE id=:userid", userid=session["user_id"])
    if request.method == "POST":
        # Catch invalid entries.
        if not request.form.get("oldpassword"):
            return apology("Must enter old password", 403)
        if not request.form.get("newpassword"):
            return apology("Must enter new password", 403)
        user = db.execute("SELECT * FROM users WHERE id = :userid", userid=session["user_id"])
        if not check_password_hash(user[0]["hash"], request.form.get("oldpassword")):
            return apology("Incorrect old password")
        if check_password_hash(user[0]["hash"], request.form.get("newpassword")):
            return apology("New password can't be old password")
        # Alter password hash in table.
        else:
            db.execute("UPDATE users SET hash = :passwordhash WHERE id = :userid",
                       passwordhash=generate_password_hash(request.form.get("newpassword")), userid=session["user_id"])
            return redirect("/")
    else:
        return render_template("passwordchange.html", house=user[0]["house"].capitalize())


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
