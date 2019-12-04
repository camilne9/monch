def sell():
    """Sell shares of stock"""
    # These lines generate the possible values for our drop down menu.
    user_id = session["user_id"]
    valid_api = db.execute(f"SELECT DISTINCT symbol FROM stonks3 WHERE id IS {user_id}")
    if request.method == "POST":
        # if we are potsing, we get the output of the lookup function and store it.
        sell = lookup(request.form.get("api"))
        if sell:
            # if the lookup doesn't return none, we use the lookup output to generate values that will allow us to update the necessary data.
            api = sell['symbol']
            price = float(sell['price'])
            # Here we are generating an updated expression for the cash the user will have.
            user_id = int(session["user_id"])
            cash = db.execute(f"SELECT cash FROM users WHERE id IS {user_id}")
            cash2 = cash[0]['cash']
            change_cash = price*float(request.form.get("shares"))
            new_cash = cash2 + change_cash
            # This query will allow us to verify that the user is selling a viable number of shares.
            current_shares = db.execute(
                f"SELECT symbol, shares FROM (SELECT symbol, SUM(quantity) AS shares FROM (SELECT * FROM stonks3 WHERE id IS {user_id} UNION ALL SELECT * FROM sales2 WHERE id IS {user_id}) GROUP BY symbol) WHERE symbol = :api",
                api=api)
            current_shares = current_shares[0]['shares']
            # We ensure that the number of shares being sold is less than or equal to the number of shares the user has.
            if current_shares < float(request.form.get("shares")):
                return apology("Not enough shares for this transaction")
            # We only let the user sell a positive number of shares, otherwise we throw an error.
            if float(request.form.get("shares")) <= 0:
                return apology("Invalid number of shares")
            db.execute("INSERT INTO sales2 (id, symbol, quantity, value_per) VALUES (:user_id, :API, :shares, :value_per);",
                       user_id=user_id, API=str.upper(request.form.get("api")), shares=-1*int(request.form.get("shares")), value_per=float(sell['price']))
            # We increase the cash of the user in the database based on the profit of the sale.
            db.execute(f"UPDATE users SET cash = {new_cash} WHERE id = {user_id}")
            # After selling, we bring the user back to the home page
            return redirect("/")
        else:
            return apology("must select symbol")
    else:
        # if the method was GET, we direct the user to the sell page.
        return render_template("sell.html", valid_api=valid_api)