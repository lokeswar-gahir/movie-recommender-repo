print("importing dependencies...", end="")
from bs4 import BeautifulSoup as bs
import random
import pandas as pd
from requests_html import HTMLSession
import regex as re
from sentiment_analyzer import Analyzer
import requests
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
from datetime import timedelta, datetime

print("\nConnecting to Database...", end="")
try:
    connection = pymysql.connect(
        host="localhost", user="root", password="root", database="auth_db"
    )
    cursor = connection.cursor()
except Exception as e:
    print("\n"+e)
    exit(0)
print("done.")

class Reviews:
    def __init__(self):
        self.df = pd.DataFrame(columns=["username","date","content"])
        self.key=None
        self.soup=None
        self.title=None
        self.total_reviews=None
        self.session = HTMLSession()
    def get_headers(self):
        user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0",
        "Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0",
        "Mozilla/5.0 (X11; Linux x86_64; rv:95.0) Gecko/20100101 Firefox/95.0"
        ]

        random_user_agent = random.choice(user_agents)
        headers = {
            'User-Agent': random_user_agent
        }
        return headers
    def get_reviews(self, imdb_id):
        if len(self.df)>0:
            clean_df(self.df)
        url="https://www.imdb.com/title/"+str(imdb_id)+"/reviews"
        print("Requesting...", end="")
        for _ in range(10):
            r = self.session.get(url, headers=self.get_headers())
            if r.status_code==200:
                break
            print(f"\n({r.status_code})Requesting again...",end="")

        print("done.")
        self.soup = bs(r.html.html, "html.parser")
        lister_list = self.soup.find("div", class_="lister-list")
        total_reviews_div = self.soup.find("div", class_="header")
        self.title = self.soup.find("div",class_="parent").text.strip().replace(" ", "").replace("\n"," ")
        print(self.title)
        self.total_reviews = int(total_reviews_div.div.text.split()[0].replace(",",""))
        print(self.get_df(lister_list))
        print(f"Total number of reviews are: {self.total_reviews}")
        if self.total_reviews<25:
            # close_conn(r)
            return self.df
        # close_conn(r)
        return self.df
    def add_more(self,imdb_id):
        url = f"https://www.imdb.com/title/{imdb_id}/reviews/_ajax?ref_=undefined&paginationKey={self.key}"
        # print(url)
        # return "done"
        print("Requesting...", end="")
        count=0
        while True:
            r =self.session.get(url, headers=self.get_headers())
            if r.status_code==200:
                break
            print("\nRequesting again...",end="")
            if count>=20:
                return "requested more than 20 times and still got nothing !!!"
            count+=1
        print("done.")
        self.soup = bs(r.html.html, "html.parser")
        lister_list = self.soup.find("div", class_="lister-list")
        print(self.get_df(lister_list))
        print(f"Total number of reviews are: {self.total_reviews}")
        return self.df

    def get_df(self, lister_list):
        rev_list = lister_list.find_all("div", class_= "imdb-user-review")
        if len(rev_list):
            for item in rev_list:
                row=list()
                name_date = item.div.div.find("div", class_="display-name-date")
                spans = name_date.find_all("span")
                content = item.div.div.find("div", class_="content")
                row.append(spans[0].text.replace("\n",""))
                row.append(spans[1].text.replace("\n",""))
                row.append(str(content.div.text.replace("\n","")))
                if len(self.df)<self.total_reviews:
                    self.df.loc[len(self.df)+1]=row
                else:
                    return self.df
            try:
                more = self.soup.find("div", class_="load-more-data")
                pat = r'data-key="(.[^"]+)'
                global key
                self.key = re.findall(pat, str(more))[0]
                # print(f"New key is set: ({self.key})")
            except IndexError:
                print(f"New key not found or is not set !!!")
            return self.df
        else:
            print("No reviews found !!!")
        
    def close_conn(self):
        self.session.close()
        print("Session Closed.")
def clean_df(df):
    if len(df)!=0:
        df.drop(df.index, inplace=True)
        print("document cleaned.")
    else:
        print("There is no data to delete !!!")



def in_session(func):
    @wraps(func)
    def inner():
        if "user" in session:
            try:
                return func()
            except Exception as e:
                return render_template("error_img_scrap.html", error=str(e))
        else:
            flash("Looks like your session has expired","warning")
            return redirect(url_for("login_page"))
    return inner

# ==================================================================================================================================================
current_df = pd.DataFrame()
current_analyzed_df = pd.DataFrame()
if __name__=="__main__":
    from flask import Flask,request, render_template, session
    app=Flask(__name__)
    app.secret_key = "something"
    app.permanent_session_lifetime = timedelta(minutes=5)
    r=Reviews()
    a=Analyzer()

    # @app.route("/")
    # def hh():
    #     return "<a href='/login'>login</a>"
    
    @app.route("/")
    @app.route("/login", methods=["GET", "POST"])
    def login_page():
        if request.method == "POST":
            email = request.form.get("email")
            password = request.form.get("password")
            cursor.execute(f"SELECT email FROM users;")
            user_emails = [user_email for user_email, in cursor.fetchall()]
            if email in user_emails:
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
    def register_page():
        if request.method == "POST":
            username = request.form.get("username")
            email = request.form.get("email")
            password = request.form.get("password")
            hashed_password = generate_password_hash(password)
            cursor.execute(f"SELECT username FROM users WHERE username='{username}';")
            users = [username for username, in cursor.fetchall()]
            if username in users:
                flash(f"Username '{username}' already exists... Try another Username!", "warning")
                return redirect(url_for("register_page"))
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
    def user_page():
        if "user" in session:
            return render_template("user_auth.html")
        else:
            flash("You are UNAUTHORIZED or Your session has expired!!! Please try logging in again...", "danger")
            return redirect(url_for("login_page"))

    @app.route("/logout")
    def logout():
        if "user" in session:
            session.clear()
            flash("You are logged out!!!", "info")
        else:
            flash("You are not logged in yet!!!", "warning")
        return redirect(url_for("login_page"))
    
    @app.route("/delete_account")
    def delete_account():
        username = session.get("user")
        if username == "Admin":
            flash("You can't delete your account... As you are the Admin.","danger")
            return redirect(url_for("user_page"))
        elif username:
            session.clear()
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
            print("from reviews: " ,session)
            if type(df)==str:
                return render_template("error_img_scrap.html", error=Exception("Enter a valid IMDB id."))
            global current_df
            # current_df = a.perform(df)
            current_df = df.copy()
            more=(len(df)<r.total_reviews)
            return render_template("show.html",title=r.title, df=df.values, total=r.total_reviews, more=more, analyzed=False, curr_len=len(current_df))
        return "No id found !!!"
    
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
                return render_template("error_img_scrap.html", error=e)
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

    app.run(debug=True)
    