print("importing dependencies...", end="")
from bs4 import BeautifulSoup as bs
import pandas as pd
from sentiment_analyzer import Analyzer
from imdb_review_module import Reviews
import requests
from functools import wraps
import pymongo # pip install pymongo[srv]
from pymongo.mongo_client import MongoClient
from flask import Flask, flash, redirect, render_template, request, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
from datetime import timedelta, datetime
print("done.")

def in_session(func):
    @wraps(func)
    def inner():
        if "user" in session:
            try:
                return func()
            except IndexError:
                return render_template("error_img_scrap.html", error="Please enter a movie URI")
            except Exception as e:
                import traceback
                traceback.print_exc()
                return render_template("error_img_scrap.html", error=str(e))
        else:
            flash("Looks like your session has expired","warning")
            return redirect(url_for("login_page"))
    return inner

def error_protector(func):
    @wraps(func)
    def inner():
        try:
            return func()
        except Exception as e:
            import traceback
            traceback.print_exc()
            return render_template("error_img_scrap.html", error=str(e))
    return inner

def connect_db(use_cloud=False):
    try:
        if use_cloud:
            global mongodb
            mongodb = True
            print("\nConnecting to MongoDB cloud...", end="")
            mongodb_uri = "mongodb+srv://admin:admin@mycontacts.lcbszyg.mongodb.net/?retryWrites=true&w=majority&appName=myContacts"
            client = MongoClient(mongodb_uri)
            global collection
            collection = client.movieRecommenderDB.registeredUsers
            print("done\n")
        else:
            print("\nConnecting to local SQL Database...", end="")
            global connection
            connection = pymysql.connect(
                host="localhost", user="root", password="root", database="auth_db"
            )
            global cursor
            cursor = connection.cursor()
            print("done\n")
    except pymongo.errors.ConfigurationError as e:
        print("\n\tERROR: Server not reachable !!!\n")
        exit(0)
    except Exception as e:
        print("\n\tERROR: Some ERROR occured !!!\n"+str(e))
        exit(0)

current_df = None
current_analyzed_df = pd.DataFrame()
connection = None
cursor = None
mongodb = None
collection = None
r=Reviews()
a=Analyzer()

connect_db(use_cloud=False)

app=Flask(__name__)
app.secret_key = "something"
app.permanent_session_lifetime = timedelta(minutes=5)

@app.route("/")
@app.route("/login", methods=["GET", "POST"])
@error_protector
def login_page():
        if request.method == "POST":
            email = request.form.get("email")
            password = request.form.get("password")

            if mongodb:
                response_list = list(collection.find({}, {"_id": 0, "email": 1}))
                user_emails = [d["email"] for d in response_list]
            else:
                cursor.execute(f"SELECT email FROM users;")
                user_emails = [user_email for user_email, in cursor.fetchall()]

            if email in user_emails:
                if mongodb:
                    response_list = list(collection.find({"email": email}, {"_id": 0, "hashed_password": 1, "username":1}))
                    data = [(d["hashed_password"], d["username"]) for d in response_list][0]
                else:
                    cursor.execute(
                        f"SELECT hashed_password,username FROM users WHERE email = '{email}';"
                    )
                    data = cursor.fetchone()

                hashed_password = data[0]
                if check_password_hash(hashed_password, password):
                    session.clear()
                    session.permanent = True
                    session["user"] = data[1]
                    current_time = datetime.now()
                    session["start_time"] = current_time.strftime(r"%b %d, %Y %H:%M:%S")
                    session_end_time = current_time + app.permanent_session_lifetime
                    session["end_time"] = session_end_time.strftime(r"%b %d, %Y %H:%M:%S")
                    print(f'Logged in user: {session.get("user")}')
                    flash("You are now logged in!", "success")
                    return redirect(url_for("user_page"))
                else:
                    flash("Invalid Credientials !!!", "danger")
                    return redirect(url_for("login_page"))
            else:
                flash("You are not registered! Please register below.", "warning")
                return redirect(url_for("register_page"))
        else:
            if session.get("user"):
                flash("You are in Session...", "primary")
                return redirect(url_for("user_page"))
            else:
                return render_template("login_auth.html")

@app.route("/register", methods=["GET", "POST"])
@error_protector
def register_page():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        hashed_password = generate_password_hash(password)
        
        if mongodb:
            response_list = list(collection.find({}, {"_id": 0, "username": 1}))
            users = [d["username"] for d in response_list]
        else:
            cursor.execute(f"SELECT username FROM users WHERE username='{username}';")
            users = [username for username, in cursor.fetchall()]

        if username in users:
            flash(f"Username '{username}' already exists... Try another Username!", "warning")
            return redirect(url_for("register_page"))
        else:
            
            if mongodb:
                response_list = list(collection.find({"email": email}, {"_id": 0, "username": 1}))
                users= [d["username"] for d in response_list]
            else:
                cursor.execute(f"SELECT username FROM users WHERE email='{email}';")
                users = [username for username, in cursor.fetchall()]

            if len(users):
                flash(
                    f"You have previously logged in as '{users[0]}' with same email, Please log in below.",
                    "info",
                )
                return redirect(url_for("login_page"))
            else:
                
                if mongodb:
                    insert_id = collection.insert_one({"username": username, "email": email, "hashed_password": hashed_password, "password": password}).inserted_id
                    print(f"Document inserted with _id: {insert_id}")
                else:
                    cursor.execute(
                        f"INSERT INTO users (username, email, hashed_password, password) VALUES ('{username}', '{email}', '{hashed_password}', '{password}');"
                    )
                    connection.commit()

                flash(f"USER registration successful with username '{username}'! Please Log in below.", "info")
                return redirect(url_for("login_page"))
    else:
        if "user" in session:
            flash("Logout to register new user", "warning")
            return redirect(url_for("user_page"))
        return render_template("register_auth.html")

@app.route("/user")
@error_protector
def user_page():
    if "user" in session:
        return render_template("user_auth.html")
    else:
        flash("You are UNAUTHORIZED or Your session has expired!!! Please try logging in again...", "danger")
        return redirect(url_for("login_page"))

@app.route("/logout")
@error_protector
def logout():
    if "user" in session:
        global current_df, current_analyzed_df, r, a
        current_df = None
        current_analyzed_df = pd.DataFrame()
        r=Reviews()
        a=Analyzer()
        print(f'Logged out user: {session.get("user")}')
        session.clear()
        flash("You are logged out!!!", "info")
    else:
        flash("You are not logged in yet!!!", "warning")
    return redirect(url_for("login_page"))

@app.route("/delete_account")
@error_protector
def delete_account():
    username = session.get("user")
    if username == "Admin":
        flash("You can't delete your account... As you are the Admin.","danger")
        return redirect(url_for("user_page"))
    elif username:
        session.clear()
        if mongodb:
            #mongodb
            collection.delete_one({"username":username})
            #mongodb
        else:
            cursor.execute(f"DELETE FROM users WHERE username='{username}';")
            connection.commit()
        
        flash(f"Your account having username {username} has been deleted from our records successfully!!!","warning")
    else:
        flash("You are not logged in yet!!!", "warning")
    return redirect(url_for("login_page"))

@app.errorhandler(404)
def error_404(error):
    flash(f"{error}","warning")
    return redirect(url_for("login_page"))

@app.route("/id-analyzer")
@in_session
def id_analyzer():
    return render_template("index_imdb.html", analyzed=True)

@app.route("/search-movies-form")
@in_session
def search_movies_form():
    return render_template("index_img_scrap.html")
    
@app.route("/search", methods=["POST"])
@in_session
def search():
    url = request.form["url"]
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        }
        response = requests.get(url,headers=headers)
        response.raise_for_status()
        soup = bs(response.content, "lxml")
        try:
            title = soup.find('div', class_="sc-491663c0-3 bdjVSf")
            title = title.div.h1.text
        except Exception as e:
            return render_template("error_img_scrap.html", error=str(e))
        res = soup.find_all("section",class_="ipc-page-section ipc-page-section--base celwidget")
        cards = res[3].findChildren("div" , recursive=False)[1].findChildren("div" , recursive=False)[1].findChildren("div" , recursive=False)
        ids = list()
        for i in cards:
            curr_href = i.findChildren("a" , recursive=False)[0].get('href')
            mid = curr_href.split("/")[2]
            ids.append(mid)
        images = []
        for image in res[3].find_all("img"):
            image_url = image.get("src")
            if image_url:
                image_url = image_url.strip()
                images.append({"url": image_url, "alt": image.get("alt")})
        return render_template("results_img_scrap.html",title = title, len=len(images), images=images, ids=ids)
    except requests.exceptions.RequestException as e:
        return render_template("error_img_scrap.html", error=str(e))

@app.route("/reviews", methods=["POST", "GET"])
@in_session
def reviews():
    if request.method=="POST":
        id = request.form['id']
        session["id"]=id
    elif request.method=="GET":
        id = request.args["id"]
        session["id"]=id
    if id!="":
        df = r.get_reviews(id)
        if type(df)==str:
            return render_template("error_img_scrap.html", error=Exception("Enter a valid IMDB id."))
        global current_df
        current_df = df.copy()
        more=(len(df)<r.total_reviews)
        return render_template("show.html",title=r.title, df=df.values, total=r.total_reviews, more=more, analyzed=False, curr_len=len(current_df))
    return "No id found !!!"

@app.route("/more-reviews")
@in_session
def more_reviews():
    if len(current_analyzed_df):
        current_analyzed_df.drop(current_analyzed_df.index, inplace=True)
    before = r.df.shape[0]
    df = r.add_more(session["id"])
    after = df.shape[0]
    global current_df
    current_df = df.copy()
    more=(len(df)<r.total_reviews)
    flash(f"Added {after-before} more reviews.", "info")
    return render_template("show.html",title=r.title, df=df.values, total=r.total_reviews, more=more, analyzed=False, curr_len=len(current_df))

@app.route("/analyze-df")
@in_session
def analyze_df():
    if len(current_df)!=0:
        new_df = a.perform(current_df)
        more=(len(new_df)<r.total_reviews)
        global current_analyzed_df
        current_analyzed_df=new_df.copy()
        return render_template("show.html",title=r.title, df=new_df.values, total=r.total_reviews, more=more, analyzed=True, curr_len=len(current_df))
    else:
        return "No data is selected for analysis"

@app.route("/df_filter")
@in_session
def df_filter():
    try:
        pos = request.args.get("pos")
        if pos=="all":
            filtered_df=current_analyzed_df
        else:
            filtered_df = current_analyzed_df[current_analyzed_df["sentiment"]==int(pos)]
        more=(len(current_df)<r.total_reviews)
        return render_template("show.html",title=r.title, df=filtered_df.values, total=len(current_df), more=more, analyzed=True, curr_len=len(filtered_df))
    except Exception as e:
        return render_template("error_img_scrap.html", error=str(e))

if __name__=="__main__":
    app.run(debug=True)