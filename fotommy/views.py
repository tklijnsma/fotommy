import logging, uuid, os
from fotommy import db, dbmanager, app

from flask import (
    Flask, request, session, g, redirect, url_for, abort,
    render_template, flash,
    send_from_directory
    )

from forms import CommentForm, IncreaseLikeForm, CreatePostForm
import factories, models

from werkzeug.utils import secure_filename


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

@app.route('/timeline', methods=['GET', 'POST'])
def timeline():
    posts=dbmanager.new_posts()
    for i, post in enumerate(posts):
        post.commentform = CommentForm(prefix='comment{0}'.format(i))
        post.likeform = IncreaseLikeForm(prefix='like{0}'.format(i))

    if request.method == 'POST':
        for post in posts:
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
                logging.info('post.commentform.author.data = {0}'.format(post.commentform.author.data))
                logging.info('post.commentform.text.data = {0}'.format(post.commentform.text.data))
                comment = models.Comment(
                    author = post.commentform.author.data,
                    text   = post.commentform.text.data,
                    post   = post
                    )
                db.session.add(comment)
                db.session.commit()
                return redirect(url_for('timeline'))
    return render_template('timeline.html', posts=posts)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/createpost', methods=['GET', 'POST'])
def createpost():

    postform = CreatePostForm(prefix='postform')

    if request.method == 'POST':

        if postform.submit.data and postform.validate_on_submit():
            logging.info('CreatePostForm is submitted:')
            logging.info('postform.text.data = {0}'.format(postform.text.data))
            logging.info('postform.secretpassword.data = {0}'.format(postform.secretpassword.data))

            if not os.path.exists('fotommy/pw.txt'):
                logging.error('No file pw.txt found')
                flash('Error processing password')
            with open('fotommy/pw.txt', 'r') as fp:
                pw = fp.read().strip()
            if postform.secretpassword.data != pw:
                logging.error('{0} != {1} (actual pw)'.format(postform.secretpassword.data, pw))
                flash('Password is incorrect!')
            else:                
                photos = request.files.getlist('postform-photos')
                photo_instances = []

                if photos:
                    uploadalbum = dbmanager.album_by_name('uploads', fail_if_not_existing=False)
                    if uploadalbum is None:
                        uploadalbum = factories.AlbumFactory().create('uploads')
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
                        photo_instance = photofactory.create(image_file)
                        photo_instances.append(photo_instance)
                else:
                    logging.info('No photos attached')

                factories.PostFactory().create(postform.text.data, photo_instances)
                return redirect(url_for('timeline'))

        else:
            flash('An error occured')

            logging.info('CreatePostForm is submitted:')
            logging.info('postform.text.data = {0}'.format(postform.text.data))
            logging.info('postform.photos = {0}'.format(postform.photos))
            print request.files
            for f in request.files:
                print request.files.get(f)

    return render_template('createpost.html', postform=postform)


@app.route('/')
def index():
    return redirect(url_for('timeline'))

@app.route('/albums')
def albums():
    return render_template('albums.html', albums=dbmanager.all_albums())

@app.route('/album/<album_name>')
def album(album_name):
    album = dbmanager.album_by_name(album_name)
    if album is None: abort(404)
    return render_template('album.html', album=album)

@app.route('/album/<album_name>/photo/<photo_id>', methods=['GET', 'POST'])
def photo(album_name, photo_id):
    photo = dbmanager.photo_by_id(photo_id)
    if photo is None: abort(404)

    commentform = CommentForm(prefix='comment')
    likeform = IncreaseLikeForm(prefix='like')

    if request.method == 'POST':
        if 'prefix' in request.form and request.form['prefix'] == likeform._prefix:
            photo.n_likes += 1
            db.session.commit()
            logging.info('Increased like count for {0}'.format(photo))
            return '', 204
        elif (commentform.author.data or commentform.text.data) and commentform.validate_on_submit():
            logging.info('Comment is submitted for Photo {0}'.format(photo))
            logging.info('commentform.author.data = {0}'.format(commentform.author.data))
            logging.info('commentform.text.data = {0}'.format(commentform.text.data))
            comment = models.Comment(
                author = commentform.author.data,
                text   = commentform.text.data,
                photo  = photo
                )
            db.session.add(comment)
            db.session.commit()
            return redirect(url_for('photo', album_name=album_name, photo_id=photo_id))
        else:
            flash('An error occured')

    return render_template('photo.html', photo=photo, form=commentform, likeform=likeform)

@app.route('/album/<album_name>/fullres/<photo_id>', methods=['GET', 'POST'])
def fullres(album_name, photo_id):
    photo = dbmanager.photo_by_id(photo_id)
    if photo is None: abort(404)

    photo_dir, photo_filename = photo.imgpath_full.rsplit('/', 1)

    return send_from_directory(photo_dir, photo_filename)

