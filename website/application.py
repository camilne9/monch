import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

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
    if session.get("user_id") is None:
        return render_template("test.html")
    else:
        user = db.execute("SELECT * FROM users WHERE id=:userid", userid=session["user_id"])
        return render_template("test.html", username=user[0]["username"], house=user[0]["house"])


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


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    userid = session["user_id"]
    # Retrieve stock history for the user.
    rows = db.execute(f"SELECT * FROM history WHERE user_id = :userid", userid=userid)
    user = db.execute(f"SELECT * FROM users WHERE id = :user_id", user_id=session["user_id"])
    for row in rows:
        row["StockValue"] = usd(row["StockValue"])
        row["TotalValue"] = usd(row["TotalValue"])
        row["cashremaining"] = usd(row["cashremaining"])
    return render_template("history.html", rows=rows, cashremaining=usd(user[0]["cash"]))


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
        print(f"{house}")
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
            return redirect("/")
        else:
            return apology("must select house")
    else:
        return render_template("createaccount.html",houses=houses)


@app.route("/dhallranks", methods=["GET", "POST"])
@login_required
def dhallranks():
    """Sell shares of stock"""
    if request.method == "POST":
        # Catch empty entries.
        if not request.form.get("numofstocks"):
            return apology("Must enter number of stocks", 403)
        elif not request.form.get("corpcode"):
            return apology("Must enter stock symbol", 403)
        stock = request.form.get("corpcode")
        numofstocks = request.form.get("numofstocks")
        row = db.execute("SELECT * FROM stocks WHERE Stock=:stock AND user_id=:userid", stock=stock, userid=session["user_id"])
        # Check to see if stocks are owned.
        if len(row) == 0:
            return apology("Can only sell stocks you own")
        # Catch negative entries.
        if int(numofstocks) <= 0:
            return apology("Must sell positive number of stocks")
        # Can only sell up to number of stocks owned.
        num2 = row[0]["NumOfStocks"]
        print(f"{num2}")
        if int(numofstocks) > row[0]["NumOfStocks"]:
            return apology("Attempt to sell more stocks than owned")
        stockvalue = lookup(stock)
        user = db.execute(f"SELECT * FROM users WHERE id = :userid", userid=session["user_id"])
        cashremaining = user[0]["cash"] + (float(numofstocks) * stockvalue["price"])
        stocks = db.execute(f"SELECT * FROM stocks WHERE user_id = :userid AND Stock=:stock",
                            userid=session["user_id"], stock=stock)
        # Update cash for user.
        db.execute(f"UPDATE users SET cash = :cashremaining WHERE id = :userid", cashremaining=cashremaining, userid=user[0]["id"])
        number = int(stocks[0]["NumOfStocks"])-int(numofstocks)
        # Get rid of stock entry if no more stocks from that company owned.
        if number == 0:
            db.execute(f"DELETE FROM stocks WHERE user_id=:userid AND Stock=:stock", userid=user[0]["id"], stock=stock)
        # Update stocks for user.
        else:
            db.execute(f"UPDATE stocks SET NumOfStocks = :number WHERE Stock = :stock AND user_id=:userid",
                       number=number, stock=stock, userid=user[0]["id"])
        db.execute(f"UPDATE stocks SET TotalValue = :value WHERE Stock = :stock AND user_id=:userid", value=(
            (float(numofstocks)+float(stocks[0]["NumOfStocks"]))*stockvalue["price"]), stock=stock, userid=user[0]["id"])
        db.execute(f"UPDATE stocks SET StockValue = :stockvalue WHERE Stock = :stock AND user_id=:userid",
                   stockvalue=stockvalue["price"], stock=stock, userid=user[0]["id"])
        db.execute(f"INSERT INTO history (user_id, boughtsold, Stock, NumOfStocks, StockValue, TotalValue, cashremaining) VALUES(:userid, 'sold', :stock, :numofstocks, :stockvalue, :totalvalue, :cashremaining)",
                   userid=user[0]["id"], stock=stock, numofstocks=int(numofstocks), stockvalue=stockvalue["price"], totalvalue=(float(numofstocks)*stockvalue["price"]), cashremaining=cashremaining)
        return redirect("/")
    else:
        return render_template("dhallranks.html", houses=houses)


@app.route("/passwordchange", methods=["GET", "POST"])
@login_required
def passwordchange():
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
        return render_template("passwordchange.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
