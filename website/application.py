import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd, checkIfDuplicates, order_by_preference, get_current_value

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


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///monch.db")

# Make sure API key is set
#if not os.environ.get("API_KEY"):
#    raise RuntimeError("API_KEY not set")

houses = {"Adams","Cabot","Currier","Dunster","Eliot","Kirkland","Leverett","Lowell","Mather","Pforzheimer","Quincy","Winthrop","First-Year"}


@app.route("/")
def index():
    """ Homepage """
    # If currently no user, show login page.
    # Show stocks and cashremaining for user.
    time = get_current_value()
    print(f"{time}")
    houses = db.execute(f"SELECT house FROM new_generic_day WHERE {time} >= start_time AND {time} <= end_time")
    if session.get("user_id") is None:
        output = []
        for row in houses:
            if row["house"]=="freshman":
                output.append("Annenberg")
            else:
                output.append(row["house"].capitalize())
        if len(output) == 0:
            output.append("None")
        return render_template("test.html", houses = output)
    else:
        user = db.execute("SELECT * FROM users WHERE id=:userid", userid=session["user_id"])
        houses = db.execute(f"SELECT DISTINCT * FROM restrictions WHERE restriction_id IN (SELECT restriction_id FROM new_generic_day WHERE {time} > start_time AND {time} < end_time)")
        output = []
        for row in houses:
            if row["open_to"]==user[0]["house"]:
                if row["house_in_question"]=="freshman":
                    output.append("Annenberg")
                else:
                    output.append(row["house_in_question"].capitalize())
        output = order_by_preference(output)
        if len(output) == 0:
            output.append("None")
        return render_template("test.html", username=user[0]["username"], house=user[0]["house"].capitalize(), houses=output)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        # Catch empty requests.
        if not request.form.get("numofstocks"):
            return apology("Must enter number of stocks", 403)
        elif not request.form.get("corpcode"):
            return apology("Must enter stock symbol", 403)
        stock = request.form.get("corpcode")
        numofstocks = request.form.get("numofstocks")
        # Catch non-positive stock numbers.
        if int(numofstocks) <= 0:
            return apology("Must buy positive number of stocks")
        stockvalue = lookup(stock)
        # Catch invalid stock symbols.
        if len(stockvalue) == 0:
            return apology("Invalid symbol", 403)
        user = db.execute(f"SELECT * FROM users WHERE id = :userid", userid=session["user_id"])
        cashremaining = user[0]["cash"] - (float(numofstocks) * stockvalue["price"])
        # Catch if enough money is available for transaction.
        if cashremaining < 0:
            return apology("Not enough cash for transaction", 403)
        db.execute(f"UPDATE users SET cash = :cashremaining WHERE id = :userid", cashremaining=cashremaining, userid=user[0]["id"])
        stocks = db.execute(f"SELECT * FROM stocks WHERE Stock = :stock AND user_id=:userid", stock=stock, userid=user[0]["id"])
        # Make new table entry if no stocks from company owned, update otherwise.
        if len(stocks) == 0:
            db.execute(f"INSERT INTO stocks (user_id, Stock, NumOfStocks, StockValue, TotalValue) VALUES(:userid, :stock, :numofstocks, :stockvalue, :totalvalue)",
                       userid=user[0]["id"], stock=stock, numofstocks=numofstocks, stockvalue=stockvalue["price"], totalvalue=(float(numofstocks)*stockvalue["price"]))
        else:
            db.execute(f"UPDATE stocks SET NumOfStocks = :number WHERE Stock = :stock AND user_id=:userid",
                       number=int(numofstocks)+int(stocks[0]["NumOfStocks"]), stock=stock, userid=user[0]["id"])
            db.execute(f"UPDATE stocks SET TotalValue = :value WHERE Stock = :stock AND user_id=:userid", value=(
                (float(numofstocks)+stocks[0]["NumOfStocks"])*stockvalue["price"]), stock=stock, userid=user[0]["id"])
            db.execute(f"UPDATE stocks SET StockValue = :stockvalue WHERE Stock = :stock",
                       stockvalue=stockvalue["price"], stock=stock)
        # Add to history table.
        db.execute(f"INSERT INTO history (user_id, boughtsold, Stock, NumOfStocks, StockValue, TotalValue, cashremaining) VALUES(:userid, 'bought', :stock, :numofstocks, :stockvalue, :totalvalue, :cashremaining)",
                   userid=user[0]["id"], stock=stock, numofstocks=int(numofstocks), stockvalue=stockvalue["price"], totalvalue=(float(numofstocks))*stockvalue["price"], cashremaining=cashremaining)
        return redirect("/")
    else:
        return render_template("buy.html")


@app.route("/inputtime", methods=["GET", "POST"])
@login_required
def inputtime():
    valid_hours = list(range(1, 13))
    valid_minutes = list(range(0, 60))
    user = db.execute("SELECT * FROM users WHERE id=:userid", userid=session["user_id"])
    if request.method == "POST":
        hour = int(request.form.get("Hour"))
        minute = int(request.form.get("Minute"))
        #if request.form.get("Hour") == None or request.form.get("Minute") == None or request.form.get("AM/PM") == None:
        #    return apology("Not a valid time")
        if request.form.get("Meridia") == "AM":
            value = (60*(hour % 12)) + minute
        else:
            value = 60 * ((hour % 12) + 12) + minute
        user_id = session["user_id"]
        user = db.execute(f"SELECT * FROM users WHERE id IS {user_id}")
        user_house = user[0]["house"]
        houses = db.execute(f"SELECT DISTINCT * FROM restrictions WHERE restriction_id IN (SELECT restriction_id FROM new_generic_day WHERE {value} > start_time AND {value} < end_time )")
        output = []
        for row in houses:
            if row["open_to"]==user_house:
                if row["house_in_question"]=="freshman":
                    output.append("Annenberg")
                else:
                    output.append(row["house_in_question"].capitalize())
        return render_template("open.html", houses=order_by_preference(output), house=user[0]["house"].capitalize())
    else:
        return render_template("arbitrary_time.html", valid_hours = valid_hours, valid_minutes = valid_minutes, house=user[0]["house"].capitalize())


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
    else:
        return render_template("createaccount.html",houses=houses)


@app.route("/dhallranks", methods=["GET", "POST"])
@login_required
def dhallranks():
    """Sell shares of stock"""
    user = db.execute("SELECT * FROM users WHERE id=:userid", userid=session["user_id"])
    if request.method == "POST":
        db.execute("DELETE FROM dhallpreferences WHERE user_id=:userid",userid=user[0]["id"])
        preferences = []
        for i in range(13):
            entry = request.form.get(f"pref{i+1}")
            preferences.append(f"{entry}")
        # Catch empty entries.
        if len(preferences)!=13:
            return apology("Empty rank")
        # Check for duplicates.
        if checkIfDuplicates(preferences):
            return apology("Cannot repeat Dining Halls")
        for j in range(13):
            db.execute(f"INSERT INTO dhallpreferences (user_id,house,rank) VALUES(:userid,:house,:rank)",userid=user[0]["id"],house=preferences[int(j)],rank=int(j+1))
        return redirect("/")
    else:
        return render_template("dhallranks.html", houses=houses, house=user[0]["house"].capitalize())


        #stock = request.form.get("corpcode")
        #numofstocks = request.form.get("numofstocks")
        #row = db.execute("SELECT * FROM stocks WHERE Stock=:stock AND user_id=:userid", stock=stock, userid=session["user_id"])
        # Check to see if stocks are owned.
        #if len(row) == 0:
        #    return apology("Can only sell stocks you own")
        # Catch negative entries.
        #if int(numofstocks) <= 0:
        #    return apology("Must sell positive number of stocks")
        # Can only sell up to number of stocks owned.
        #num2 = row[0]["NumOfStocks"]
        #print(f"{num2}")
        #if int(numofstocks) > row[0]["NumOfStocks"]:
        #    return apology("Attempt to sell more stocks than owned")
        #stockvalue = lookup(stock)
        #user = db.execute(f"SELECT * FROM users WHERE id = :userid", userid=session["user_id"])
        #cashremaining = user[0]["cash"] + (float(numofstocks) * stockvalue["price"])
        #stocks = db.execute(f"SELECT * FROM stocks WHERE user_id = :userid AND Stock=:stock",
        #                    userid=session["user_id"], stock=stock)
        # Update cash for user.
        #db.execute(f"UPDATE users SET cash = :cashremaining WHERE id = :userid", cashremaining=cashremaining, userid=user[0]["id"])
        #number = int(stocks[0]["NumOfStocks"])-int(numofstocks)
        # Get rid of stock entry if no more stocks from that company owned.
        #if number == 0:
        #    db.execute(f"DELETE FROM stocks WHERE user_id=:userid AND Stock=:stock", userid=user[0]["id"], stock=stock)
        # Update stocks for user.
        #else:
        #    db.execute(f"UPDATE stocks SET NumOfStocks = :number WHERE Stock = :stock AND user_id=:userid",
        #               number=number, stock=stock, userid=user[0]["id"])
        #db.execute(f"INSERT INTO preferences (user_id, boughtsold, Stock, NumOfStocks, StockValue, TotalValue, cashremaining) VALUES(:userid, 'sold', :stock, :numofstocks, :stockvalue, :totalvalue, :cashremaining)",
        #           userid=user[0]["id"], stock=stock, numofstocks=int(numofstocks), stockvalue=stockvalue["price"], totalvalue=(float(numofstocks)*stockvalue["price"]), cashremaining=cashremaining)
        #return redirect("/")

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
