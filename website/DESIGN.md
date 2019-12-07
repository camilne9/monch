Monch Design

	The concept for Monch comes from the complexities of the dining hall restrictions in the various houses. Depending on the meal and the day of
the week, each house as a different policy on which house people must be a part of in order to eat in that dining hall. With differing hours and
inconsistent time windows where restrictions exist, we decided it would be handy to have a website that parces through the information for you, and
outputs a list of the dining halls that are open to you. This was the premise of Monch and is indeed also the function of the website now that it is
created.
	In terms of the workflow, we created a shared GitHub repository. Inside the repository, we created a directory called “website” in which all of
the actual files would live, which is what we submitted. In this directory, we have a directory with the CSS file and the “Monch” logo, a directory
with all of the html files and templates, and a collection of all of the csv files needed for the databases as well as 3 python files. The program
application.py contains the bulk of the code for the site, helpers.py contains functions that we call repeatedly in applications.py to simplify the
code, and table_writing.py contains the code that transferred all of the dhall data from our csv files to our SQL database.
	The largest and most important hurdle for Monch was storing all of the information about the dining hall hours and restrictions. We decided we
would store the information in an SQL database for ease of isolating information that is of interest. However, designing the layout of the SQL
tables was difficult. Ultimately the Monch website required 4 different SQL tables: 2 with the information about the dining hall hours and restrictions
and 2 dealing with the user information including user dhall preferences.
    In terms of structure, we first had an SQL table “restrictions” containing rows that have a “restriction_id” (which is a variable that we created
to represent each of the different restriction cases), a “house_in_question” variable that indicates what dhall you’re checking, and an “open_to”
variable that indicates a house that can eat in the “house_in_question”. For example, Eliot house dhall is sometimes open to Eliot students, so there
is a row with a restriction_id that has one row in the table that says Eliot in the “open_to” and “house_in_question” columns, but there are also times
when any upperclassman can eat in Eliot, so there is a different restriction_id that appears 12 times in the table, each with the “house_in_question”
being Eliot and each one having a different “open_to”. Next, the primary table, “all_days” goes through each of the houses and creates a bunch of rows
that represent the relevant time intervals. Each row has a start time, an end time, a house, and 7 columns of restriction_id’s, one for each day of the
week. (Note: the format of the time columns is unusual and is discussed later in this document.) The 7 restriction_id columns are named for the days of
the week for clarity and for ease of making queries because we can input a user-chosen day of the week as the queried column this way. Interpreting
these restriction_id’s requires using the “restrictions” table in tandem with “all_days”.
    The 2 SQL tables that handle user information were more straightforward. The “users” table stores the username, user_id, the user’s house, and
hashed password of anyone that creates an account. The “dhallpreferences” table has a row with a user_id, house, and a rank number. When you submit your
preferences, 13 rows are added to the table, one for each of your ranks.
In the SQL that we submitted there are also tables called “generic_day” and “new_generic_day”. These tables are from our first attempt at Monch. Because
of the difficulty of having all 7 different days restrictions, we first created the infrastructure for one “normal” day. Although we no longer use those
tables because we were able to fully implement a version of Monch that can handle any day of the week (a Better outcome rather than a Good), we left it
in the submitted folder for your reference.
	Although the SQL work was the biggest design choice of the project, we also handled other design challenges such as working with a time variables.
Since it is easier to work with numbers than time-like variables, we decided that we would express time as the number of minutes from the start of the
day. (Meaning 12:01AM is 1 and 11:30AM is 690 and 5:00pm is 1020, just to name a few.) With this format, we are able to check if a particular time falls
in a particular time window by comparing the numerical value of the particular time to the numerical values of the endpoints of the time interval. This
made the logic of our SQL queries much simpler (because it relied only on the algebra of inequalities rather than properties of time variables). To deal
with time this way, we made helper functions that give you the “value” (as we define it) of the current time or that give you the current day of the
week. We were also able to manipulate user inputs to also obtain a time “value” in cases where the user input a time.
	A subtlety of our design that was particularly valuable for our goals can be observed in the “order_by_preference” helper function. Since the goal
of Monch was to simplify the experience of discovering what dhalls were open, it was important to us that the outputs were in a logical order. For this
reason, a main feature of the site is the ability to indicate your personal preferences for the various dhalls. Thus, when you are shown a list of the
dining halls open to you, you always see them in order of favorite to least favorite. The re-ordering helper function gave us the ability to re-order any
list by preference just by using the power of the SQL databases we had already created. Furthermore, the function also deals with the case when there
are no inputs of user preference. It was one of our project goals that the website still be useful when the user does not input all of the possible
fields. Thus, it was important to us that this function handle the edge case where the user does not input dhall preferences. If there are no user
preferences, the reorder function instead orders the houses alphabetically. Thus, the site does not need to return an apology and instead still manages
to make the output be most useful. Putting the houses in alphabetical order is more user friendly and therefore was better aligned with Monch’s goal
than returning the open houses in a random order.
	Another small design choice that is particularly powerful is the use of the DELETE function in SQL. If the user submits dhall preferences, that
information will be stored in our SQL database. However, if they resubmit dhall preferences, we first delete their old preferences before writing the
new ones to the SQL database. Thus, the user is free to change their mind as many times as they want and we will always use their most recent
preferences.
	We had a lot of fun making Monch and we hope you enjoy it!