# -*- coding: utf-8 -*-

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired

from flask_wtf.file import FileField, FileRequired
from werkzeug.utils import secure_filename

# from markupsafe import Markup
from flask import Markup


# class LoginForm(FlaskForm):
#     username = StringField('Username', validators=[DataRequired()])
#     password = PasswordField('Password', validators=[DataRequired()])
#     remember_me = BooleanField('Remember Me')
#     submit = SubmitField('Sign In')

class CommentForm(FlaskForm):
    author = StringField('Author', validators=[DataRequired()])
    text = TextAreaField('Text', validators=[DataRequired()])
    submit = SubmitField('Post')


class IncreaseLikeForm(FlaskForm):
    pass
    # submit = SubmitField(
    #     'Nice'
    #     # Markup('<span title="nice"><i class="fas fa-heart"></i></span>')
    #     )


class CreatePostForm(FlaskForm):
    secretpassword = StringField('Secretpassword', validators=[DataRequired()])
    text = TextAreaField('Text', validators=[DataRequired()])
    submit = SubmitField('Submit')
    photos = FileField('Photos')
