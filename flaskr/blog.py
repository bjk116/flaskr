from flask import (
	Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('blog', __name__)

@bp.route('/')
def index():
    db = get_db()

    if g.user:
        userId = g.user['id']
    else:
        userId = -1
    print("user: "+str(userId))

    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username, IFNULL(SUM(l.postId=p.id),0) as likes, IFNULL(SUM(l.userId=?),0) as personallyLiked'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' LEFT JOIN likedPosts l ON l.postId = p.id'
        ' GROUP BY p.id'
        ' ORDER BY created DESC',
        (userId,)
    ).fetchall()
    print("posts: " + str(posts))
    countOfPosts = db.execute('SELECT COUNT(*) FROM post').fetchone()[0]
    print("post count: " + str(countOfPosts))
    if posts:
        print("posts"+str(posts[0]))
        for stuff in posts[0]:
            print(str(stuff))
    return render_template('blog/index.html', posts=posts)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, author_id)'
                ' VALUES (?, ?, ?)',
                (title, body, g.user['id'])
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')

def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
    	abort(404, "Post id {0} doesn't exist.".format(id))

    if check_author and post['author_id'] != g.user['id']:
    	abort(403)

    return post

@bp.route('/<int:id>/update', methods=('GET','POST'))
@login_required
def update(id):
	post = get_post(id)

	if request.method == 'POST':
		title = request.form['title']
		body = request.form['body']
		error = None

		if not title:
			error = 'Title is required.'
		
		if error is not None:
			flash(error)
		else:
			db = get_db()
			db.execute(
				'UPDATE post SET title = ?, body = ?'
				' WHERE id = ?',
				(title, body, id)
			)
			db.commit()
			return redirect(url_for('blog.index'))

	return render_template('blog/update.html', post=post)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
	get_post(id)
	db = get_db()
	db.execute('DELETE FROM post WHERE id = ?', (id,))
	db.commit()
	return redirect(url_for('blog.index'))

@bp.route('/<int:id>/like', methods=('POST',))
@login_required
def like(id):
    """
    Arguments:
        id: id of the post to be liked
    Returns:
        Nothing as of now, will figure this out later
    """
    db = get_db()
    if g.user:
        userId = g.user['id']
    else:
        userId = -1

    userAlreadyLikedPost = db.execute('SELECT COUNT(*) FROM likedPosts WHERE postId = ? AND userId = ?', (id, userId)).fetchone()[0] > 0
    
    if userAlreadyLikedPost:
        #Then delete the record, the user unlikes the post
        db.execute(
            'DELETE FROM likedPosts'
            ' WHERE postId = ? AND userId = ?',
            (id, userId)
        )
        db.commit()
        print("Unliked post")
    else:
        # Like this post
        db.execute(
            'INSERT INTO likedPosts (postId, userId)'
            ' VALUES (?, ?)',
            (id, g.user['id'])
        )
        db.commit()
        print("Liked post")
    
    return redirect(url_for('blog.index'))