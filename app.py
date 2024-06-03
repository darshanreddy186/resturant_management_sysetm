from flask import Flask, render_template, request, session, redirect
import sqlite3
from datetime import date
from collections import Counter
import os

app = Flask("__FoodOrderSystem__", template_folder="templates", static_folder="static")
app.secret_key = "Dgjoewheighe"
db = "foodsystem.db"

# Ensure the database connection is closed properly
def get_db_connection():
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    return conn

# function that queries the database
def fetchQuery(query):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query)
    result = cur.fetchall()  # stores the query results
    conn.close()
    return result

# function for committing to the database
def commitQuery(query):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(query)  # executes the query
        conn.commit()  # commits it to the database
    except:
        conn.rollback()  # rolls back the commitment if an error occurs
    finally:
        conn.close()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            newUser = request.form["new-username"]
            newPwd = request.form["new-pwd"]
            fname = request.form["fname"]
            lname = request.form["lname"]

            with sqlite3.connect(db) as con:
                cur = con.cursor()
                cur.execute("INSERT INTO Users (UserName, FirstName, LastName, Password, UserType) VALUES (?, ?, ?, ?, ?)", 
                            (newUser, fname, lname, newPwd, "retail"))
                con.commit()
                msg = "Account created successfully"
        except:
            con.rollback()
            msg = "Creation failed, try again"
        finally:
            return render_template("login.html", msg=msg)
    if request.method == "GET":
        session.clear()
        return render_template("login.html")

@app.route("/createaccount", methods=["GET", "POST"])
def createaccount():
    return render_template("signup.html")

@app.route("/validate", methods=["GET", "POST"])
def validate():
    confirm = False
    user_type = 0
    if request.method == "POST":
        session["login"] = request.form
        login = session["login"]
        username = login["username"]
        pwd = login["pwd"]
        userlogin = (username, pwd)
        try:
            with sqlite3.connect(db) as con:
                cur = con.cursor()
                cur.execute("SELECT UserName, Password FROM Users")
                userlist = cur.fetchall()
                if userlogin in userlist:
                    cur.execute(f"SELECT UserType FROM Users WHERE UserName = '{username}'")
                    user_type = cur.fetchall()
                    confirm = True
                else:
                    confirm = False
        except:
            confirm = False
    return render_template("loginvalidation.html", username=username, confirm=confirm, type=user_type, retail=[('retail',)], staff=[('staff',)])

@app.route("/createitem", methods=["GET", "POST"])
def foodcreation():
    msg = ""
    if request.method == "POST":
        try:
            foodname = request.form["foodname"]
            descr = request.form["description"]
            itemprice = request.form["price"]
            category = request.form["category"]
            with sqlite3.connect(db) as con:
                cur = con.cursor()
                cur.execute("INSERT INTO Items (ItemName, ItemDescription, ItemPrice, Category) VALUES (?, ?, ?, ?)",
                            (foodname, descr, itemprice, category))
                con.commit()
                msg = "Item created"
        except:
            msg = "Try again"
    return render_template("foodcreation.html", msg=msg)

@app.route("/retail/options", methods=["GET", "POST"])
def options():
    username = session["login"]["username"]
    orderlist = []
    try:
        with sqlite3.connect(db) as con:
            userID = fetchQuery(f"SELECT UserID FROM Users WHERE Username = '{username}'")
            orderlist = fetchQuery(f"SELECT * FROM Orders WHERE UserID = '{userID[0][0]}' ORDER BY OrderID DESC")
    except:
        pass
    return render_template("retail.html", username=username, orderlist=orderlist, count=0)

@app.route("/orders/<OrderID>")
def vieworder(OrderID):
    try:
        orderitems = fetchQuery(f"SELECT OrderItems.ItemID, Items.ItemName, ItemQuantity, Items.ItemPrice FROM OrderItems INNER JOIN Items ON Items.ItemID = OrderItems.ItemID WHERE OrderID = {OrderID}")
        orderlists = []
        count = 0
        for item in orderitems:
            orderlist = list(orderitems[count])
            orderlist[3] = orderlist[3] * orderlist[2]
            orderlists.append(orderlist)
            count += 1
        orderitems = tuple(orderlists)
        orderprice = fetchQuery(f"SELECT TotalPrice FROM Orders WHERE OrderID = {OrderID}")
    except:
        orderprice = 0
        orderitems = 0
    return render_template("vieworder.html", orderprice=orderprice[0][0], orderitems=orderitems, username=session["login"]["username"], OrderID=OrderID)

@app.route("/retail/createorder")
def createorder():
    lunch = fetchQuery("SELECT * FROM Items WHERE Category = 'Lunch'")
    drinks = fetchQuery("SELECT * FROM Items WHERE Category = 'Drink'")
    snacks = fetchQuery("SELECT * FROM Items WHERE Category = 'Snack'")
    return render_template("neworder.html", lunch=lunch, drinks=drinks, snacks=snacks)

@app.route("/staff")
def staffoptions():
    today = date.today().strftime("%d/%m")
    try:
        orderlist = fetchQuery(f"SELECT Orders.*, Users.FirstName, Users.LastName FROM Orders INNER JOIN Users ON Orders.UserID = Users.UserID WHERE Date = '{today}'")
    except:
        orderlist = []
    return render_template("staff.html", username=session["login"]["username"], orderlist=orderlist, today=today)

@app.route("/staff/allorders")
def revieworders():
    try:
        orderlist = fetchQuery(f"SELECT Orders.*, Users.FirstName, Users.LastName FROM Orders INNER JOIN Users ON Orders.UserID = Users.UserID")
    except:
        orderlist = []
    return render_template("staffAll.html", username=session["login"]["username"], orderlist=orderlist)

@app.route("/retail/cart")
def checkout():
    cartDict = session["cartDict"]
    itemPriceDict = {}
    nameDict = {}
    totalPrice = 0
    for key in cartDict:
        itemName = fetchQuery(f"SELECT ItemName FROM Items WHERE ItemID = {key}")[0][0]
        nameDict.update({key: itemName})
        itemPrice = fetchQuery(f"SELECT ItemPrice FROM Items WHERE ItemID = {key}")[0][0]
        itemPriceDict.update({key: itemPrice})
        totalPrice += itemPriceDict[key] * cartDict[key]
    session["itemPriceDict"] = itemPriceDict
    session["totalPrice"] = totalPrice
    return render_template("cart.html", cartDict=cartDict, nameDict=nameDict, itemPriceDict=itemPriceDict, totalPrice=totalPrice, itemTotal=session["itemCount"])

@app.route("/cart/<string:itemList>", methods=["POST"])
def retrieveCartList(itemList):
    itemList = itemList.split(",")
    count = 0
    for item in itemList:
        itemList[count] = int(item)
        count += 1
    cartDict = dict(Counter(itemList))
    session["itemCount"] = count
    session["cartDict"] = cartDict
    session["itemList"] = itemList
    return "/"

@app.route("/system/insert", methods=["POST"])
def insertOrder():
    itemPriceDict = session["itemPriceDict"]
    totalPrice = session["totalPrice"]
    cartDict = session["cartDict"]
    username = session["login"]["username"]
    today = date.today().strftime("%d/%m")
    userID = fetchQuery(f"SELECT UserID FROM Users WHERE Username = '{username}'")[0][0]
    commitQuery(f"INSERT INTO Orders (UserID, Date, TotalPrice, CollectionTime) VALUES ('{userID}', '{today}', '{totalPrice}', 'Lunch')")
    orderID = fetchQuery("SELECT OrderID FROM Orders ORDER BY OrderID DESC LIMIT 1")[0][0]
    for item in cartDict:
        commitQuery(f"INSERT INTO OrderItems (OrderID, ItemID, ItemQuantity) VALUES ({orderID}, {item}, {cartDict[item]})")
    return redirect("/retail/options")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
