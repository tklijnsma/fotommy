# -*- coding: utf-8 -*-

import logging, uuid, os, functools
from fotommy import db, dbmanager, app, login_manager

from flask import (
    Flask, request, session, g, redirect, url_for, abort,
    render_template, flash,
    send_from_directory
    )

from forms import *
import factories, models

from werkzeug.utils import secure_filename
import werkzeug.security

import flask_login
from flask_login import current_user, logout_user

from customemail import Email

import time
def timestamp():
    return time.strftime('%Y-%m-%d %H:%M:%S')

def escape_html(text):
    return text.replace('"','').replace("'",'').replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')

def notify_new_comment(author, pub_or_priv, comment):
    if pub_or_priv == 'admin': pub_or_priv = 'private'
    subject = 'New {0} comment by {1}'.format(pub_or_priv, author)
    body = [
        'New comment created at {0}'.format(timestamp()),
        'id: {0}'.format(comment.id),
        'author: {0}'.format(comment.author.encode('utf-8', 'replace')),
        'text: {0}'.format(comment.text.encode('utf-8', 'replace')),
        'user: {0}'.format(comment.user),
        'photo: {0}'.format(comment.photo),
        'post: {0}'.format(comment.post),
        'groups: {0}'.format(comment.groups),
        'IP: {0}'.format(request.remote_addr),
        ]
    email = Email(
        subject = subject,
        body    = '<br>\n'.join(body)
        )
    email.send()

def login_required(groups=['loggedin']):
    """Custom login_required wrapper to deal with groups"""
    def wrapper(fn):
        @functools.wraps(fn)
        def decorated_view(*args, **kwargs):
            if 'public' in groups:
                logging.info('Allowing access, public')
            if 'loggedin' in groups and not(current_user.is_authenticated):
                return login_manager.unauthorized()
            user_groups = [g.name for g in current_user.groups]
            if current_user.is_admin():
                logging.info('Allowing access, user is admin')
            else:
                intersection = list(set(user_groups) & set(groups))
                if len(intersection) > 0:
                    logging.info('Allowing access through group(s) {0}'.format(intersection))
                else:
                    logging.info(
                        'Unauthorized; no intersection between user {0} and required {1}'
                        .format(current_user.groups, groups)
                        )
                    return login_manager.unauthorized()                
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper

def current_user_is_admin():
    if hasattr(current_user, 'groups'):
        logging.info('current_user.groups = {0}'.format(current_user.groups))
        if 'admin' in [ g.name for g in current_user.groups ]:
            return True
    return False

@app.route('/robots.txt')
@app.route('/sitemap.xml')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])

@app.route('/android-chrome-192x192.png')
@app.route('/android-chrome-384x384.png')
@app.route('/apple-touch-icon.png')
@app.route('/browserconfig.xml')
@app.route('/favicon-16x16.png')
@app.route('/favicon-32x32.png')
@app.route('/favicon.ico')
@app.route('/mstile-150x150.png')
@app.route('/safari-pinned-tab.svg')
@app.route('/site.webmanifest')
def icon_root_urls():
    return send_from_directory(
        os.path.join(app.static_folder, 'icons'),
        request.path[1:]
        )


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(prefix='register')
    if request.method == 'POST':
        if form.validate_on_submit():
            logging.info('Registration submitted for name {1}, email {0}'.format(form.email.data, form.name.data))
            pwhash = werkzeug.security.generate_password_hash(form.password.data)
            user = models.User(name=form.name.data, email=form.email.data, pwhash=pwhash)
            db.session.add(user)
            db.session.commit()
            flask_login.login_user(user)
            logging.info('Registered {0}'.format(user))
            flash('Account successfully created!')
            body = [
                'New account created at {0}'.format(timestamp()),
                'id: {0}'.format(user.id),
                'name: {0}'.format(user.name.encode('utf-8', 'replace')),
                'email: {0}'.format(user.email),
                'want_newsletter: {0}'.format(user.want_newsletter),
                'comments: {0}'.format(user.comments),
                'groups: {0}'.format(user.groups),
                'IP: {0}'.format(request.remote_addr),
                ]
            email = Email(
                subject = 'New account: {0}'.format(user),
                body    = '<br>\n'.join(body)
                )
            email.send()
            return redirect(url_for('timeline'))
    return render_template('register.html', registerform=form)


@app.route('/account', methods=['GET', 'POST'])
def account():
    if not current_user.is_authenticated:
        return login_manager.unauthorized()
    form = AccountEditForm(prefix='account')
    if request.method == 'POST':
        if form.validate_on_submit():
            logging.info('Account edit submitted for user {0}'.format(current_user))
            pwhash = werkzeug.security.generate_password_hash(form.newpassword.data)
            current_user.pwhash = pwhash
            db.session.commit()
            flash('Password successfully changed!')
            logging.info('Password changed for user {0}'.format(current_user))
            return redirect(url_for('account'))
    return render_template('account.html', pwform=form)


def is_safe_url(url):
    logging.info('Url {0} is safe'.format(url))
    return True

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(prefix='login')
    if form.validate_on_submit():
        logging.info('Login for email {0}'.format(form.email.data))
        user = dbmanager.user_by_email(form.email.data)
        if user is None:
            logging.info('Login failed, no email {0}'.format(form.email.data))
            flash('No user registered for {0}'.format(form.email.data))
        else:
            logging.info('Found user {0}'.format(user))
            if user.check_password(form.password.data):
                flask_login.login_user(user)
                flash('Logged in successfully.')
                next = request.args.get('next')
                # is_safe_url should check if the url is safe for redirects.
                # See http://flask.pocoo.org/snippets/62/ for an example.
                if not is_safe_url(next):
                    return abort(400)
                return redirect(next or url_for('timeline'))
            else:
                flash('Password incorrect')
    return render_template('login.html', loginform=form)

@app.route('/logout')
def logout():
    if current_user.is_authenticated:
        logging.info('Logging out user {0}'.format(current_user))
        logout_user()
        flash('You have successfully logged yourself out.')
        return redirect(url_for('timeline'))
    else:
        flash('You were not logged in!')
        return redirect(url_for('timeline'))


@app.route('/timeline', methods=['GET', 'POST'])
def timeline():
    if current_user.is_authenticated:
        posts = dbmanager.new_posts_for_user(current_user)
    else:
        posts = dbmanager.new_posts_public()
    
    for i, post in enumerate(posts):
        post.commentform = CommentForm(prefix='comment{0}'.format(i))
        post.likeform = IncreaseLikeForm(prefix='like{0}'.format(i))

    if request.method == 'POST':
        for post in posts:
            if current_user.is_authenticated: post.commentform.author.data = current_user.name
            if 'prefix' in request.form and request.form['prefix'] == post.likeform._prefix:
                post.n_likes += 1
                db.session.commit()
                logging.info('Increased like count for {0}'.format(post))
                if 'safari' in request.headers.get('User-Agent').lower():
                    return redirect(url_for('timeline'))
                else:
                    return '', 304
            elif (post.commentform.author.data or post.commentform.text.data) and post.commentform.validate_on_submit():
                logging.info('Comment is submitted for Post {0}'.format(post))
                logging.info('post.commentform.author.data = {0}'.format(post.commentform.author.data.encode('utf-8', 'replace')))
                logging.info('post.commentform.text.data = {0}'.format(post.commentform.text.data.encode('utf-8', 'replace')))
                logging.info('post.commentform.visibility.data = {0}'.format(post.commentform.visibility.data.encode('utf-8', 'replace')))
                comment = models.Comment(
                    author = post.commentform.author.data,
                    text   = post.commentform.text.data,
                    post   = post
                    )
                comment.groups.append(dbmanager.group_by_name(post.commentform.visibility.data))
                if current_user.is_authenticated:
                    comment.user = current_user
                db.session.add(comment)
                db.session.commit()
                notify_new_comment(
                    post.commentform.author.data,
                    post.commentform.visibility.data,
                    comment
                    )
                if not current_user.is_authenticated and post.commentform.visibility.data == 'admin':
                    flash(
                        'Your comment is submitted, '
                        'but you set it to \'private\' and are not logged in, '
                        'so you will not be able to see it'
                        )
                else:
                    flash('Your comment is submitted!')
                return redirect(url_for('timeline'))
    logging.info('is_admin: {0}'.format(current_user_is_admin()))
    return render_template('timeline.html', posts=posts, is_admin=current_user_is_admin())



@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/createpost', methods=['GET', 'POST'])
@login_required(groups=['admin'])
def createpost():
    postform = CreatePostForm(prefix='postform')
    groups = dbmanager.all_groups()

    if request.method == 'POST':

        if postform.submit.data and postform.validate_on_submit():
            logging.info('CreatePostForm is submitted:')
            logging.info('postform.text.data = {0}'.format(postform.text.data.encode('utf-8', 'replace')))

            formvals = request.form.to_dict()
            selected_groups = []
            for group in groups:
                if group.name in formvals.keys() and formvals[group.name] == u'on':
                    selected_groups.append(group)
            logging.info('Selected groups: {0}'.format(selected_groups))

            photos = request.files.getlist('postform-photos')
            photo_instances = []

            if photos:
                uploadalbum = dbmanager.album_by_name('uploads')
                photofactory = factories.PhotoFactory(uploadalbum)

                for fs in photos:
                    logging.info('Processing {0}'.format(fs))
                    image_file = os.path.join(
                        app.config['UPLOADED_PHOTOS_DEST'],
                        str(uuid.uuid4()) + secure_filename(fs.filename)
                        )
                    fs.save(image_file)
                    logging.info('Saved to {0}'.format(image_file))

                    logging.info('Entering {0} into database'.format(image_file))
                    photo_instance = photofactory.create(image_file, groups=selected_groups)
                    photo_instances.append(photo_instance)
            else:
                logging.info('No photos attached')

            factories.PostFactory().create(postform.text.data, photo_instances, groups=selected_groups)
            return redirect(url_for('timeline'))

        else:
            flash('An error occured')
            logging.info('CreatePostForm is submitted:')
            logging.info('postform.text.data = {0}'.format(postform.text.data.encode('utf-8', 'replace')))
            logging.info('postform.photos = {0}'.format(postform.photos))
            print request.files
            for f in request.files:
                print request.files.get(f)

    return render_template('createpost.html', postform=postform, groups=groups)


@app.route('/editcomment/<comment_id>', methods=['GET', 'POST'])
def editcomment(comment_id):
    comment = dbmanager.comment_by_id(comment_id)
    if comment is None: abort(404)
    if not(current_user_is_admin() or comment.user == current_user):
        return login_manager.unauthorized()
    groups = dbmanager.all_groups()

    form = EditCommentForm(prefix='editform')

    if request.method == 'POST':
        if form.submit.data and form.validate_on_submit():
            formvals = request.form.to_dict()
            selected_groups = []
            print formvals.keys()
            for group in groups:
                if group.name in formvals.keys() and formvals[group.name] == u'on':
                    selected_groups.append(group)
            logging.info('Selected groups: {0}'.format(selected_groups))
            comment.groups = [dbmanager.group_by_name(form.visibility.data)]
            comment.text = form.text.data
            db.session.commit()
            flash('Comment {0} edited!'.format(comment_id))
            return redirect(url_for('timeline'))
        else:
            flash('Submission problem')

    form.text.data = comment.text
    return render_template('editcomment.html', comment=comment, form=form)


@app.route('/editpost/<post_id>', methods=['GET', 'POST'])
@login_required(groups=['admin'])
def editpost(post_id):
    post = dbmanager.post_by_id(post_id)
    if post is None: abort(404)
    groups = dbmanager.all_groups()

    form = EditPostForm(prefix='editform')

    if request.method == 'POST':
        if form.submit.data and form.validate_on_submit():
            formvals = request.form.to_dict()
            selected_groups = []
            for group in groups:
                if group.name in formvals.keys() and formvals[group.name] == u'on':
                    selected_groups.append(group)
            logging.info('Selected groups: {0}'.format(selected_groups))
            post.groups = selected_groups
            post.text = form.text.data
            db.session.commit()
            flash('Post {0} edited!'.format(post_id))
            return redirect(url_for('timeline'))

    form.text.data = post.text
    return render_template('editpost.html', post=post, form=form, groups=groups)

@app.route('/')
def index():
    return redirect(url_for('timeline'))

@app.route('/albums')
@login_required(groups=['admin'])
def albums():
    return render_template('albums.html', albums=dbmanager.all_albums())

@app.route('/album/<album_name>')
@login_required(groups=['admin'])
def album(album_name):
    album = dbmanager.album_by_name(album_name)
    if album is None: abort(404)
    return render_template('album.html', album=album)

@app.route('/album/<album_name>/photo/<photo_id>', methods=['GET', 'POST'])
def photo(album_name, photo_id):
    photo = dbmanager.photo_by_id(photo_id)
    if photo is None: abort(404)
    if not photo.allow(current_user):
        return login_manager.unauthorized()

    commentform = CommentForm(prefix='comment')
    likeform = IncreaseLikeForm(prefix='like')

    if request.method == 'POST':
        if current_user.is_authenticated: commentform.author.data = current_user.name
        if 'prefix' in request.form and request.form['prefix'] == likeform._prefix:
            photo.n_likes += 1
            db.session.commit()
            logging.info('Increased like count for {0}'.format(photo))
            if 'safari' in request.headers.get('User-Agent').lower():
                logging.info('Detected user-agent safari ({0}); redirecting to same page'.format(request.headers.get('User-Agent')))
                return redirect(url_for('photo', album_name=album_name, photo_id=photo_id))
            else:
                return '', 304
        elif (commentform.author.data or commentform.text.data) and commentform.validate_on_submit():
            logging.info('Comment is submitted for photo {0}'.format(photo))
            logging.info('commentform.author.data = {0}'.format(commentform.author.data.encode('utf-8', 'replace')))
            logging.info('commentform.text.data = {0}'.format(commentform.text.data.encode('utf-8', 'replace')))
            logging.info('commentform.visibility.data = {0}'.format(commentform.visibility.data.encode('utf-8', 'replace')))
            comment = models.Comment(
                author = commentform.author.data,
                text   = commentform.text.data,
                photo  = photo
                )
            comment.groups.append(dbmanager.group_by_name(commentform.visibility.data))
            if current_user.is_authenticated:
                comment.user = current_user
            db.session.add(comment)
            db.session.commit()
            notify_new_comment(
                commentform.author.data,
                commentform.visibility.data,
                comment
                )
            return redirect(url_for('photo', album_name=album_name, photo_id=photo_id))

    return render_template('photo.html', photo=photo, form=commentform, likeform=likeform)

@app.route('/album/<album_name>/fullres/<photo_id>', methods=['GET', 'POST'])
def fullres(album_name, photo_id):
    photo = dbmanager.photo_by_id(photo_id)
    if photo is None: abort(404)
    if not photo.allow(current_user):
        return login_manager.unauthorized()

    photo_dir, photo_filename = photo.imgpath_full.rsplit('/', 1)

    return send_from_directory(photo_dir, photo_filename)

