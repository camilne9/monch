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