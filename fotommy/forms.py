# -*- coding: utf-8 -*-

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, RadioField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Email

from flask_wtf.file import FileField, FileRequired
from werkzeug.utils import secure_filename

# from markupsafe import Markup
from flask import Markup


class RegisterForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    want_newsletter = BooleanField('Newsletter')
    submit = SubmitField('Create account')

class AccountEditForm(FlaskForm):
    newpassword = PasswordField('New password', validators=[DataRequired()])
    submit = SubmitField('Change password')

class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class CommentForm(FlaskForm):
    author = StringField('Author', validators=[DataRequired()])
    text = TextAreaField('Text', validators=[DataRequired()])
    visibility = RadioField('Label',
        choices = [
            ('admin', u'<b>Private:</b> For you and Amélie'),
            ('public', u'<b>Public:</b> For everybody')
            ],
        default = 'admin'
        )
    submit = SubmitField('Post')

class IncreaseLikeForm(FlaskForm):
    pass

class CreatePostForm(FlaskForm):
    text = TextAreaField('Text', validators=[DataRequired()])
    submit = SubmitField('Submit')
    photos = FileField('Photos')

class EditPostForm(FlaskForm):
    text = TextAreaField('Text', validators=[DataRequired()])
    submit = SubmitField('Edit')

class EditCommentForm(FlaskForm):
    text = TextAreaField('Text', validators=[DataRequired()])
    submit = SubmitField('Edit')
    visibility = RadioField('Label',
        choices = [
            ('admin', u'<b>Private:</b> For you and Amélie'),
            ('public', u'<b>Public:</b> For everybody')
            ],
        default = 'admin'
        )


