from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import date
from forms import RegisterCafe, CreateCount, LoginForm, CommentForm
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
ckeditor = CKEditor(app)
Bootstrap(app)

# -------------------- CONNECT TO DATABASE -------------------- #
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "sqlite:///cafes.db")
app.config['SQLALCHEMY_TRACK_MODIFICATION'] = False
db = SQLAlchemy(app)

# -------------------- CONFIG LOGIN -------------------- #
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return Users.query.filter_by(id=user_id).first()

# -------------------- ADMIN CONFIG -------------------- #
def admin_only(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if current_user.get_id() == "1":
            return func(*args, **kwargs)
        return abort(403)
    return decorated_function

# -------------------- DATABASE STRUCTURE -------------------- #
class Cafes(db.Model):
    __tablename__ = "cafe"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    map_url = db.Column(db.String(500), nullable=False)
    img_url = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    has_sockets = db.Column(db.Boolean, nullable=False)
    has_toilet = db.Column(db.Boolean, nullable=False)
    has_wifi = db.Column(db.Boolean, nullable=False)
    can_take_calls = db.Column(db.Boolean, nullable=False)
    seats = db.Column(db.String(100), nullable=False)
    coffee_price = db.Column(db.String(100), nullable=False)
    qualification = db.Column(db.Float)
    t_opinions = db.Column(db.Integer)
    stars = db.Column(db.String(50), nullable=False)
    comments = relationship("Comments", back_populates="parent_cafe")

    def __repr__(self):
        return f"<Cafe {self.name}>"

class Users(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(500), nullable=False)
    comments = relationship("Comments", back_populates="comment_author")

    def __repr__(self):
        return f"<User {self.name}>"

class Comments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    cafe_id = db.Column(db.Integer, db.ForeignKey("cafe.id"))
    body = db.Column(db.String(500), nullable=True)
    date = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    comment_author = relationship("Users", back_populates="comments")
    parent_cafe = relationship("Cafes", back_populates="comments")

    def __repr__(self):
        return f"<Comment id {self.id}>"

# -------------------- PAGES -------------------- #
# List of all cafes
@app.route("/")
def get_all_cafes():
    data = db.session.query(Cafes).all()
    return render_template("index.html", data=data, title='Coffee & Wifi', current_user=current_user)

@app.route("/cafe/<int:cafe_id>", methods=["GET", "POST"])
def show_cafe(cafe_id):
    current_cafe = db.session.query(Cafes).get(cafe_id)
    all_comments = db.session.query(Comments).filter_by(cafe_id=cafe_id).all()
    comment = CommentForm()
    can_comment = True
    for c in all_comments:
        if current_user.get_id() == str(c.author_id):
            can_comment = False
            break

    if comment.validate_on_submit():
        new_comment = Comments(author_id=current_user.get_id(),
                               cafe_id=cafe_id,
                               body=comment.body.data,
                               date=date.today().strftime("%B %d, %Y"),
                               score=len(comment.score.data))
        db.session.add(new_comment)

        # Change stats of current café
        qualification = len(comment.score.data)
        total_opinions = len(all_comments) + 1
        for s in all_comments:
            qualification += s.score
        qualification /= total_opinions
        stars = "★" * int(qualification) + "☆" * (5 - int(qualification))

        current_cafe.qualification = qualification
        current_cafe.t_opinions = total_opinions
        current_cafe.stars = stars
        db.session.commit()

        return redirect(url_for("show_cafe", cafe_id=cafe_id))
    return render_template("current_cafe.html", data=current_cafe, all_comments=all_comments, form=comment,
                           can_comment=can_comment, title=f'{current_cafe.name} | Coffe & Wifi',
                           current_user=current_user)

@app.route("/register-cafe", methods=["GET", "POST"])
@login_required
def register_cafe():
    form = RegisterCafe()

    if form.validate_on_submit():
        if Cafes.query.filter_by(name=form.name.data).first():
            flash("This cafe has already been registered.")
        else:
            new_cafe = Cafes(name=form.name.data,
                             location=form.location.data,
                             map_url=form.map_url.data,
                             seats=form.seats.data,
                             img_url=form.img_url.data,
                             coffee_price=form.coffee_price.data,
                             has_wifi=form.has_wifi.data,
                             has_toilet=form.has_toilet.data,
                             has_sockets=form.has_sockets.data,
                             can_take_calls=form.can_take_calls.data,
                             qualification=0.0,
                             t_opinions=0,
                             stars="☆☆☆☆☆")
            db.session.add(new_cafe)
            db.session.commit()
            return redirect(url_for("get_all_cafes"))
    return render_template("add_cafe.html", form=form, toedit=False, title="Register Cafe | Coffe & Wifi")

@app.route("/edit-cafe/<int:cafe_id>", methods=["GET", "POST"])
@login_required
def edit_current(cafe_id):
    edit_cafe = db.session.query(Cafes).get(cafe_id)
    form = RegisterCafe(name=edit_cafe.name,
                        location=edit_cafe.location,
                        map_url=edit_cafe.map_url,
                        seats=edit_cafe.seats,
                        img_url=edit_cafe.img_url,
                        coffee_price=float(edit_cafe.coffee_price[1:]),
                        has_wifi=edit_cafe.has_wifi,
                        has_sockets=edit_cafe.has_sockets,
                        has_toilet=edit_cafe.has_toilet,
                        can_take_calls=edit_cafe.can_take_calls)

    if form.validate_on_submit():
        edit_cafe.name = form.name.data
        edit_cafe.location = form.location.data
        edit_cafe.map_url = form.map_url.data
        edit_cafe.seats = form.seats.data
        edit_cafe.img_url = form.img_url.data
        edit_cafe.coffee_price = f"£{form.coffee_price.data}"
        edit_cafe.has_wifi = form.has_wifi.data
        edit_cafe.has_sockets = form.has_sockets.data
        edit_cafe.has_toilet = form.has_toilet.data
        edit_cafe.can_take_calls = form.can_take_calls.data

        db.session.commit()
        return redirect(url_for("show_cafe", cafe_id=edit_cafe.id))

    return render_template("add_cafe.html", form=form, toedit=True, title="Edit Cafe | Coffe & Wifi",
                           current_user=current_user)

@app.route("/delete-cafe/<int:cafe_id>")
@login_required
@admin_only
def delete_cafe(cafe_id):
    print("Entre!")
    comments_to_delete = Comments.query.filter_by(cafe_id=cafe_id).all()
    for comment in comments_to_delete:
        db.session.delete(comment)
    to_delete = Cafes.query.get(cafe_id)
    db.session.delete(to_delete)
    db.session.commit()
    print("Lo borre!")
    return redirect(url_for("get_all_cafes"))

@app.route("/create-count", methods=["GET", "POST"])
def create_count():
    form = CreateCount()
    if form.validate_on_submit():
        if Users.query.filter_by(email=form.email.data).first():
            flash("This email is already registered.")
        else:
            new_user = Users()
            new_user.name = form.name.data
            new_user.email = form.email.data
            new_user.password = generate_password_hash(form.password.data)

            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for("get_all_cafes"))
    return render_template("create_count.html", form=form, title="Register | Coffee & Wifi",
                           current_user=current_user)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        # Check email in Users table on the database
        if user:
            # Check password
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for("get_all_cafes"))
            else:
                flash("Wrong password")
        else:
            flash("This email isn't registered")
    return render_template("login.html", form=form, title="Login | Coffee & Wifi", current_user=current_user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for("get_all_cafes"))


if __name__ == "__main__":
    app.run(debug=True)
