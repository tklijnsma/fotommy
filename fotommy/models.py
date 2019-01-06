# -*- coding: utf-8 -*-

import os
from fotommy import db, app

posts = db.Table(
    'posts',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
    db.Column('photo_id', db.Integer, db.ForeignKey('photo.id'), primary_key=True)
    )

class Post(db.Model):
    __table_args__ = {'extend_existing': True} 

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime(), nullable=True)
    text = db.Column(db.String(1000), nullable=False)

    n_likes = db.Column(db.Integer, nullable=False, default=0)
    comments = db.relationship('Comment')
    photos = db.relationship('Photo', secondary=posts)


class Photo(db.Model):
    __table_args__ = {'extend_existing': True} 

    id = db.Column(db.Integer, primary_key=True)
    imgpath_full      = db.Column(db.String(120), nullable=False)
    imgpath_medium    = db.Column(db.String(120), unique=True, nullable=False)
    imgpath_thumbnail = db.Column(db.String(120), unique=True, nullable=False)

    album_id = db.Column(db.Integer, db.ForeignKey('album.id'), nullable=False)
    album = db.relationship(
        'Album',
        backref=db.backref('photos', lazy=True)
        )

    comments = db.relationship('Comment')
    posts = db.relationship('Post', secondary=posts)

    n_likes = db.Column(db.Integer, nullable=False, default=0)
    creation_date = db.Column(db.DateTime(), nullable=True)

    def __repr__(self):
        return '<Photo %r>' % self.imgpath_full

    def imgrelpath_thumbnail(self):
        return os.path.relpath(self.imgpath_thumbnail, os.path.join(app.root_path, 'static'))

    def imgrelpath_medium(self):
        return os.path.relpath(self.imgpath_medium, os.path.join(app.root_path, 'static'))

    def n_comments(self):
        return len(self.comments)


class Album(db.Model):
    __table_args__ = {'extend_existing': True} 

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return '<Album %r>' % self.name

    def repr_elaborate(self):
        r = self.__repr__()
        if len(self.photos) > 0:
            r += '\n  ' + '\n  '.join([ '{0}: {1}'.format(p.id, p.imgpath_full) for p in self.photos])
        else:
            r += ' (no photos)'
        return r

    def n_photos(self):
        return len(self.photos)

    def n_photos_str(self):
        n_photos = self.n_photos()
        if n_photos == 1:
            photo_str = 'photo'
        else:
            photo_str = 'photos'
        return '{0} {1}'.format(n_photos, photo_str)


class Comment(db.Model):
    __table_args__ = {'extend_existing': True} 

    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(50), nullable=False)
    text = db.Column(db.String(400), nullable=False)

    photo_id = db.Column(db.Integer, db.ForeignKey('photo.id'))
    photo = db.relationship("Photo", back_populates="comments") # not totally necessary

    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    post = db.relationship("Post", back_populates="comments") # not totally necessary

    def __repr__(self):
        short_text = self.text[:10] + '...' if len(self.text) > 13 else self.text
        return '< #{0} Comment by \'{1}\': \'{2}\'>'.format(self.id, self.author, short_text)

