from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float, desc
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired
import requests
import os


class Base(DeclarativeBase):
    pass


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ["Secret key"]
api_key = os.environ["Api key"]
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Movie ranking collection.db'
Bootstrap5(app)
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# CREATE DB
class Table(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    year: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True, default=0.0)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True, default=0)
    review: Mapped[str] = mapped_column(String, nullable=True, default="")
    image_url: Mapped[str] = mapped_column(String, nullable=False)


class Edit_rating(FlaskForm):
    rating = FloatField("Your rating out of 10", validators=[DataRequired()])
    review = StringField("Your review", validators=[DataRequired()])
    done = SubmitField("Done")


class Add_movie(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")


headers = {"Authorization":"eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJhNjFjN2U3OWE2MzgzYjhlMDVmYTgxOGNhN2IyMWE3ZSIsIm5iZiI6MTczNDAxMzg0Ni42MDgsInN1YiI6IjY3NWFmMzk2NTRmZDljYjlmN2I4NTk3NiIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.5TBXBnalAObVt443TMD0Ze1v4j3ejdYUhrSABzONO0o"}

@app.route("/")
def home():
    movies = db.session.execute(db.select(Table).order_by(Table.rating.desc())).scalars().all()
    for i in range(1, len(movies)):
        movies[i-1].ranking = i
    db.session.commit()
    return render_template("index.html", movies=movies)


@app.route("/edit/<movie_id>", methods=["GET", "POST"])
def update(movie_id):
    form = Edit_rating()
    title = db.session.execute(db.select(Table).where(Table.id == movie_id)).scalar().title
    if form.validate_on_submit() and request.method == "POST":
        rating = form.rating.data
        review = form.review.data
        print(rating, review)
        movie_to_update = db.session.execute(db.select(Table).where(Table.id == movie_id)).scalar()
        print(movie_to_update)
        movie_to_update.rating = rating
        # movie_to_update.review = review
        db.session.commit()
        return redirect(url_for("home"))

    return render_template("edit.html", form=form, title=title)


@app.route("/delete/<movie_id>")
def delete(movie_id):
    book_to_delete = db.session.execute(db.select(Table).where(Table.id == movie_id)).scalar()
    db.session.delete(book_to_delete)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/add", methods=["GET", "POST"])
def add():
    form = Add_movie()
    if form.validate_on_submit() and request.method == "POST":
        title = form.title.data
        return redirect(url_for("select", title=title))
    return render_template("add.html", form=form)


@app.route("/select/<title>")
def select(title):
    result = requests.get(f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={title}").json()
    # movie_ids = [item["id"] for item in result["results"]]
    # movie_titles = [item["original_title"] for item in result["results"]]
    # movie_dates = [item["release_date"] for item in result["results"]]
    return render_template("select.html", result=result)


@app.route("/<movie_id>")
def process(movie_id):
    result2 = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}").json()
    new_movie = Table(
        id=movie_id,
        title=result2["original_title"],
        image_url=f"https://image.tmdb.org/t/p/w500/{result2["poster_path"]}",
        year=result2["release_date"][:4],
        description=result2["overview"]
    )
    print(new_movie)
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for("update", movie_id=movie_id))


if __name__ == '__main__':
    app.run(debug=True)
