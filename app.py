import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from datetime import datetime
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/get_checks")
def get_checks():
    checks = mongo.db.checks.find()
    return render_template("checks.html", checks=checks)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "fname": request.form.get("fname").lower(),
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for("profile", username=session["user"]))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                existing_user["password"], request.form.get("password")):
                    session["user"] = request.form.get("username").lower()
                    flash("Welcome, {}".format(request.form.get("username")))
                    return redirect(url_for(
                        "profile", username=session["user"]))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # grab the session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    return render_template("profile.html", username=username)

    return redirect(url_for("login"))

@app.route("/logout")
def logout():
    # remove user from session cookie
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_check", methods=["GET", "POST"])
def add_check():
    if request.method == "POST":
        screen_q1 = "true" if request.form.get("screen_q1") else "false"
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        check = {
            "manager_name": request.form.get("manager_name"),
            "dept_name": request.form.get("dept_name"),
            "max_total_time": request.form.get("max_total_time"),
            "screen_q1": screen_q1,
            "created_by": session["user"],
            "created_date": (dt_string),
            "dsp_created_date": (dt_string)
        }
        mongo.db.checks.insert_one(check)
        flash("Assessment Successfully Added")
        return redirect(url_for("get_checks"))
        
    managers = mongo.db.managers.find().sort("manager_name", 1)
    departments = mongo.db.departments.find().sort("dept_name", 1)
    return render_template("add_check.html", managers=managers, departments=departments)

@app.route("/edit_check/<check_id>", methods=["GET", "POST"])
def edit_check(check_id):
    if request.method == "POST":
        screen_q1 = "true" if request.form.get("screen_q1") else "false"
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        submit = {
            "manager_name": request.form.get("manager_name"),
            "dept_name": request.form.get("dept_name"),
            "max_total_time": request.form.get("max_total_time"),
            "created_date": request.form.get("created_date"),
            "dsp_created_date": request.form.get("created_date"),
            "screen_q1": screen_q1,
            "created_by": session["user"],
            "updated_date": (dt_string)
        }
        mongo.db.checks.update({"_id": ObjectId(check_id)}, submit)
        flash("Assessment Successfully Updated")
        return redirect(url_for("get_checks"))

    check = mongo.db.checks.find_one({"_id": ObjectId(check_id)})
    managers = mongo.db.managers.find().sort("manager_name", 1)
    departments = mongo.db.departments.find().sort("dept_name", 1)
    return render_template("edit_check.html", check=check, managers=managers, departments=departments)


@app.route("/delete_check/<check_id>")
def delete_check(check_id):
    mongo.db.checks.remove({"_id": ObjectId(check_id)})
    flash("Assessment Successfully Deleted")
    return redirect(url_for("get_checks"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)