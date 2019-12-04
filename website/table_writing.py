import csv
from sys import exit
from cs50 import SQL
# First we load the necessary packages.

db = SQL("sqlite:///monch.db")
# This will allow us to load the information from the csv to the sql database.

#db.execute("DELETE FROM generic_day")
db.execute("DELETE FROM restrictions")
#db.execute("DELETE FROM new_generic_day")

# file = open("generic_day.csv", "r")
# # we take the csv file with the information about the dhall hours
# # so we open it to read it to memory.
# data = csv.DictReader(file)
# # We read the csv file in as a dictionary.

# for row in data:
#     # we loop through all of the rows in the data
#     db.execute("INSERT INTO generic_day (start_time, end_time, house, restriction_id) VALUES(?, ?, ?, ?)",
#                   row["start_time"], row["end_time"], row["house"], row["restriction_id"])
#     # we put all of the information from the csv into the SQL table

# file.close()
# # We make sure to close the file.

file = open("restrictions.csv", "r")
# we take the csv file with the information about the restrictions
# so we open it to read it to memory.
restrictions = csv.DictReader(file)
# We read the csv file in as a dictionary.

for other_row in restrictions:
    # we loop through all of the rows in the data
    db.execute("INSERT INTO restrictions (restriction_id, open_to, house_in_question) VALUES(?, ?, ?)",
                   other_row["restriction_id"], other_row["open_to"], other_row["house_in_question"])
    # we put all of the information from the csv into the SQL table

file.close()
# We make sure to close the file.

# file = open("new_generic_day.csv", "r")
# # we take the csv file with the information about the dhall hours
# # so we open it to read it to memory.
# data = csv.DictReader(file)
# # We read the csv file in as a dictionary.

# for row in data:
#     # we loop through all of the rows in the data
#     db.execute("INSERT INTO new_generic_day (start_time, end_time, house, restriction_id) VALUES(?, ?, ?, ?)",
#                   row["start_time"], row["end_time"], row["house"], row["restriction_id"])
#     # we put all of the information from the csv into the SQL table

# file.close()
# # We make sure to close the file.

file = open("all_days.csv", "r")
# we take the csv file with the information about the dhall hours
# so we open it to read it to memory.
data = csv.DictReader(file)
# We read the csv file in as a dictionary.

for row in data:
    # we loop through all of the rows in the data
    db.execute("INSERT INTO all_days (start_time, end_time, house, monday, tuesday, wednesday, thursday, friday, saturday, sunday) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   row["start_time"], row["end_time"], row["house"], row["monday"], row["tuesday"], row["wednesday"], row["thursday"], row["friday"], row["saturday"], row["sunday"])
    # we put all of the information from the csv into the SQL table

file.close()
# We make sure to close the file.