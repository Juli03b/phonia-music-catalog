from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, TextAreaField, PasswordField
from wtforms.validators import Required, Optional, Length, required
from models import User, db

form_styles = {
    "input": "form-control rounded-3 my-1",
    "field": "form-control rounded-4 my-2"
}

class UserForm(FlaskForm):

    username = StringField("Username", validators=[Required('You need a username'), Length(min=5, max=15, message=' should be at least 5 characters. 15 max.')]
        , render_kw=dict(class_=form_styles["input"], autocomplete="username"))
    password = PasswordField("Password", validators=[Required('You need a password'), Length(min=6, message=' should be at least 6 characters.')]
        , render_kw=dict(class_=form_styles["input"], autocomplete="new-password"))
    full_name = StringField("Full name", validators=[Required('Enter your name'), Length(min=5, max=40)]
        , render_kw=dict(class_=form_styles["input"]))

    @classmethod
    def sign_in(cls):
        form = UserForm()
        form.password.render_kw['auto-complete'] = 'current-password'
        
        del form.full_name

        return form

class PlaylistForm(FlaskForm):

    name = StringField("Name", validators=[Required('Enter name'), Length(min=1, max=15, message=' should be at least 5 characters. 15 max.')] 
        , render_kw=dict(class_=form_styles["input"]))
    description = TextAreaField("Description", validators=[Length(max=120, message="120 characters max.")]
        , render_kw=dict(class_=form_styles["field"]))