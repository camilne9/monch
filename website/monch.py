import datetime
from datetime import datetime
from cs50 import SQL

db = SQL("sqlite:///monch.db")
# This will allow us to reference the information in the sql database.

now = datetime.now()
current_time = datetime.timestamp(now)

test = str(now.hour) + ":" + str(now.minute)

# houses = db.execute(f"SELECT * FROM generic_day WHERE {time} IS end_time")

print(f"{test} \n {now}")

@app.route("/dhallranks", methods=["GET", "POST"])
@login_required
def dhallranks():
    valid_hours = list(range(1, 13))
    valid_minutes = list(range(0, 60))
    if request.method == "POST":
        hour = request.form.get("Hour")
        minute = request.form.get("Minute")
        if request.form.get("Hour") == none or request.form.get("Minute") == none or request.form.get("AM/PM") == none:
            return apology("Not a valid time")
        if request.form.get("") == "AM":
            value = 60*hour + minute
        else:
            value = 60 * (hour + 12) + minute
        houses = db.execute(f"SELECT house FROM new_generic_day ")
        return render_template("open.html", value=value)
    else:
        return render_template("arbitrary_time.html", valid_hours = valid_hours, valid_minutes = valid_minutes)

@app.route("/open_dhalls")
@login_required
def open_dhalls():

user_id = session["user_id"]
user = db.execute(f"SELECT * FROM users WHERE user_id IS {user_id}")
user_house = user["house"]
houses = db.execute(f"SELECT house_in_question FROM restrictions WHERE restriction_id IN (SELECT restriction_id FROM new_generic_day WHERE {value} > start_time AND {value} < end_time ) AND open_to IS {user_house}")
