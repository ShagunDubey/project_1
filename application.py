import os

from flask import Flask, session,render_template,request,url_for,redirect,flash,jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import requests
# from dotenv import load_dotenv

# load_dotenv('.env')

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register",methods=["GET","POST"])
def register():
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        if not name:
            return render_template("error.html",message = "Please provide your name")
        username = request.form.get("username")
        if not username:
            return render_template("error.html",message = "Please provide a username")
        userCheck = db.execute("SELECT * FROM users WHERE username = :username",
                          {"username":username}).fetchone()

        # Check if username already exists
        if userCheck:
            flash('An error occurred!', "error")
            return render_template("error.html", message="Username already exists. Please try again with another username.")
        
        password = request.form.get("password")
        if not password:
            return render_template("error.html",message = "Please provide a password")
        confirm = request.form.get("confirm")
        #if password and its confirmation do not match
        if not confirm or confirm!=password:
            flash('An error occurred!', "error")
            return render_template("error.html",message="Passwords do not match.")
        else:
            db.execute("INSERT INTO users(name,username,password) VALUES(:name,:username,:password)",{"name":name,"username":username,"password":password})
            db.commit() 
            flash('Account created successfully. Please login now.', "success")
            return render_template("login.html",message="Success")
    else:
        return render_template("register.html")

@app.route("/login",methods=["GET","POST"])
def login():
    session.clear()
    if request.method == "POST":
        username = request.form.get("username")
        password=request.form.get("password")

        getuser = db.execute("SELECT * FROM users WHERE username=:username",{"username":username}).fetchone()

        if getuser == None:
            flash('An error occurred!', "error")
            return render_template("error.html",message="User not found. Have you signed up yet?")
        elif getuser[3] != password:
            flash('An error occurred!', "error")
            return render_template("login.html",message="Incorrect password. Please try again.")
        else:
            session["log"] = True
            session["user_id"] = getuser[0]
            session["username"] = getuser[1]
            print(session['log'])
            flash("You have logged in successfully!","success")
            return redirect("/")
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    session["log"] = False
    session.clear()
    flash("You have logged out successfully!","success")
    return redirect(url_for('index'))

@app.route("/search",methods=["GET"])
def search():
    if session.get("log"):
        user_search = request.args.get("search")
        if not user_search:
            flash("Invalid search query! Please try again","error")
            return redirect("/")
        else:
            query = "%" + user_search + "%"
            # query=query.title()
            books = db.execute("SELECT isbn,title,author,year from books where LOWER(isbn) LIKE LOWER(:query) OR LOWER(title) LIKE LOWER(:query) OR LOWER(author) LIKE LOWER(:query)",{"query":query})
            if books.rowcount == 0:
                flash("No related searches!Please try again.","error")
                return redirect("/")
            else:
                result = books.fetchall()
                return render_template("result.html",result=result)
    else:
        flash("Please login first","error")
        return render_template("login.html")

@app.route("/search/<isbn>",methods=["GET","POST"])
def book(isbn):
    if session.get("log"):
        if request.method == "POST":
            curr_usr = session["user_id"]
            rating = request.form.get("rating")
            comment = request.form.get("comment")

            check_prev = db.execute("SELECT * FROM reviews WHERE user_id=:user_id and isbn=:isbn",{"user_id":curr_usr,"isbn":isbn})
            if check_prev.rowcount == 1:
                flash("Sorry!You have already submitted a review for this book.","error")
                return redirect("/search/"+isbn)

            rating = (int)(rating)
            db.execute("INSERT INTO reviews (user_id,isbn,comment,rating) VALUES(:user_id,:isbn,:comment,:rating)",{"user_id":curr_usr,"isbn":isbn,"comment":comment,"rating":rating})
            db.commit()
            flash("Review submitted successfully!","success")
            return redirect("/search/"+isbn)
        else:
            info = db.execute("SELECT isbn,title,author,year FROM books WHERE isbn=:isbn",{"isbn":isbn}).fetchall()
            key = os.getenv("GOODREADS_KEY")
            req = requests.get("https://www.goodreads.com/book/review_counts.json",params={"key": key, "isbns": isbn})
            if req.status_code !=200:
                raise ValueError
            response = req.json()
            response=response['books'][0]
            info.append(response)
            reviews = db.execute("SELECT users.name,reviews.comment,reviews.rating,reviews.date FROM users,reviews,books WHERE users.user_id=reviews.user_id AND books.isbn=reviews.isbn and reviews.isbn=:isbn order by date",{"isbn":isbn})
            reviews = reviews.fetchall()
            return render_template("bookdetails.html",info=info,reviews=reviews)
    else:
        flash("Please login first","error")
        return render_template("login.html")

@app.route("/myreviews")
def myreviews():
    if session.get("log"):
        curr_usr = session["user_id"]
        myrev = db.execute("SELECT books.title,reviews.rating,reviews.comment,reviews.date,reviews.isbn,reviews.user_id FROM books,reviews,users WHERE books.isbn=reviews.isbn AND users.user_id=reviews.user_id AND reviews.user_id=:user_id ORDER BY reviews.date",{"user_id":curr_usr}).fetchall()
        return render_template("myreviews.html",myrev=myrev)
    else:
        flash("Please login first","error")
        return render_template("login.html")

@app.route("/myreviews/<isbn>")
def deletion(isbn):
    if session.get("log"):
        curr_usr = session["user_id"]
        db.execute("DELETE FROM REVIEWS WHERE user_id=:user_id AND isbn=:isbn",{"user_id":curr_usr,"isbn":isbn})
        db.commit()
        flash("Record deleted successfully","success")
        return redirect('/myreviews')
    else:
        flash("Please login first","error")
        return render_template("login.html")

@app.route("/api/<isbn>")
def book_api(isbn):
    if session.get("log"):
        book = db.execute("SELECT * FROM books WHERE isbn=:isbn",{"isbn":isbn}).fetchone()
        if book is None:
            return jsonify({"error": "Invalid ISBN number"}), 404
        else:
            book_api_dict = {}
            book_api_dict['title'] = book[1]
            book_api_dict['isbn'] = book[0]
            book_api_dict['author'] = book[2]
            book_api_dict['year'] = book[3]    
            key = os.getenv("GOODREADS_KEY")
            req = requests.get("https://www.goodreads.com/book/review_counts.json",params={"key": key, "isbns": isbn})
            if req.status_code !=200:
                raise ValueError
            response = req.json()
            book_api_dict['review_count'] = response['books'][0]['work_ratings_count']
            book_api_dict['average_score'] = response['books'][0]['average_rating']
            return jsonify(book_api_dict)
    else:
        flash("Please login first","error")
        return render_template("login.html")

if __name__ == "__main__":
    app.secret_key = os.getenv("SECRET_KEY")
    app.run(debug=True)