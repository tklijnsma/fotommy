# -*- coding: utf-8 -*-

import fotommy
import sys, os, logging
from fotommy import db, app
from models import *
from PIL import Image, ExifTags
import uuid
from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash

class DBManager(object):
    """docstring for DBManager"""
    def __init__(self, db):
        super(DBManager, self).__init__()
        self.db = db

    def all_users(self):
        return db.session.query(User).all()
        
    def all_albums(self):
        return db.session.query(Album).all()

    def all_photos(self):
        return db.session.query(Photo).all()

    def all_comments(self):
        return db.session.query(Comment).all()

    def all_groups(self):
        # Put admin group as last group
        groups = db.session.query(Group).all()
        admin_group = [g for g in groups if g.name == 'admin'][0]
        groups.remove(admin_group)
        groups.append(admin_group)
        return groups

    def album_by_name(self, name, fail_if_not_existing=False):
        albums = db.session.query(Album).filter_by(name=name).all()
        if len(albums) == 0:
            logging.info('No album found with name \'{0}\''.format(name))
            if fail_if_not_existing: sys.exit()
            return None
        elif len(albums) > 1:
            logging.info('Found multiple albums for name \'{0}\' (taking first): {1}'.format(name, albums))
        album = albums[0]
        return album

    def user_by_email(self, email):
        users = db.session.query(User).filter_by(email=email).all()
        if len(users) == 0:
            logging.info('No user found with email {0}'.format(email))
            return None
        else:
            return users[0]

    def user_by_id(self, id):
        users = db.session.query(User).filter_by(id=id).all()
        if len(users) == 0:
            logging.info('No user found with id {0}'.format(id))
            return None
        else:
            return users[0]

    def group_by_name(self, name):
        groups = db.session.query(Group).filter_by(name=name).all()
        if len(groups) == 0:
            logging.info('No group found with name {0}'.format(name))
            return None
        else:
            return groups[0]

    def photo_by_id(self, id):
        photos = db.session.query(Photo).filter_by(id=id).all()
        if len(photos) == 0:
            logging.info('No photo found with id {0}'.format(name))
        elif len(photos) > 1:
            logging.info('Found multiple photos for id {0} (taking first): {1}'.format(name, photos))
        photo = photos[0]
        return photo

    def photo_increase_like(self, photo):
        photo.n_likes += 1
        db.session.commit()

    def new_posts(self):
        six_months_ago = datetime.now() - timedelta(6.* 365./12.)
        return db.session.query(Post).filter(Post.date >= six_months_ago).all()[::-1]

    def new_posts_for_user(self, user):
        return [ p for p in self.new_posts() if p.allow(user) ]

    def new_posts_public(self):
        return [ p for p in self.new_posts() if p.is_public() ]

    def delete_comment(self, i):
        db.session.query(Comment).filter(Comment.id==i).delete()
        db.session.commit()


class Factory(object):
    """docstring for Factory"""
    def __init__(self):
        super(Factory, self).__init__()
        self.dbmanager = DBManager(db)


class UserFactory(Factory):
    """ """
    def __init__(self, album):
        super(UserFactory, self).__init__()

    def create(self, email, password):
        pwhash = generate_password_hash(password)
        user = User(email=email, pwhash=pwhash)


class PhotoFactory(Factory):
    """docstring for PhotoFactory"""
    thumbnail_width = 420
    medium_width = 1620
    debug = False
    # debug = True

    orientation_funcs = [
        lambda im: im, # 0 shouldn't happen but do nothing just in case
        lambda im: im,
        lambda im: im.transpose(Image.FLIP_LEFT_RIGHT),
        lambda im: im.transpose(Image.ROTATE_180),
        lambda im: im.transpose(Image.FLIP_TOP_BOTTOM),
        lambda im: rotate_90(flip_horizontal(im)),
        lambda im: im.transpose(Image.ROTATE_270),
        lambda im: rotate_90(flip_vertical(im)),
        lambda im: im.transpose(Image.ROTATE_90),
        ]

    def __init__(self, album):
        super(PhotoFactory, self).__init__()
        self.album = album

    def create(self, imgpath_full):
        logging.info('Adding photo {0} to album {1}'.format(imgpath_full, self.album.name))

        imgpath_medium = self.make_medium_photo(imgpath_full)
        imgpath_thumbnail = self.make_thumbnail_photo(imgpath_full)
        photo = Photo(
            imgpath_full = imgpath_full,
            imgpath_medium = imgpath_medium,
            imgpath_thumbnail = imgpath_thumbnail,
            album = self.album,
            )

        creation_date = self.get_creation_date(imgpath_full)
        if not(creation_date is None):
            photo.creation_date = creation_date

        if not self.debug:
            logging.info('Adding {0} to the db'.format(photo))
            db.session.add(photo)
            db.session.commit()
        return photo

    def fix_orientation(self, im):
        try:
            for orientation in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation]=='Orientation': break 
            exif=dict(im._getexif().items())
            im = self.orientation_funcs[exif[orientation]](im)
        except:
            logging.info('Failed to retrieve orientation data')
        return im

    def get_filename_for_smaller(self, imgpath_full, tag):
        filename, fileextension = os.path.splitext(os.path.basename(imgpath_full))
        uid = uuid.uuid4().hex
        new_filename = filename + '_' + tag + '_' + uid + fileextension
        return os.path.join(app.config['PHOTOPATH'], new_filename)

    def make_smaller_photo(self, imgpath_full, imgpath_smaller, new_width, apply_to_height=False):
        if self.debug: return
        im = Image.open(imgpath_full)
        im = self.fix_orientation(im)
        if apply_to_height and im.height > im.width:
            new_width = int(new_width * float(im.width) / im.height)

        new_size = (new_width, new_width) # Aspect ratio is by default maintained
        im.thumbnail(new_size, Image.ANTIALIAS) # ANTIALIAS flag highly recommended
        im.save(imgpath_smaller)

    def make_medium_photo(self, imgpath_full):
        logging.info('Creating medium sized image for %r' % imgpath_full)
        imgpath_medium = self.get_filename_for_smaller(imgpath_full, 'medium')
        self.make_smaller_photo(imgpath_full, imgpath_medium, self.medium_width)
        return imgpath_medium

    def make_thumbnail_photo(self, imgpath_full):
        logging.info('Creating thumbnail sized image for %r' % imgpath_full)
        imgpath_thumbnail = self.get_filename_for_smaller(imgpath_full, 'thumbnail')
        self.make_smaller_photo(imgpath_full, imgpath_thumbnail, self.thumbnail_width, apply_to_height=True)
        return imgpath_thumbnail

    def get_creation_date(self, imgpath_full):
        try:
            date_str = Image.open(imgpath_full)._getexif()[36867]
            datetime_object = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
            return datetime_object
        except:
            return None


class AlbumFactory(Factory):
    """docstring for AlbumFactory"""
    dbmanager = DBManager(db)

    def __init__(self):
        super(AlbumFactory, self).__init__()

    def exists(self, name):
        album = self.dbmanager.album_by_name(name)
        if album is None:
            return False
        else:
            return True

    def create(self, name):
        if self.exists(name):
            raise RuntimeError(
                'Album \'{0}\' already exists in the database; not creating.'
                .format(name)
                )
        logging.info('Creating new Album {0}'.format(name))
        album = Album(name=name)
        logging.info(album.repr_elaborate())
        db.session.add(album)
        db.session.commit()
        return album

    def delete(self, name):
        if not self.exists(name):
            logging.info('Album \'{0}\' does not exist, nothing to delete'.format(name))
        if raw_input('Are you sure you want to delete Album {0}? (y/n)'.format(name)).lower() != 'y':
            sys.exit()
        logging.info('Deleting Album {0}'.format(name))
        db.session.query(Album).filter_by(name=name).delete()
        db.session.commit()


class CommentFactory(Factory):
    """docstring for CommentFactory"""
    def __init__(self, photo):
        super(CommentFactory, self).__init__()
        self.photo = photo
        
    def create(self, author, text):
        logging.info('Creating new Comment by {0}'.format(author))
        comment = Comment(author=author, text=text, photo=self.photo)
        logging.info(comment)
        db.session.add(comment)
        db.session.commit()


class PostFactory(Factory):
    """docstring for PostFactory"""
    def __init__(self):
        super(PostFactory, self).__init__()

    def create(self, text, photos=None, groups=None):
        logging.info('Creating new Post')
        logging.info('<text = {0}, photos = {1}>'.format(text.encode('utf-8', 'replace'), photos))
        post = Post(text=text, photos=photos, date=datetime.now())
        if not(groups is None): post.groups.extend(groups)
        logging.info(post)
        db.session.add(post)
        db.session.commit()





