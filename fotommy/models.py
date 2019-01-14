# -*- coding: utf-8 -*-

import os
from fotommy import db, app, login_manager
import flask_login
from flask_login import UserMixin
import werkzeug.security


posts = db.Table(
    'posts',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
    db.Column('photo_id', db.Integer, db.ForeignKey('photo.id'), primary_key=True)
    )


groups_to_users = db.Table(
    'groups_to_users',
    db.Column('group_id', db.Integer, db.ForeignKey('group.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    )

groups_to_posts = db.Table(
    'groups_to_posts',
    db.Column('group_id', db.Integer, db.ForeignKey('group.id'), primary_key=True),
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
    )

groups_to_photos = db.Table(
    'groups_to_photos',
    db.Column('group_id', db.Integer, db.ForeignKey('group.id'), primary_key=True),
    db.Column('photo_id', db.Integer, db.ForeignKey('photo.id'), primary_key=True),
    )

groups_to_comments = db.Table(
    'groups_to_comments',
    db.Column('group_id', db.Integer, db.ForeignKey('group.id'), primary_key=True),
    db.Column('comment_id', db.Integer, db.ForeignKey('comment.id'), primary_key=True),
    )


class Group(db.Model):
    __table_args__ = {'extend_existing': True} 

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

    def __repr__(self):
        return 'Group #{0} {1}'.format(self.id, self.name)


class AuthMixin(object):
    """docstring for AuthMixin"""

    def is_public(self):
        return 'public' in [ g.name for g in self.groups  ]

    def is_public_after_auth(self):
        return 'loggedin' in [ g.name for g in self.groups  ]

    def allow(self, user):
        if self.is_public():
            return True
        elif self.is_public_after_auth() and user.is_authenticated:
            return True
        elif hasattr(self, 'user') and self.user is user:
            return True
        elif not hasattr(user, 'groups'):
            return False
        else:
            return len(set(user.groups) & set(self.groups)) > 0


def anonymous_is_admin():
    return False
flask_login.mixins.AnonymousUserMixin.is_admin = staticmethod(anonymous_is_admin)

class User(db.Model, UserMixin):
    __table_args__ = {'extend_existing': True} 

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    pwhash = db.Column(db.String(1000), nullable=False)
    want_newsletter = db.Column(db.Boolean(), nullable=False, default=True)
    comments = db.relationship('Comment')
    groups = db.relationship('Group', secondary=groups_to_users)

    def check_password(self, password):
        return werkzeug.security.check_password_hash(self.pwhash, password)

    def is_admin(self):
        if len(self.groups) > 0:
            return 'admin' in [ g.name for g in self.groups ]
        else:
            return False

    def __repr__(self):
        return 'User #{0:<3} {1} {2}'.format(self.id, self.email, self.groups)



class Post(db.Model, AuthMixin):
    __table_args__ = {'extend_existing': True} 

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime(), nullable=True)
    text = db.Column(db.String(1000), nullable=False)

    n_likes = db.Column(db.Integer, nullable=False, default=0)
    comments = db.relationship('Comment')
    photos = db.relationship('Photo', secondary=posts)
    groups = db.relationship('Group', secondary=groups_to_posts)

    def public_comments(self):
        return [ c for c in self.comments if c.is_public() ]

    def comments_for_user(self, user):
        return [ c for c in self.comments if c.allow(user) ]

    def __repr__(self):
        return 'Post #{0:<3} {1}'.format(self.id, self.groups)



class Photo(db.Model, AuthMixin):
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
    groups = db.relationship('Group', secondary=groups_to_photos)

    n_likes = db.Column(db.Integer, nullable=False, default=0)
    creation_date = db.Column(db.DateTime(), nullable=True)

    def __repr__(self):
        return 'Photo %r' % self.imgpath_full

    def comments_for_user(self, user):
        return [ c for c in self.comments if c.allow(user) ]

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
        return 'Album %r' % self.name

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


class Comment(db.Model, AuthMixin):
    __table_args__ = {'extend_existing': True} 

    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(50), nullable=False)
    text = db.Column(db.String(400), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship("User", back_populates="comments")

    photo_id = db.Column(db.Integer, db.ForeignKey('photo.id'))
    photo = db.relationship("Photo", back_populates="comments") # not totally necessary

    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    post = db.relationship("Post", back_populates="comments") # not totally necessary

    groups = db.relationship('Group', secondary=groups_to_comments)

    def __repr__(self):
        short_text = self.text[:10] + '...' if len(self.text) > 13 else self.text
        return (
            'Comment #{0} by \'{1}\'{4}: \'{2}\'; {3}'
            .format(
                self.id, self.author, short_text, self.groups,
                ' (' + self.user.email + ')' if not(self.user is None) else ''
                )
            )


