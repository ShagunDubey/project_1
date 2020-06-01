# Project 1

Web Programming with Python and JavaScript

Project 1 : Books
A book review website with the name Bibliophilic Me has been created. It allows the users to register with the website. The users can then login to their account and search for a book using its title, author or ISBN number. Incomplete search queries show all related searches. The search page has a link to each of the book pages where the user can see the goodreads review, reviews by other people, and also leave a rating and comment if needed. He/She can also make an api request which returns a json object if found, else a 404 error. Also, the past reviews made can be seen, and delete one if the user wishes to. The user can then logout.

application.py - main application
import.py - to import the books from the given csv file
layout.html - basic html layout which is extended in the other html files
index.html - defines appearance of home page when user is logged in and not logged in
register.html - contains form for user to register
login.html - contains login page
result.html -  shows the search results when user searches for a book
bookdetails.html - shows the details of each book page
myreviews.html - shows the users their past reviews made and allows them to delete the review they want
error.html - a general error template 

static folder - has two files- styles.css and login.css, and an images folder

Database has three tables - books, users and reviews

Table structure:
books: isbn(primary key),title, author, year
users: user_id(primary key), username, name, password
reviews: isbn,user_id,rating,comment,date --- Primary key(isbn,user_id)
