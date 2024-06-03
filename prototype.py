from pickle import TRUE
from typing import final
from urllib import request
from flask import Flask, render_template, request, session, redirect
import sqlite3
from datetime import date
import json
from collections import Counter


app = Flask("__FoodOrderSystem__", template_folder="templates", static_folder="static")
app.secret_key = "Dgjoewheighe"
db = "foodsystem.db"
conn = sqlite3.connect(db)


# function that querys the database
def fetchQuery(query):
    sqlite3.connect(db).row_factory = sqlite3.Row #sets up row factory
    cur=sqlite3.connect(db).cursor()
    cur.execute(query)
    result = cur.fetchall() # stores the query results
    return result

# function for committing to the database
def commitQuery(query):
    try:
        con = sqlite3.connect(db) #connects
        cur = con.cursor()
        cur.execute(query)  # executes the query
        print("Query executed")
        con.commit()    #commits it to database
        print("committed")
    except:
        con.rollback() #rolls back the commitment if a bad happens
        print("exception")


# route for index.hmtl, will immediately redirect to login page
@app.route("/")
def index():
    return render_template("index.html")

#login page, POST from creating an account in the account page.
@app.route("/login", methods=["GET","POST"])
def login():
    #POST from account page
    if request.method == "POST":
        conn
        print("Opened database successfully")
        try:
            print("trying")
            #sets variables as form reuslts
            newUser = request.form["new-username"]
            newPwd = request.form["new-pwd"]
            fname = request.form["fname"]
            lname = request.form["lname"]

            with sqlite3.connect(db) as con:
                cur = con.cursor()
                #creates a new user
                cur.execute("INSERT INTO Users (UserName,FirstName,LastName,Password,UserType) VALUES(?,?,?,?,?)", (newUser,fname,lname,newPwd,"retail")) 
                con.commit()
                print("succ")
                msg = "Account created successfully"
        except:
            con.rollback()
            print("bad")
            msg = "Creation failed, try again"
        finally:
            return render_template("login.html", msg = msg) #returns the login page

    if request.method =="GET":
        session.clear() #clears the login session if you log out
        return render_template("login.html")


#route for signup page
@app.route("/createaccount", methods=["GET","POST"])
def createaccount():
    return render_template("signup.html")


#page that validates login details
@app.route("/validate", methods=["GET", "POST"])
def validate():
    if request.method == "POST":
        conn
        session["login"] = request.form #creates session details from the login form
        login = session["login"]
        username = login["username"]
        pwd = login["pwd"]
        userlogin = (username, pwd)
        type=0
        try:
            with sqlite3.connect(db) as con:
                cur=con.cursor()
                cur.execute("SELECT UserName, Password FROM Users") #queries the Users entity
                userlist = cur.fetchall()
                if userlogin in userlist: #allows user through if they exist
                    print("user in login list")
                    cur.execute(f"SELECT UserType FROM Users WHERE UserName = '{username}'")
                    type = cur.fetchall()
                    confirm=True
                        
                else:
                    print("user not in list") #if user doesnt exist
                    confirm=False
        except:
            print("process aborted") #if a bad happens kick them out
            confirm = False
        finally:
            username = login["username"] 
            confirm=confirm
    elif request.method == "GET": #if going to the validate page for no reason
        confirm = False #kick them to the login page
    print(confirm)
    return render_template("loginvalidation.html", username=username, confirm=confirm, type=type, retail=([('retail',)]), staff=([('staff',)])) #render the validation page and pass variables through


# route for page to create items, only accessible through typing route into url
@app.route("/createitem", methods=["GET","POST"])
def foodcreation():
    msg=""
    if request.method == "POST": #stores form results as variables
        try:
            foodname = request.form["foodname"]
            descr = request.form["description"]
            itemprice = request.form["price"]
            category = request.form["category"]
            with sqlite3.connect(db) as con: #inserts those variables into the database as an item
                cur = con.cursor()
                cur.execute("INSERT INTO Items (ItemName,ItemDescription,ItemPrice,Category) VALUES(?,?,?,?)", (foodname, descr, itemprice, category)) 
                con.commit()
                msg = "item created" #lets the user know the item was created
        except:
            print("exception") #does this if a bad happens  
            msg = "try again" #lets user know a bad happened
    return render_template("foodcreation.html", msg=msg) #render the page and pass the message through


# route for the retail page first page for retail users
@app.route("/retail/options", methods=["GET","POST"])
def options():
    username = session["login"]["username"] #grabs username from session
    orderlist=[]
    try:
        with sqlite3.connect(db) as con: #Grabs current user ID from db
            userID = fetchQuery(f"SELECT UserID FROM Users WHERE Username = '{username}'")
            print(userID)
            orderlist = fetchQuery(f"SELECT * FROM Orders WHERE UserID = '{userID[0][0]}' ORDER BY OrderID DESC") #creates the orderlist to be displayed on the page
            print(orderlist)
    except:
        print("exception")
    return render_template("retail.html", username = username, orderlist=orderlist, count=0) #renders the retail page and passes the appropriate variables through


#route for viewing a specific order's items
@app.route("/orders/<OrderID>")
def vieworder(OrderID): #OrderID is passed through
    try: #fetches orderitems from the database 
        orderitems = fetchQuery(f"SELECT OrderItems.ItemID, Items.ItemName, ItemQuantity, Items.ItemPrice FROM OrderItems INNER JOIN Items on items.ItemID = OrderItems.ItemID WHERE OrderID = {OrderID}")
        print(orderitems)
        orderlists = []
        count = 0
        for item in orderitems: #changes the price to the product of price and quantity, for total price for every item
            orderlist = list(orderitems[count]) #by converting the query result to a list so it can be changed
            orderlist[3] = orderlist[3]*orderlist[2]
            orderlists.append(orderlist)
            count +=1
        orderitems = tuple(orderlists) #converts back into a tuple
        print(orderitems)
        orderprice = fetchQuery(f"SELECT TotalPrice FROM Orders WHERE OrderID = {OrderID}") #fetches orderprice from database
    except:
        orderprice=0
        orderitems=0
        print("exception")
    return render_template("vieworder.html", orderprice=orderprice[0][0], orderitems=orderitems, username = session["login"]["username"], OrderID = OrderID)#renders the page with appropriate variables


#route for the menu page
@app.route("/retail/createorder")
def createorder(): #fetches items from database and assigns them a category to be displayed appropriately
    lunch = fetchQuery("SELECT * FROM Items WHERE Category = 'Lunch'")
    drinks = fetchQuery("SELECT * FROM Items WHERE Category = 'Drink'")
    snacks = fetchQuery("SELECT * FROM Items WHERE Category = 'Snack'")
    return render_template("neworder.html", lunch=lunch, drinks=drinks, snacks=snacks)#you get how its rendered


#route for staff page
@app.route("/staff")
def staffoptions():
    today = date.today().strftime("%d/%m") #gets date in a day/month format eg 28/08, 28th of August
    try:
        with sqlite3.connect(db) as con: #fetches orders that were made for that day
            orderlist = fetchQuery(f"SELECT Orders.*, Users.FirstName, Users.LastName FROM Orders INNER JOIN Users ON Orders.UserID = Users.UserID WHERE Date = '{today}'")
    except:
        orderlist=[]
        print("exception")
    return render_template("staff.html", username = session["login"]["username"], orderlist = orderlist, today=today)#renders page


#route for the page which displays all orders in the database
@app.route("/staff/allorders")
def revieworders():
    try:
        with sqlite3.connect(db) as con: #fetches all orders and who ordered them from database
            orderlist = fetchQuery(f"SELECT Orders.*, Users.FirstName, Users.LastName FROM Orders INNER JOIN Users ON Orders.UserID = Users.UserID")
    except:
        orderlist=[]
        print("exception")
    return render_template("staffAll.html", username = session["login"]["username"], orderlist = orderlist)#renders


#route for the cart page
@app.route("/retail/cart")
def checkout():
    cartDict = session["cartDict"] #fetches the session data and stores it
    itemPriceDict = {}
    nameDict={}
    totalPrice=0
    for key in cartDict: #displays the items selected from the menu as items in a cart
        itemName = fetchQuery(f"SELECT ItemName FROM Items WHERE ItemID = {key}")[0][0]
        nameDict.update({key:itemName})
        itemPrice = fetchQuery(f"SELECT ItemPrice FROM Items WHERE ItemID = {key}")[0][0]
        itemPriceDict.update({key:itemPrice})
        totalPrice = totalPrice + itemPriceDict[key]*cartDict[key]
        print(totalPrice)

    print(cartDict)
    print(nameDict)
    print(itemPriceDict)
    session["itemPriceDict"] = itemPriceDict #stores these as session stuff for later use
    session["totalPrice"] = totalPrice
    return render_template("cart.html", cartDict=cartDict, nameDict=nameDict, itemPriceDict=itemPriceDict, totalPrice=totalPrice, itemTotal=session["itemCount"])#render stuff


#route that the order details are sent to
@app.route("/cart/<string:itemList>", methods = ["POST"])
def retrieveCartList(itemList):
    itemList = itemList.split(",") #turns it into an actual list
    count=0
    for item in itemList: #turns the items into integers
        newItem = itemList[count]
        newItem = int(newItem)
        itemList[count] = newItem
        count +=1
    print(itemList) 
    cartDict = dict(Counter(itemList)) #turns the list into a dictionary based on the amount of times a value is repeated in the list
    session["itemCount"] = count    #stores in session for later use
    session["cartDict"] = cartDict
    session["itemList"] = itemList

    return("/")


#takes the stuff from the cart and inserts it into the database
@app.route("/system/insert", methods = ["POST"])
def insertOrder():
    itemPriceDict = session["itemPriceDict"] #fetching shizzle from session
    totalPrice = session["totalPrice"]
    cartDict = session["cartDict"]
    username = session["login"]["username"]
    today = date.today().strftime("%d/%m") #getting da date
    userID = fetchQuery(f"SELECT UserID FROM Users WHERE Username = '{username}'")[0][0] #getting userId 
    commitQuery(f"INSERT INTO Orders (UserID,Date,TotalPrice,CollectionTime) VALUES('{userID}','{today}','{totalPrice}','Lunch')")#creates an entry for Orders entity in database
    orderID = fetchQuery("SELECT OrderID FROM Orders ORDER BY OrderID DESC LIMIT 1")[0][0]
    print(orderID)
    for item in cartDict: #creates entries in OrderItems entity in database for every item in the order
        commitQuery(f"INSERT INTO OrderItems (OrderID,ItemID,ItemQuantity) VALUES('{orderID}','{item}','{cartDict[item]}')")
    return("/")


#function for re ordering an order
@app.route("/system/<int:OrderID>", methods = ["POST"])
def reorder(OrderID):
    orderitems = fetchQuery(f"SELECT * FROM OrderItems WHERE OrderID = {OrderID}") #gets OrderItems for a specific order
    order = fetchQuery(f"SELECT * FROM Orders WHERE OrderID = {OrderID}") #gets the Order details from Orders entity
    commitQuery(f"INSERT INTO Orders (UserID,Date,TotalPrice,CollectionTime) VALUES('{order[0][1]}','{order[0][2]}','{order[0][3]}','{order[0][4]}')") #creates an entry in Orders
    orderID = fetchQuery("SELECT OrderID FROM Orders ORDER BY OrderID DESC LIMIT 1")[0][0]#gets the orderID for the thing right above ^^^^
    count=0
    for item in orderitems: #creates an entry for every order item
        print("orderitems stuff: ",orderitems[count][2],orderitems[count][3])
        commitQuery(f"INSERT INTO OrderItems (OrderID,ItemID,ItemQuantity) VALUES('{orderID}','{orderitems[count][2]}','{orderitems[count][3]}')")
        count+=1
    return("/")

app.run(host="0.0.0.0", port=81)