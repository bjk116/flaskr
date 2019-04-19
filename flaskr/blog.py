from flask import (
	Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db
from collections import defaultdict

bp = Blueprint('blog', __name__)

#This should probably end up going in db.py, unless I don't want to always use it
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

@bp.route('/')
def index():
    db = get_db()
    # A design pattern I am borrowing from work and making more streamlined.  Write queries once and fit the parameters to it
    # So if I have a user, then nice, use the userId and get the additional info on if they liked an individual post
    # But if they're not, set our userId to what we know to be a nonsense value such that we can still use the same query
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
    if g.user:
        userId = g.user['id']
    else:
        userId = -1

    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username, IFNULL(SUM(l.postId=p.id),0) as likes, IFNULL(SUM(l.userId=?),0) as personallyLiked'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' LEFT JOIN likedPosts l ON l.postId = p.id'
        ' WHERE p.id = ?'
        ' GROUP BY p.id'
        ' ORDER BY created DESC',
        (userId,id)
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

def get_comments(postId):
    db = get_db()
    db.row_factory = dict_factory
    print('postId: ' + str(postId))
    print('type: ' + str(type(postId)))
    #comments = db.execute('SELECT c1.id, c1.u.username, c1.commentContent, c1.createdAt,c2.id, u.username, c2.commentContent, c2.createdAt '
    #            'FROM commentsOnPost c1 '
    #            'JOIN commentsOnPost c2 ON c1.id = c2.commentParentId '
    #            'JOIN user u ON c1.author_id = u.id '
    #            'JOIN user u ON c2.author_id = u.id '
    #            'WHERE c.postId = ?', (postId,)).fetchall()
    comments = db.execute('WITH CommentsCTE as '
                        '(SELECT c.id, c.commentParentId, username, c.commentContent, c.createdAt '
                        'FROM commentsOnPost c '
                        'JOIN user u ON c.author_id = u.id '
                        'WHERE c.commentParentId = -1 and c.postId = ?'
                        'UNION ALL '
                        'SELECT c.id, c.commentParentId, username, c.commentContent, c.createdAt '
                        'FROM commentsOnPost c '
                        'INNER JOIN CommentsCTE ce '
                        'ON ce.id = c.commentParentId '
                        ') '
                        'SELECT * From CommentsCTE',(postId,)).fetchall()

    for comment in comments:
        print("comment:" + str(comment))

    print("GETTING COMMENTS")

    comments_by_parent = defaultdict(list)
    
    for comment in comments:
        if comment['commentParentId']==-1:
            id = None
        else:
            id = comment['commentParentId']
        comments_by_parent[id].append(comment)


    for comment in comments:
        comment['children_comments'] = comments_by_parent[comment['id']]

    root_comments = comments_by_parent[None]

    print("root comments:")
    print(str(root_comments))

    return root_comments


@bp.route('/<int:id>/view', methods=('GET',))
def view(id):
    post = get_post(id, check_author=False)

    comments = get_comments(post['id'])
    print("%i comments should appear"%(len(comments)))

    if post:
        return render_template('blog/view.html', post=post, comments=comments)
    else:
        return redirect(url_for('blog.index'))

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
def like(id, rerdirectHere=False):
    """
    Arguments:
        id: id of the post to be liked
        redirectHere: if true, redirect to blog.view with current id, else redirect to blog.index
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
    
    redirectToView = request.args.get('redirectHere')
    print("redirectToView: " + str(redirectToView))
    if redirectToView:
        return redirect(url_for('blog.view', id=id))
    else:
        return redirect(url_for('blog.index'))

@bp.route('/<int:postId>/comment/add/', methods=('POST',))
@login_required
def addComment(postId, redirectHere=False, parentComment=-1):
    userId = g.user['id']
    db = get_db()
    created = db.execute("SELECT strftime('%Y-%m-%d %H:%M:%S', datetime('now'))").fetchone()[0]
    comment =  request.form['comment']
    if request.args.get('parentComment'):
        parentComment = request.args.get('parentComment')
    queryValues = (postId, userId, parentComment, comment, created)
    print("adding comment")
    print('PARENT COMMENT: ' +str(queryValues[2]))
    for value in queryValues:
        print("value: "+str(value))
        print("type: "+str(type(value)))
    db.execute('INSERT INTO commentsOnPost(postId, author_id,commentParentId, commentContent, createdAt) '
        'VALUES (?, ?, ?, ?, ?)', (postId, userId, parentComment, comment, created))
    db.commit()
    return redirect(url_for('blog.view', id=postId))