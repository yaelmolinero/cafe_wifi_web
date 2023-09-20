from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, EmailField, PasswordField, SelectField, BooleanField, FloatField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField

# -------------------- WTForms REGISTER NEW USER -------------------- #
class RegisterCafe(FlaskForm):
    name = StringField("Cafe Name:", validators=[DataRequired()])
    location = StringField("Location: ", validators=[DataRequired()])
    map_url = StringField("Map Url:", validators=[DataRequired(), URL()])
    seats = SelectField("Seats:", validators=[DataRequired()],
                        choices=["0-10", "10-20", "20-30", "30-40", "40-50", "+50"])
    img_url = StringField("Image URL:", validators=[DataRequired(), URL()])
    coffee_price = FloatField("Coffe Price: ")
    has_wifi = BooleanField("Has Wifi: ")
    has_toilet = BooleanField("Has Toilets: ")
    has_sockets = BooleanField("Has Sockets: ")
    can_take_calls = BooleanField("Can Take Calls:")

    submit = SubmitField("Submit")

# -------------------- WTForms CREATE NEW COUNT -------------------- #
class CreateCount(FlaskForm):
    name = StringField("Username:", validators=[DataRequired()])
    email = EmailField("Email:", validators=[DataRequired()])
    password = PasswordField("Password:", validators=[DataRequired()])

    submit = SubmitField("Create")

# -------------------- WTForms LOGIN USER -------------------- #
class LoginForm(FlaskForm):
    email = EmailField("Email:", validators=[DataRequired()])
    password = PasswordField("Password:", validators=[DataRequired()])

    submit = SubmitField("Login")

# -------------------- CREATE NEW COMMENT -------------------- #
class CommentForm(FlaskForm):
    score = SelectField("Do you enjoy?", validators=[DataRequired()],
                        choices=["⭐⭐⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐", "⭐⭐", "⭐"])
    body = CKEditorField("Comment:")

    submit = SubmitField("Confirm")
