import datetime
from datetime import datetime
from datetime import date
from cs50 import SQL
import calendar

db = SQL("sqlite:///monch.db")
# This will allow us to reference the information in the sql database.

# now = datetime.now()
# current_time = datetime.timestamp(now)

# test = str(now.hour) + ":" + str(now.minute)

# # houses = db.execute(f"SELECT * FROM generic_day WHERE {time} IS end_time")

# print(f"{test} \n {now}")

# @app.route("/dhallranks", methods=["GET", "POST"])
# @login_required
# def dhallranks():
#     valid_hours = list(range(1, 13))
#     valid_minutes = list(range(0, 60))
#     if request.method == "POST":
#         hour = request.form.get("Hour")
#         minute = request.form.get("Minute")
#         if request.form.get("Hour") == none or request.form.get("Minute") == none or request.form.get("AM/PM") == none:
#             return apology("Not a valid time")
#         if request.form.get("") == "AM":
#             value = 60*hour + minute
#         else:
#             value = 60 * (hour + 12) + minute
#         houses = db.execute(f"SELECT house FROM new_generic_day ")
#         return render_template("open.html", value=value)
#     else:
#         return render_template("arbitrary_time.html", valid_hours = valid_hours, valid_minutes = valid_minutes)

# @app.route("/open_dhalls")
# @login_required
# def open_dhalls():

# user_id = session["user_id"]
# user = db.execute(f"SELECT * FROM users WHERE user_id IS {user_id}")
# user_house = user["house"]
# houses = db.execute(f"SELECT house_in_question FROM restrictions WHERE restriction_id IN (SELECT restriction_id FROM new_generic_day WHERE {value} > start_time AND {value} < end_time ) AND open_to IS {user_house}")

# def order_by_preference(list_of_strings):
#     user_id = session["user_id"]
#     for house in list_of_strings:
#         houses = db.execute(f"SELECT * FROM preferences WHERE user_id IS {user_id} ORDER BY rank")
#     houses = houses["house"]
#     return houses

def get_current_value():
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    value = ((hour-5)%24)*60 + minute
    return value

def get_current_day():
    my_date = date.today()
    return calendar.day_name[my_date.weekday()]

test = datetime.today().strftime('%A').lower()
print(f"{get_current_value()}")
print(f"{get_current_day}")
print(f"{test}")