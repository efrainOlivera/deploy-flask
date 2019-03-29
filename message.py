from flask import Flask, render_template, request, redirect, session, flash
from mysqlconnection import connectToMySQL
from flask_bcrypt import Bcrypt
import re

app = Flask(__name__)
app.secret_key = "keep it secret"
bcrypt = Bcrypt(app)
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$') 

@app.route("/regislogin")
def regi():
	print("*"*50)

	return render_template("regi.html")

#________USER REGISTRATION
@app.route("/", methods = ["POST"])
def regi_info():
	print("&"*50)
	# name validation
	if len(request.form["fname"]) <= 1 or any(str.isdigit(c) for c in request.form["fname"]) == True:
		flash("please enter a first name")
		print("enter a different name")
		return redirect("/regislogin")
	session["username"] = request.form["fname"]
	print("session_firstname:", session["username"])
	# last name validation
	if len(request.form["lname"]) <= 1 or any(str.isdigit(c) for c in request.form["lname"]) == True:
		flash("please enter a last name")
		print("enter a different last name")
		return redirect("/regislogin")
	session["userlastname"] = request.form["lname"]
	print("session_lastname:", session["userlastname"])
	# email validation
	user = find_email_to_compare(request.form["email"])
	if user != ():
		flash("this email is already used.")
		return redirect("/regislogin")
	elif not EMAIL_REGEX.match(request.form["email"]):
		flash("Invalid email address!")
		return redirect("/regislogin")
	session["useremail"] = request.form["email"]
	print("session_email:", session["useremail"])
	# password validation
	if not re.match(r"[A-Za-z0-9@#$%^&+=]{8,}", request.form["password"]):
		flash("at least 8 characters, 1 uppercase letter, numbers and special characters")
		return redirect("/regislogin")
	elif request.form["password"] != request.form["passwordconfi"]:
		flash("Password and confirm password don't match")
		return redirect("/regislogin")
	
	password_hash = bcrypt.generate_password_hash(request.form["password"])
	if not "_flashes" in session.keys():
		mysql = connectToMySQL("user_info")
		data_to_db = "INSERT INTO userdata (first_name, last_name, email, password) VALUES (%(fn)s,%(ln)s,%(em)s,%(psh)s);"
		data_from = {
			"fn": request.form["fname"],
			"ln": request.form["lname"],
			"em": request.form["email"],
			"psh": password_hash
		}
		user_id = mysql.query_db(data_to_db,data_from)
		session["login_user"] = user_id
		flash("New user successfully added!")
		return redirect("/home")

#_________LOGIN 
@app.route("/login", methods=["POST"])
def login():
	# getting email from db to compare
	user = find_email_to_compare(request.form["email"])
	print("^"*50)
	print(user)
	if user:
		if bcrypt.check_password_hash(user[0]["password"], request.form["password"]):
			session["login_user"] = user[0]["id"]
			print(session["login_user"])
			return redirect("/home")
	flash("Please check email and password")
	return redirect("/regislogin")

#_________LOG OUT AND CLEAR SESSION
@app.route("/logout")
def logout():
	#clear session
	print("$"*50)
	print(session)
	session.clear()
	return redirect("/regislogin")

#_________HOME RENDER PAGE user account
@app.route("/home")
def user_account():
	# only user that are login should see this page.
	print("#"*50)
	

	user = find_all_user_info(session["login_user"])
	session["user_id"] = user[0]["id"]
	session["showname"] = user[0]["first_name"]
	session["showlastname"] = user[0]["last_name"]
	session["showemail"] = user[0]["email"]
	mysql = connectToMySQL("user_info")
	nombres = mysql.query_db("SELECT userdata.first_name, userdata.id FROM userdata")

	db_message_display = messages_retrieving(session["user_id"])

	return render_template("home.html", displaynombres = nombres, messages_display = db_message_display)

#_______SEND MESSAGES
@app.route("/send_message/<id>", methods=["POST"])
def send_mms(id):
	# add message to do
	message_to_send = mms_to_db_recipient(request.form["message_created"],session["user_id"],id)
	print(session["user_id"])
	print("%"*50)
	return redirect("/home")
#_________DELETE MESSAGES
@app.route("/delete_messages/<id>", methods=["POST"])
def delete(id):
	message_to_delete = db_delete_message(id)
	return redirect("/home")


#_________EDIT MESSAGES
@app.route("/edit")
def edit_user():
	return render_template("edit_user.html")

@app.route("/edit", methods = ["POST"])
def edit_post():
	# user_id_id = session["user_id"]
	mysql = connectToMySQL("user_info")
	query = "UPDATE user_info.userdata SET first_name = %(fn)s, last_name = %(ln)s, email = %(em)s WHERE (id = %(id)s );" 
	data = { 
		"fn": request.form["fname"],
		"ln": request.form["lname"],
		"em": request.form["email"],
		"id": session["user_id"]

	} 
	mysql.query_db(query,data)
	return redirect("/home")


#______________DATABASE FUNCTIONS
def find_email_to_compare(email):
    mysql = connectToMySQL("user_info")
    query = "SELECT * FROM userdata WHERE userdata.email=%(email)s"
    data = {
        "email": email
    }
    return mysql.query_db(query, data)

def find_all_user_info(bob):
	mysql = connectToMySQL("user_info")
	query = "SELECT * FROM userdata WHERE userdata.id =%(id)s"
	data = {
		"id": bob
	}
	return mysql.query_db(query,data)

def mms_to_db_recipient(message,user_id_from,recipient_id):
	mysql = connectToMySQL("user_info")
	query = "INSERT INTO mms (messages, userdata_id,recipient_id) VALUES (%(mms)s,%(usd)s,%(rcp)s);"
	data = {
		"mms": message,
		"usd": user_id_from,
		"rcp": recipient_id
	}
	return mysql.query_db(query,data)

def messages_retrieving(messages):
	mysql = connectToMySQL("user_info")
	query = "SELECT mms.messages, mms.userdata_id, userdata.first_name , mms.id FROM mms JOIN userdata ON userdata.id = mms.userdata_id WHERE recipient_id = %(usd)s"
	data = {
		"usd": messages,
	
	}
	return mysql.query_db(query,data)

def db_delete_message(mid):
    mysql = connectToMySQL("user_info")
    query = "DELETE FROM mms WHERE mms.id = %(id)s"
    data = {
    	"id": mid
    }
    return mysql.query_db(query, data)






if __name__=="__main__":
	app.run(debug=True)