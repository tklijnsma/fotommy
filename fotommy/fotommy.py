# -*- coding: utf-8 -*-

import os, glob
import sqlite3
from flask import (
    Flask, request, session, g, redirect, url_for, abort,
    render_template, flash,
    send_from_directory
    )
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import werkzeug.security
import click
import logging
logging.getLogger().setLevel(logging.INFO)
logging._defaultFormatter = logging.Formatter(u"%(message)s")

app = Flask(__name__) # create the application instance
app.config.from_object(__name__) # load config from this file

from flask_wtf.csrf import CsrfProtect
CsrfProtect(app)

login_manager = LoginManager()
login_manager.init_app(app)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'fotommy.db'),
    SECRET_KEY='development key',
    SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(app.root_path, 'fotommy.db'),
    SQLALCHEMY_TRACK_MODIFICATIONS = False,
    PHOTOPATH=os.path.join(app.root_path, 'static/photos'),
    UPLOADED_PHOTOS_DEST=os.path.join(app.root_path, 'static/uploads'),
    ))
app.config.from_envvar('FOTOMMY_SETTINGS', silent=True)

db = SQLAlchemy(app)
if not os.path.isdir(app.config['PHOTOPATH']):
    os.makedirs(app.config['PHOTOPATH'])
if not os.path.isdir(app.config['UPLOADED_PHOTOS_DEST']):
    os.makedirs(app.config['UPLOADED_PHOTOS_DEST'])

import models, factories
dbmanager = factories.DBManager(db)

@login_manager.user_loader
def load_user(user_id):
    # return User.get(user_id)
    users = db.session.query(models.User).filter_by(id=user_id).all()
    if len(users) == 0:
        return None
    else:
        return users[0]


# Dropzone settings
from flask_dropzone import Dropzone
dropzone = Dropzone(app)
app.config['DROPZONE_UPLOAD_MULTIPLE'] = True
app.config['DROPZONE_ALLOWED_FILE_CUSTOM'] = True
app.config['DROPZONE_ALLOWED_FILE_TYPE'] = 'image/*'
app.config['DROPZONE_UPLOAD_ON_CLICK'] = True
app.config['DROPZONE_REDIRECT_VIEW'] = 'createpost' # This redirects immediately after uploading... not the wanted interaction



@app.cli.command()
def init_db():
    db.create_all()
    db.session.commit()

    public_group = models.Group(name='public')
    db.session.add(public_group)

    admin_group = models.Group(name='admin')
    db.session.add(admin_group)

    kennis_group = models.Group(name='kennis')
    db.session.add(kennis_group)

    with open(os.path.join(app.root_path, 'pw.txt'), 'r') as fp:
        pw = fp.read().strip()

    admin_user  = models.User(
        email = 'thomasklijnsma@gmail.com',
        pwhash = werkzeug.security.generate_password_hash(pw)
        )
    admin_user.groups.append(admin_group)
    db.session.add(admin_user)

    kennis_user  = models.User(
        email = 'tklijnsm@gmail.com',
        pwhash = werkzeug.security.generate_password_hash(pw)
        )
    kennis_user.groups.append(kennis_group)
    db.session.add(kennis_user)

    album = models.Album(name='uploads')
    db.session.add(album)

    db.session.commit()

@app.cli.command()
def show_users():
    for user in dbmanager.all_users(): print user

@app.cli.command()
def show_groups():
    for group in dbmanager.all_groups(): print group

@app.cli.command()
def show_albums():
    print dbmanager.all_albums()

@app.cli.command()
@click.argument('useremail', required=False)
def show_comments(useremail=None):
    if useremail is None:
        comments = dbmanager.all_comments()
    else:
        user = dbmanager.user_by_email(useremail)
        posts = dbmanager.new_posts()
        comments = []
        for post in posts:
            comments.extend(post.comments_for_user(user))
    for comment in comments:
        print comment

@app.cli.command()
@click.argument('useremail', required=False)
def show_new_posts(useremail=None):
    if useremail is None:
        posts = dbmanager.new_posts()
    else:
        user = dbmanager.user_by_email(useremail)
        posts = dbmanager.new_posts_for_user(user)
    for post in posts:
        print post

@app.cli.command()
@click.argument('comment_id')
def del_comment(comment_id):
    dbmanager.delete_comment(comment_id)

@app.cli.command()
@click.argument('album_name')
def show_album(album_name):
    album = dbmanager.album_by_name(album_name)
    print album.repr_elaborate()

@app.cli.command()
@click.argument('album_name')
def new_album(album_name):
    albumfactory = factories.AlbumFactory()
    albumfactory.create(album_name)

@app.cli.command()
@click.argument('album_name')
def delete_album(album_name):
    albumfactory = factories.AlbumFactory()
    albumfactory.delete(album_name)


@app.cli.command()
@click.argument('album_name')
@click.argument('imgpath_full')
def add_photo_to_album(album_name, imgpath_full):
    _util_add_photo_to_album(album_name, imgpath_full)

@app.cli.command()
@click.argument('album_name', nargs=1)
@click.argument('imgpaths_full', nargs=-1)
def add_photos_to_album(album_name, imgpaths_full):
    for imgpath_full in imgpaths_full:
        _util_add_photo_to_album(album_name, imgpath_full)

def _util_add_photo_to_album(album_name, imgpath_full):
    album = dbmanager.album_by_name(album_name, fail_if_not_existing=True)
    imgpath_full = os.path.abspath(imgpath_full)
    factory = factories.PhotoFactory(album)
    factory.create(imgpath_full)


import views










