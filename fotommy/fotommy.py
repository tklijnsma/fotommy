# all the imports
import os, glob
import sqlite3
from flask import (
    Flask, request, session, g, redirect, url_for, abort,
    render_template, flash,
    send_from_directory
    )
from flask_sqlalchemy import SQLAlchemy
import click
import logging
logging.getLogger().setLevel(logging.INFO)

app = Flask(__name__) # create the application instance :)
app.config.from_object(__name__) # load config from this file , flaskr.py

from flask_wtf.csrf import CsrfProtect
CsrfProtect(app)

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

@app.cli.command()
def show_albums():
    print dbmanager.all_albums()

@app.cli.command()
def show_comments():
    for comment in dbmanager.all_comments():
        print comment

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










