import os
import requests

# Flask imports
from flask import Flask, render_template, request, url_for, redirect
from flask_pymongo import PyMongo

from bson.objectid import ObjectId

if os.path.exists('secrets.py'):
    import secrets

app = Flask(__name__)

app.config['MONGODB_NAME'] = os.environ.get('MONGODB_NAME')
app.config['MONGO_URI'] = os.environ.get('MONGO_URI')

mongo = PyMongo(app)

#Define Search function to GET information from OpenLibrary API
def search_result(search_text):
    resp = requests.get(
        url='http://openlibrary.org/search.json?q=' + search_text)
    result = resp.json()

#Get results from API in JSON format
    search = result['docs']
    result_list = []
#Sort results in loop to collect 10 items and store them in an object
    i = 0
    for item in search:
        if (i == 10):
            break
        i += 1
        isbn = item.get('isbn')
        if isbn is not None:
            isbn = isbn[0]
        authors = item.get('author_name')
        authors = authors[:4]
        obj = {
            "title": item.get('title'),
            "author": authors,
            'isbn': isbn,
            'image': 'http://covers.openlibrary.org/b/isbn/{}-M.jpg'.format(isbn),
            #Use ISBN of selected books and pass them as arguements to COVERS API to get an image (if it exists)
        }
        result_list.append(obj)

    return result_list

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/results", methods=["POST"])
def results():
    if request.method == "POST":
        search_text = request.form['search']
        return render_template("results.html", book_results=search_result(search_text))

# Display singular book information as selected by User from Results page

@app.route("/book/<isbn>")
def book(isbn):
    url = "https://openlibrary.org/api/books?bibkeys=ISBN:{}".format(isbn) + "&format=json&jscmd=data"
    resp = requests.get(url=url)
    info = resp.json()
    info = info['ISBN:{}'.format(isbn)]
    authors = []
    publishers = []
    subjects = []
    if info.get('authors'):
        for item in info.get('authors'):
            authors.append(item.get('name'))
    if info.get('publishers'):
        for item in info.get('publishers'):
            publishers.append(item.get('name'))
    if info.get('subjects'):
        for item in info.get('subjects'):
            publishers.append(item.get('name'))
    review_list = []

# Find any existing reviews in MongoDB
#    get_reviews = Reviews.find({'ISBN': isbn})
#    for review in get_reviews:
#        review_list.append(review)

# Get image for selected book
    image = info.get('cover')
    if image:
        image = image.get('medium')
    return render_template("book.html", book=info, reviews=review_list, isbn=isbn, image=image, authors=authors,
                           publishers=publishers, subjects=subjects)

#Review Functions to create, retrieve, update and delete records in MongoDB
@app.route("/submit_review", methods=["POST"])
def submit_review():
    isbn = request.form.get('isbn')
    review = {'username': request.form.get('username'),
              'comments': request.form.get('review'),
              'ISBN': isbn,
              'rating': int(request.form.get('rating'))}
    Reviews.insert_one(review)
    return redirect(url_for('book', isbn=isbn))

if __name__ == "__main__":
    app.run(debug=True)
